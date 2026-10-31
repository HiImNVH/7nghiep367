"""Bridge the shared AI package to the existing prediction contract."""

from visign_api.config import settings
from visign_api.domain.errors import (
    ClipDecodeFailedException,
    ClipTooLongException,
    ClipTooShortException,
    InsufficientLandmarksException,
    NoPersonDetectedException,
)
from visign_api.domain.prediction import PredictionQualityHints, PredictionTimings


class GRUApiPredictor:
    def __init__(self, artifact_dir, metadata):
        # Lazy import keeps the fixture service usable without the AI extra installed.
        from visign_ai.inference import GRUPredictor
        from visign_ai.landmarks.holistic_extractor import extractor_identity
        from visign_ai.landmarks.sequence_transform import load_schema

        self._predictor = GRUPredictor(artifact_dir)
        schema = load_schema(self._predictor.schema_path)
        identity = extractor_identity(schema, self._predictor.model_dir)
        if identity["version"] != metadata.extractorVersion:
            raise ValueError("Serving extractor differs from model extractor")
        if schema.get("status") != "APPROVED":
            raise ValueError("An approved schema is required for pilot/full serving")
        # Evaluation alone cannot authorize a demo release.
        metadata.demoReady = (
            metadata.demoReady and self._predictor.metadata.get("demoReady") is True
        )
        self._metadata = metadata

    @property
    def metadata(self):
        return self._metadata

    def predict(self, clip_path, request_id):
        from visign_ai.landmarks.errors import PipelineError

        from visign_api.inference.predictor import RawPredictionResult

        try:
            result = self._predictor.predict(
                clip_path,
                min_duration_ms=settings.min_duration_ms,
                max_duration_ms=settings.max_duration_ms,
            )
        except PipelineError as error:
            errors = {
                "CLIP_TOO_SHORT": ClipTooShortException,
                "CLIP_TOO_LONG": ClipTooLongException,
                "NO_PERSON_DETECTED": NoPersonDetectedException,
                "INSUFFICIENT_LANDMARKS": InsufficientLandmarksException,
            }
            raise errors.get(error.code, ClipDecodeFailedException)() from error
        return RawPredictionResult(
            classLabel=result["classLabel"],
            confidence=result["confidence"],
            text=result["text"],
            timingsMs=PredictionTimings(**result["timingsMs"]),
            qualityHints=PredictionQualityHints(**result["qualityHints"]),
        )


def build_gru_predictor(artifact_dir, metadata, display_text_map, extras):
    return GRUApiPredictor(artifact_dir, metadata)
