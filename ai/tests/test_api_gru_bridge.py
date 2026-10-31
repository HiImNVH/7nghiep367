"""Exercise the real adapter with synthetic tensors, without making quality claims."""

import numpy as np
import pytest
import torch
from visign_ai.io import write_json
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest
from visign_ai.training.gru_classifier import GRUClassifier
from visign_api.domain.errors import ClipTooShortException
from visign_api.inference.predictor import PredictorRegistry


def test_adapter_uses_gru_scores_and_maps_pipeline_errors(tmp_path, monkeypatch):
    schema = load_schema()
    schema["status"] = "APPROVED"  # synthetic test artifact only
    write_json(tmp_path / "feature_schema.json", schema)
    config = {"input_size": 234, "hidden_size": 4, "num_classes": 2, "num_layers": 1}
    model = GRUClassifier(**config)
    with torch.no_grad():
        model.classifier.weight.zero_()
        model.classifier.bias.copy_(torch.tensor([0.0, 2.0]))
    torch.save(
        {
            "modelConfig": config,
            "stateDict": model.state_dict(),
            "schemaSha256": schema_digest(schema),
        },
        tmp_path / "model.pt",
    )
    metadata = {
        "artifactKind": "pilot",
        "modelVersion": "synthetic-test-only",
        "datasetVersion": "synthetic-test-only",
        "featureSchemaVersion": schema["featureSchemaVersion"],
        "extractorVersion": schema["extractorVersion"],
        "meanings": ["A", "B"],
        "classLabels": ["A_HCM", "B_HCM"],
        "meaningMap": {"A_HCM": "A", "B_HCM": "B"},
        "displayTextMap": {"A": "Test A", "B": "Test B"},
        "demoReady": False,
    }
    write_json(tmp_path / "model_info.json", metadata)
    from visign_api.config import settings

    monkeypatch.setattr(
        settings, "feature_schema_version", schema["featureSchemaVersion"]
    )
    monkeypatch.setattr(
        "visign_ai.landmarks.holistic_extractor.extractor_identity",
        lambda *args: {"version": schema["extractorVersion"]},
    )
    predictor = PredictorRegistry().load_artifact(str(tmp_path))
    result = {
        "tensor": np.zeros((32, 234), np.float32),
        "point_valid": np.ones((8, 78), bool),
        "masks": np.ones((8, 4), bool),
        "report": {
            "ptsSpanMs": 1000,
            "inputStatus": "HAS_USABLE_FRAMES",
            "frameCount": 8,
            "timingsMs": {"decode": 1.0, "extractIncludingInit": 2.0, "transform": 1.0},
        },
    }
    monkeypatch.setattr(
        predictor._predictor, "clip_to_tensor", lambda clip, **kwargs: result
    )
    response = predictor.predict(tmp_path / "unused.webm", "test-request")
    assert response.classLabel == "B_HCM" and response.text == "Test B"
    assert response.confidence == pytest.approx(
        float(torch.softmax(torch.tensor([0.0, 2.0]), 0)[1])
    )
    assert predictor.metadata.demoReady is False
    result["report"]["ptsSpanMs"] = 20
    with pytest.raises(ClipTooShortException):
        predictor.predict(tmp_path / "unused.webm", "test-request")
