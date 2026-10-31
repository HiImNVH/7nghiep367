import pytest
import torch
from visign_ai.io import write_json
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest
from visign_ai.training.gru_classifier import GRUClassifier


@pytest.fixture
def synthetic_pilot_artifact(tmp_path):
    schema = load_schema()
    schema["status"] = "APPROVED"  # Isolated test fixture, never a real approval.
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
    write_json(
        tmp_path / "model_info.json",
        {
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
        },
    )
    return tmp_path
