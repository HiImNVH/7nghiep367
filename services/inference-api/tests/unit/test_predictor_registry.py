"""Unit tests for artifact loading, consistency checks, fail-closed loading and rollback (T037)."""

import json
from pathlib import Path

import pytest

from visign_api.domain.errors import ModelNotReadyException
from visign_api.domain.model_version import ArtifactKind
from visign_api.inference.predictor import (
    PREDICTOR_FACTORIES,
    FixturePredictor,
    PredictorRegistry,
)

ARTIFACTS_DIR = Path(__file__).parents[1] / "fixtures" / "model-artifacts"
FIXTURE_PATH = ARTIFACTS_DIR / "fixture"
LOW_CONFIDENCE_FIXTURE_PATH = ARTIFACTS_DIR / "fixture-low-confidence"

P0_MEANINGS = [
    "GIAY_TO", "DAU_BUNG", "THUOC", "SOT", "NHAN",
    "BAN", "XIN_CHAO", "CAM_ON", "CHO", "SAO_CHEP",
]


def _fixture_info() -> dict:
    return json.loads((FIXTURE_PATH / "model_info.json").read_text(encoding="utf-8"))


def _write_artifact(directory: Path, info: dict) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "model_info.json").write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
    return directory


def _as_kind(info: dict, kind: str, meanings: list) -> dict:
    info.update(
        artifactKind=kind,
        meanings=meanings,
        classLabels=[f"{m}_HCM_1" for m in meanings],
        meaningMap={f"{m}_HCM_1": m for m in meanings},
        displayTextMap={m: m.replace("_", " ").title() for m in meanings},
    )
    return info


def _fixture_factory(artifact_dir, metadata, display_text_map, extras):
    return FixturePredictor(metadata, display_text_map)


def test_loads_fixture_artifact():
    registry = PredictorRegistry()
    predictor = registry.load_artifact(str(FIXTURE_PATH))

    assert isinstance(predictor, FixturePredictor)
    assert registry.is_ready
    assert predictor.metadata.artifactKind == ArtifactKind.FIXTURE


def test_fixture_demo_ready_flag_is_always_overridden(tmp_path):
    info = _fixture_info()
    info["demoReady"] = True
    registry = PredictorRegistry()

    predictor = registry.load_artifact(str(_write_artifact(tmp_path / "a", info)))

    assert predictor.metadata.demoReady is False


def test_first_load_failure_raises_model_not_ready(tmp_path):
    registry = PredictorRegistry()

    with pytest.raises(ModelNotReadyException):
        registry.load_artifact(str(tmp_path / "missing"))
    assert registry.is_ready is False


def _unsupported_feature_schema(info):
    info["featureSchemaVersion"] = "vsl-feature-v9.9"


def _duplicate_class_label(info):
    info["classLabels"] = ["XIN_CHAO_HCM_1", "XIN_CHAO_HCM_1", "TAM_BIET_HCM_1"]


def _class_label_missing_from_meaning_map(info):
    del info["meaningMap"]["CAM_ON_HCM_1"]


def _meaning_map_to_unknown_meaning(info):
    info["meaningMap"]["CAM_ON_HCM_1"] = "KHONG_TON_TAI"


def _meaning_without_display_text(info):
    del info["displayTextMap"]["CAM_ON"]


def _empty_class_labels(info):
    info["classLabels"] = []
    info["meaningMap"] = {}


def _fixture_response_unknown_class(info):
    info["fixtureResponse"] = {"classLabel": "KHONG_TON_TAI_HCM_1", "confidence": 0.9}


def _invalid_json_metadata(info):
    info["acceptanceThreshold"] = 1.5


@pytest.mark.parametrize(
    "mutate",
    [
        _unsupported_feature_schema,
        _duplicate_class_label,
        _class_label_missing_from_meaning_map,
        _meaning_map_to_unknown_meaning,
        _meaning_without_display_text,
        _empty_class_labels,
        _fixture_response_unknown_class,
        _invalid_json_metadata,
    ],
)
def test_inconsistent_artifact_fails_closed(tmp_path, mutate):
    info = _fixture_info()
    mutate(info)
    registry = PredictorRegistry()

    with pytest.raises(ModelNotReadyException):
        registry.load_artifact(str(_write_artifact(tmp_path / "broken", info)))
    assert registry.is_ready is False


def test_failed_load_rolls_back_to_previous_predictor(tmp_path):
    registry = PredictorRegistry()
    original = registry.load_artifact(str(FIXTURE_PATH))
    info = _fixture_info()
    _unsupported_feature_schema(info)

    result = registry.load_artifact(str(_write_artifact(tmp_path / "broken", info)))

    assert result is original
    assert registry.active_predictor is original


@pytest.mark.parametrize("kind,meanings", [("pilot", P0_MEANINGS[:3]), ("full", P0_MEANINGS)])
def test_pilot_and_full_without_real_predictor_fail_closed(tmp_path, kind, meanings):
    """Pilot/full must never silently fall back to the deterministic fixture predictor."""
    info = _as_kind(_fixture_info(), kind, meanings)
    registry = PredictorRegistry()

    with pytest.raises(ModelNotReadyException):
        registry.load_artifact(str(_write_artifact(tmp_path / kind, info)))


def test_pilot_loads_through_registered_predictor_factory(tmp_path, monkeypatch):
    monkeypatch.setitem(PREDICTOR_FACTORIES, ArtifactKind.PILOT, _fixture_factory)
    info = _as_kind(_fixture_info(), "pilot", P0_MEANINGS[:3])
    registry = PredictorRegistry()

    predictor = registry.load_artifact(str(_write_artifact(tmp_path / "pilot", info)))

    assert predictor.metadata.artifactKind == ArtifactKind.PILOT
    assert predictor.metadata.demoReady is False


def test_pilot_with_more_than_three_meanings_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setitem(PREDICTOR_FACTORIES, ArtifactKind.PILOT, _fixture_factory)
    info = _as_kind(_fixture_info(), "pilot", P0_MEANINGS[:4])
    registry = PredictorRegistry()

    with pytest.raises(ModelNotReadyException):
        registry.load_artifact(str(_write_artifact(tmp_path / "pilot", info)))


def test_full_without_exactly_ten_meanings_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setitem(PREDICTOR_FACTORIES, ArtifactKind.FULL, _fixture_factory)
    info = _as_kind(_fixture_info(), "full", P0_MEANINGS[:9])
    registry = PredictorRegistry()

    with pytest.raises(ModelNotReadyException):
        registry.load_artifact(str(_write_artifact(tmp_path / "full", info)))


def test_fixture_response_controls_deterministic_output(tmp_path):
    registry = PredictorRegistry()
    predictor = registry.load_artifact(str(LOW_CONFIDENCE_FIXTURE_PATH))

    result = predictor.predict(tmp_path / "unused.webm", "00000000-0000-0000-0000-000000000000")

    assert result.classLabel == "CAM_ON_HCM_1"
    assert result.text == "Cảm ơn"
    assert result.confidence == pytest.approx(0.42)
