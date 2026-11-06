"""Read-only pilot/full handoff check (T037): load gate, label binding and offline/serving parity.

These tests never import the real visign_ai package: the pilot predictor is a test double and
process_video comes from a stub module installed in sys.modules.
"""

import json
import sys
import types
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")  # check_artifact runs in the AI environment, where numpy exists

from visign_api.domain.errors import ModelNotReadyException
from visign_api.domain.model_version import ArtifactKind
from visign_api.domain.prediction import PredictionQualityHints, PredictionTimings
from visign_api.inference import check_artifact as check_artifact_module
from visign_api.inference.check_artifact import check_artifact
from visign_api.inference.predictor import (
    PREDICTOR_FACTORIES,
    RawPredictionResult,
    predictor_registry,
)

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "model-artifacts" / "fixture"
VALID_WEBM_BYTES = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01mock_valid_payload"


def _features(offset: float = 0.0) -> dict:
    tensor = np.zeros((32, 234), dtype=np.float32)
    tensor[0, 0] = offset
    return {
        "tensor": tensor,
        "point_valid": np.ones((32, 78), dtype=bool),
        "masks": np.ones((32, 3), dtype=bool),
        "tensor_mask": np.ones(32, dtype=bool),
    }


class _SharedPredictorDouble:
    """Stands in for visign_ai.inference.GRUPredictor as seen through the API adapter."""

    def __init__(self, label_binding_verified=True, serving_features=None):
        self.label_binding_verified = label_binding_verified
        self.schema_path = "feature_schema.json"
        self.model_dir = "models"
        self._serving_features = serving_features or _features()

    def clip_to_tensor(self, clip, **kwargs):
        return self._serving_features


class _AdapterDouble:
    def __init__(self, metadata, shared):
        self.metadata = metadata
        self._predictor = shared

    def predict(self, clip_path, request_id):
        return RawPredictionResult(
            classLabel="CAM_ON_HCM_1",
            confidence=0.81,
            text="Cảm ơn",
            timingsMs=PredictionTimings(decode=10, extract=900, infer=5),
            qualityHints=PredictionQualityHints(handsDetectedRatio=0.75, frameCount=64),
        )


def _pilot_artifact(directory: Path) -> Path:
    info = json.loads((FIXTURE_PATH / "model_info.json").read_text(encoding="utf-8"))
    meanings = ["XIN_CHAO", "CAM_ON"]
    info.update(
        modelVersion="vsl-pilot-handoff-test",
        artifactKind="pilot",
        meanings=meanings,
        classLabels=[f"{m}_HCM_1" for m in meanings],
        meaningMap={f"{m}_HCM_1": m for m in meanings},
        displayTextMap={"XIN_CHAO": "Xin chào", "CAM_ON": "Cảm ơn"},
    )
    info.pop("fixtureResponse", None)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "model_info.json").write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
    return directory


@pytest.fixture
def pilot_with(monkeypatch, tmp_path):
    """Register a pilot predictor double built around the given shared predictor."""

    def install(shared):
        monkeypatch.setitem(
            PREDICTOR_FACTORIES,
            ArtifactKind.PILOT,
            lambda artifact_dir, metadata, display_text_map, extras: _AdapterDouble(metadata, shared),
        )
        return _pilot_artifact(tmp_path / "pilot")

    return install


@pytest.fixture
def offline_features(monkeypatch):
    """Stub visign_ai.landmarks.pipeline.process_video; tests set the features it returns."""
    state = {"features": _features()}
    pipeline_module = types.ModuleType("visign_ai.landmarks.pipeline")
    pipeline_module.process_video = lambda clip, **kwargs: state["features"]
    monkeypatch.setitem(sys.modules, "visign_ai", types.ModuleType("visign_ai"))
    monkeypatch.setitem(sys.modules, "visign_ai.landmarks", types.ModuleType("visign_ai.landmarks"))
    monkeypatch.setitem(sys.modules, "visign_ai.landmarks.pipeline", pipeline_module)
    return state


def _clip(tmp_path: Path) -> Path:
    clip = tmp_path / "golden.webm"
    clip.write_bytes(VALID_WEBM_BYTES)
    return clip


def test_fixture_artifact_is_refused_for_handoff():
    with pytest.raises(ValueError, match="not a fixture"):
        check_artifact(FIXTURE_PATH)


def test_rejected_candidate_fails_without_touching_the_serving_registry(tmp_path):
    active_before = predictor_registry.active_predictor

    with pytest.raises(ModelNotReadyException):
        check_artifact(tmp_path / "missing-artifact")

    assert predictor_registry.active_predictor is active_before


def test_unbound_legacy_labels_are_refused(pilot_with):
    artifact = pilot_with(_SharedPredictorDouble(label_binding_verified=False))

    with pytest.raises(ValueError, match="Unbound legacy labels"):
        check_artifact(artifact)


def test_load_only_report_marks_parity_not_run(pilot_with):
    artifact = pilot_with(_SharedPredictorDouble())

    report = check_artifact(artifact)

    assert report["artifactLoadPassed"] is True
    assert report["modelVersion"] == "vsl-pilot-handoff-test"
    assert report["labelBindingVerified"] is True
    assert report["demoReady"] is False
    assert report["parity"] == {"status": "NOT_RUN"}
    assert "prediction" not in report


def test_matching_offline_and_serving_tensors_pass_parity(pilot_with, offline_features, tmp_path):
    artifact = pilot_with(_SharedPredictorDouble())

    report = check_artifact(artifact, _clip(tmp_path))

    assert report["parity"]["status"] == "PASSED"
    assert report["parity"]["shape"] == [32, 234]
    assert report["parity"]["maxAbsDiff"] == 0.0
    assert report["prediction"]["classLabel"] == "CAM_ON_HCM_1"
    assert report["prediction"]["qualityHints"]["frameCount"] == 64


def test_tensor_drift_between_offline_and_serving_fails_parity(pilot_with, offline_features, tmp_path):
    artifact = pilot_with(_SharedPredictorDouble())
    offline_features["features"] = _features(offset=1e-3)

    with pytest.raises(AssertionError):
        check_artifact(artifact, _clip(tmp_path))


def test_mask_mismatch_fails_parity(pilot_with, offline_features, tmp_path):
    artifact = pilot_with(_SharedPredictorDouble())
    drifted = _features()
    drifted["point_valid"][0, 0] = False
    offline_features["features"] = drifted

    with pytest.raises(AssertionError):
        check_artifact(artifact, _clip(tmp_path))


def test_non_webm_clip_is_rejected_before_parity(pilot_with, offline_features, tmp_path):
    artifact = pilot_with(_SharedPredictorDouble())
    clip = tmp_path / "not-a-clip.webm"
    clip.write_bytes(b"not a webm file")

    with pytest.raises(Exception) as exc_info:
        check_artifact(artifact, clip)

    assert not isinstance(exc_info.value, AssertionError)


def test_cli_reports_failure_as_json_and_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["check_artifact", "--artifact", str(FIXTURE_PATH)])

    with pytest.raises(SystemExit) as exc_info:
        check_artifact_module.main()

    assert exc_info.value.code == 1
    output = json.loads(capsys.readouterr().out)
    assert output["artifactLoadPassed"] is False
