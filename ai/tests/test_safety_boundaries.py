from types import SimpleNamespace

import numpy as np
import pytest
from visign_ai.evaluation.release_gate import passes_release_gate
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest
from visign_ai.training.sequence_dataset import SequenceDataset
from visign_ai.training.train import prepare


def test_training_refuses_draft_schema_before_accessing_manifest():
    with pytest.raises(ValueError, match="approval"):
        prepare(SimpleNamespace(schema=None))


def test_dataset_rejects_schema_mismatch_and_nonfinite_features(tmp_path):
    schema = load_schema()
    row = {"sampleId": "test", "classLabel": "A", "landmarkPath": "features.npz"}
    np.savez(
        tmp_path / "features.npz",
        features=np.zeros((32, 234), np.float32),
        featureSchemaVersion="wrong",
        extractorVersion=schema["extractorVersion"],
        schemaSha256=schema_digest(schema),
    )
    with pytest.raises(ValueError, match="mismatch"):
        SequenceDataset([row], tmp_path, ["A"], schema)
    features = np.zeros((32, 234), np.float32)
    features[0, 0] = np.nan
    np.savez(
        tmp_path / "features.npz",
        features=features,
        featureSchemaVersion=schema["featureSchemaVersion"],
        extractorVersion=schema["extractorVersion"],
        schemaSha256=schema_digest(schema),
    )
    with pytest.raises(ValueError, match="Non-finite"):
        SequenceDataset([row], tmp_path, ["A"], schema)


@pytest.mark.parametrize(
    "macro_f1,recall",
    [(float("nan"), 0.9), (0.9, float("nan")), (0.79, 0.9), (0.9, 0.64)],
)
def test_quality_gate_refuses_nonfinite_or_below_boundary(macro_f1, recall):
    meanings = [str(index) for index in range(10)]
    report = {
        "macroF1": macro_f1,
        "perMeaningRecall": dict.fromkeys(meanings, recall),
        "testSampleCounts": dict.fromkeys(meanings, 1),
        "splitAudit": {"passed": True, "mode": "signer-held-out"},
    }
    assert not passes_release_gate("full", meanings, report, meanings)
