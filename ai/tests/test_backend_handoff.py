import json

import pytest
import torch
from visign_ai.inference import GRUPredictor
from visign_ai.io import write_json
from visign_api.config import settings
from visign_api.inference.check_artifact import check_artifact


def bind_labels(artifact):
    info = json.loads((artifact / "model_info.json").read_text("utf-8"))
    path = artifact / "model.pt"
    checkpoint = torch.load(path, weights_only=True)
    checkpoint["labelBinding"] = {
        key: info[key] for key in ("classLabels", "meaningMap", "displayTextMap")
    }
    torch.save(checkpoint, path)
    return info


@pytest.mark.parametrize("mutation", ["order", "meaning", "text"])
def test_checkpoint_rejects_changed_label_contract(synthetic_pilot_artifact, mutation):
    info = bind_labels(synthetic_pilot_artifact)
    if mutation == "order":
        info["classLabels"].reverse()
    elif mutation == "meaning":
        info["meaningMap"] = {"A_HCM": "B", "B_HCM": "A"}
    else:
        info["displayTextMap"]["A"] = "Changed text"
    write_json(synthetic_pilot_artifact / "model_info.json", info)
    with pytest.raises(ValueError, match="label binding mismatch"):
        GRUPredictor(synthetic_pilot_artifact)


def test_handoff_load_and_reject_candidate_without_rollback(synthetic_pilot_artifact, monkeypatch):
    info = bind_labels(synthetic_pilot_artifact)
    monkeypatch.setattr(settings, "feature_schema_version", info["featureSchemaVersion"])
    monkeypatch.setattr(
        "visign_ai.landmarks.holistic_extractor.extractor_identity",
        lambda *args: {"version": info["extractorVersion"]},
    )
    report = check_artifact(synthetic_pilot_artifact)
    assert report["labelBindingVerified"] is True
    assert report["demoReady"] is False
    assert report["parity"]["status"] == "NOT_RUN"
    monkeypatch.setattr(settings, "feature_schema_version", "wrong-version")
    with pytest.raises(Exception, match="serving schema"):
        check_artifact(synthetic_pilot_artifact)


def test_new_handoff_requires_bound_labels(synthetic_pilot_artifact, monkeypatch):
    info = json.loads((synthetic_pilot_artifact / "model_info.json").read_text("utf-8"))
    monkeypatch.setattr(settings, "feature_schema_version", info["featureSchemaVersion"])
    monkeypatch.setattr(
        "visign_ai.landmarks.holistic_extractor.extractor_identity",
        lambda *args: {"version": info["extractorVersion"]},
    )
    with pytest.raises(ValueError, match="Unbound legacy labels"):
        check_artifact(synthetic_pilot_artifact)


@pytest.mark.parametrize("code, expected", [
    ("INVALID_REQUEST", "INVALID_REQUEST"),
    ("INSUFFICIENT_LANDMARKS", "INSUFFICIENT_LANDMARKS"),
    ("FEATURE_SCHEMA_MISMATCH", "CLIP_DECODE_FAILED"),
])
def test_adapter_pipeline_error_contract(synthetic_pilot_artifact, monkeypatch, code, expected):
    from visign_ai.landmarks.errors import PipelineError
    from visign_api.domain.errors import ViSignApiException
    from visign_api.inference.predictor import PredictorRegistry

    info = bind_labels(synthetic_pilot_artifact)
    monkeypatch.setattr(settings, "feature_schema_version", info["featureSchemaVersion"])
    monkeypatch.setattr(
        "visign_ai.landmarks.holistic_extractor.extractor_identity",
        lambda *args: {"version": info["extractorVersion"]},
    )
    adapter = PredictorRegistry().load_artifact(str(synthetic_pilot_artifact))
    def fail(*args, **kwargs):
        raise PipelineError(code, "Test only")
    monkeypatch.setattr(adapter._predictor, "predict", fail)
    with pytest.raises(ViSignApiException) as error:
        adapter.predict(synthetic_pilot_artifact / "test.webm", "request")
    assert error.value.code.value == expected
