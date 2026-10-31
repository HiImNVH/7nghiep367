"""Predictor interface and artifact loader with rollback capability (T037)."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from visign_api.config import settings
from visign_api.domain.errors import ModelNotReadyException
from visign_api.domain.model_version import ArtifactKind, ModelMetadata
from visign_api.domain.prediction import PredictionQualityHints, PredictionTimings
from visign_api.observability import logger

PILOT_MAX_MEANINGS = 3
FULL_MEANING_COUNT = 10


@dataclass
class RawPredictionResult:
    """Raw prediction result from predictor before final acceptance decision."""

    classLabel: Optional[str]
    confidence: float
    text: str
    timingsMs: Optional[PredictionTimings]
    qualityHints: Optional[PredictionQualityHints]


class BasePredictor(ABC):
    """Abstract predictor interface for fixture, pilot, and full models."""

    @abstractmethod
    def predict(self, clip_path: Path, request_id: str) -> RawPredictionResult:
        """Execute inference on the temporary clip path."""
        pass

    @property
    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """Active model metadata."""
        pass


class FixturePredictor(BasePredictor):
    """
    Deterministic test double predictor for local integration and E2E testing.
    The optional `fixtureResponse` in model_info.json selects the returned class and confidence,
    e.g. a low-confidence fixture for rejected-path E2E tests.
    """

    def __init__(
        self,
        metadata: ModelMetadata,
        display_text_map: Dict[str, str],
        fixture_response: Optional[Dict[str, Any]] = None,
    ):
        self._metadata = metadata
        self._display_text_map = display_text_map
        response = fixture_response or {}
        self._class_label: str = response.get("classLabel") or metadata.classLabels[0]
        self._confidence = float(response.get("confidence", 0.95))

    @property
    def metadata(self) -> ModelMetadata:
        return self._metadata

    def predict(self, clip_path: Path, request_id: str) -> RawPredictionResult:
        meaning_id = self._metadata.meaningMap[self._class_label]

        # Fake timings for diagnostic contract
        timings = PredictionTimings(
            decode=12,
            extract=35,
            infer=8,
        )
        quality_hints = PredictionQualityHints(
            handsDetectedRatio=0.92,
            frameCount=30,
        )

        return RawPredictionResult(
            classLabel=self._class_label,
            confidence=self._confidence,
            text=self._display_text_map[meaning_id],
            timingsMs=timings,
            qualityHints=quality_hints,
        )


PredictorFactory = Callable[[Path, ModelMetadata, Dict[str, str], Dict[str, Any]], BasePredictor]


def _build_fixture_predictor(
    artifact_dir: Path,
    metadata: ModelMetadata,
    display_text_map: Dict[str, str],
    extras: Dict[str, Any],
) -> BasePredictor:
    return FixturePredictor(metadata, display_text_map, extras.get("fixtureResponse"))


# Pilot/full use the optional shared AI package. Missing assets or weights fail closed.
from visign_api.inference.gru_predictor import build_gru_predictor
PREDICTOR_FACTORIES: Dict[ArtifactKind, PredictorFactory] = {
    ArtifactKind.FIXTURE: _build_fixture_predictor,
    ArtifactKind.PILOT: build_gru_predictor,
    ArtifactKind.FULL: build_gru_predictor,
}


def validate_artifact_consistency(
    metadata: ModelMetadata,
    display_text_map: Dict[str, str],
    extras: Dict[str, Any],
) -> None:
    """Reject artifacts whose schema, class map or display texts cannot be served safely."""
    if metadata.featureSchemaVersion != settings.feature_schema_version:
        raise ValueError(
            f"featureSchemaVersion '{metadata.featureSchemaVersion}' does not match "
            f"serving schema '{settings.feature_schema_version}'"
        )

    if len(set(metadata.meanings)) != len(metadata.meanings):
        raise ValueError("meanings must be distinct")
    if not metadata.classLabels:
        raise ValueError("classLabels must not be empty")
    if len(set(metadata.classLabels)) != len(metadata.classLabels):
        raise ValueError("classLabels must be distinct")
    if set(metadata.meaningMap) != set(metadata.classLabels):
        raise ValueError("meaningMap keys must match classLabels exactly")
    if set(metadata.meaningMap.values()) != set(metadata.meanings):
        raise ValueError("meaningMap values must cover exactly the declared meanings")

    missing_texts = [m for m in metadata.meanings if not display_text_map.get(m, "").strip()]
    if missing_texts:
        raise ValueError(f"displayTextMap missing Vietnamese text for {missing_texts}")

    if metadata.artifactKind == ArtifactKind.PILOT and len(metadata.meanings) > PILOT_MAX_MEANINGS:
        raise ValueError(f"pilot artifact supports at most {PILOT_MAX_MEANINGS} meanings")
    if metadata.artifactKind == ArtifactKind.FULL and len(metadata.meanings) != FULL_MEANING_COUNT:
        raise ValueError(f"full artifact must support exactly {FULL_MEANING_COUNT} meanings")

    fixture_response = extras.get("fixtureResponse")
    if fixture_response is not None:
        if metadata.artifactKind != ArtifactKind.FIXTURE:
            raise ValueError("fixtureResponse is only allowed on fixture artifacts")
        label = fixture_response.get("classLabel")
        if label is not None and label not in metadata.classLabels:
            raise ValueError(f"fixtureResponse classLabel '{label}' is not a declared classLabel")
        confidence = fixture_response.get("confidence", 0.95)
        if not 0.0 <= float(confidence) <= 1.0:
            raise ValueError("fixtureResponse confidence must be within [0, 1]")


class PredictorRegistry:
    """Manages active predictor and safe rollback if a new artifact fails to load."""

    def __init__(self):
        self._active_predictor: Optional[BasePredictor] = None
        self._active_artifact_path: Optional[str] = None
        self._last_working_artifact_path: Optional[str] = None

    @property
    def active_predictor(self) -> BasePredictor:
        if self._active_predictor is None:
            raise ModelNotReadyException(message="Không có model artifact nào được nạp.")
        return self._active_predictor

    @property
    def is_ready(self) -> bool:
        return self._active_predictor is not None

    def load_artifact(self, artifact_path_str: str) -> BasePredictor:
        """
        Load an artifact from directory path.
        If loading fails, fail-closed and keep the last working artifact when one is active.
        """
        path = Path(artifact_path_str)
        if not path.is_absolute():
            # Resolve relative to current working directory
            path = Path.cwd() / path

        try:
            info_file = path / "model_info.json"
            if not info_file.exists():
                raise FileNotFoundError(f"model_info.json not found at {path}")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            display_text_map = data.pop("displayTextMap", {})
            extras = {"fixtureResponse": data.pop("fixtureResponse", None)}
            metadata = ModelMetadata(**data)
            validate_artifact_consistency(metadata, display_text_map, extras)

            factory = PREDICTOR_FACTORIES.get(metadata.artifactKind)
            if factory is None:
                raise ValueError(
                    f"no predictor registered for artifactKind '{metadata.artifactKind.value}'"
                )
            predictor = factory(path, metadata, display_text_map, extras)

        except Exception as e:
            logger.error(f"Failed to load artifact from {path}: {e}")
            if self._active_predictor is not None:
                logger.warning(f"Keeping last working artifact {self._active_artifact_path}")
                return self._active_predictor
            raise ModelNotReadyException(message=f"Không thể khởi tạo mô hình: {e}") from e

        self._last_working_artifact_path = self._active_artifact_path or str(path)
        self._active_artifact_path = str(path)
        self._active_predictor = predictor
        logger.info(
            f"Successfully loaded model artifact: {metadata.modelVersion} "
            f"(kind={metadata.artifactKind.value}, demoReady={metadata.demoReady})"
        )
        return predictor


predictor_registry = PredictorRegistry()
