import json
from pathlib import Path

import pytest
import torch
from visign_ai.inference import GRUPredictor
from visign_ai.io import write_json


def test_checkpoint_refuses_changed_sampling_with_same_version(
    synthetic_pilot_artifact,
):
    path = synthetic_pilot_artifact / "feature_schema.json"
    schema = json.loads(path.read_text("utf-8"))
    schema["preExtractionSampling"]["maxFrames"] = 32
    write_json(path, schema)
    with pytest.raises(ValueError, match="schema content mismatch"):
        GRUPredictor(synthetic_pilot_artifact)


def test_new_schema_cannot_load_an_unbound_checkpoint(synthetic_pilot_artifact):
    path = synthetic_pilot_artifact / "model.pt"
    checkpoint = torch.load(path, weights_only=True)
    checkpoint.pop("schemaSha256")
    torch.save(checkpoint, path)
    with pytest.raises(ValueError, match="schema content mismatch"):
        GRUPredictor(synthetic_pilot_artifact)


def test_exact_old_draft_checkpoint_still_loads(synthetic_pilot_artifact):
    legacy_path = (
        Path(__file__).resolve().parents[1] / "configs/feature_schema.legacy-v0.2.json"
    )
    schema = json.loads(legacy_path.read_text("utf-8"))
    write_json(synthetic_pilot_artifact / "feature_schema.json", schema)
    metadata_path = synthetic_pilot_artifact / "model_info.json"
    metadata = json.loads(metadata_path.read_text("utf-8"))
    metadata["featureSchemaVersion"] = schema["featureSchemaVersion"]
    write_json(metadata_path, metadata)
    model_path = synthetic_pilot_artifact / "model.pt"
    checkpoint = torch.load(model_path, weights_only=True)
    checkpoint.pop("schemaSha256")
    torch.save(checkpoint, model_path)
    predictor = GRUPredictor(synthetic_pilot_artifact)
    assert predictor.metadata["featureSchemaVersion"] == "demo2-xy-32-v0.2-draft"
