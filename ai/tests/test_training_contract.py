import pytest
import torch
from visign_ai.dataset.manifest import audit_splits
from visign_ai.evaluation.metrics import meaning_metrics
from visign_ai.evaluation.release_gate import passes_release_gate
from visign_ai.training.gru_classifier import GRUClassifier


def test_packed_gru_ignores_padding_and_is_deterministic():
    torch.manual_seed(42)
    model = GRUClassifier(6, 8, 3).eval()
    sequence = torch.randn(2, 5, 6)
    lengths = torch.tensor([2, 5])
    with torch.inference_mode():
        original = model(sequence, lengths)
        sequence[0, 2:] = 1000
        changed = model(sequence, lengths)
    assert original.shape == (2, 3)
    torch.testing.assert_close(original, changed)
    torch.testing.assert_close(changed, model(sequence, lengths))


def test_meaning_metrics_aggregate_variants():
    metrics = meaning_metrics(["A", "A", "B"], ["A", "B", "B"], ["A", "B"])
    assert metrics["accuracy"] == pytest.approx(2 / 3)
    assert metrics["macroF1"] == pytest.approx(2 / 3)
    assert metrics["perMeaningRecall"] == {"A": 0.5, "B": 1.0}
    assert metrics["confusionMatrix"] == [[1, 1], [0, 1]]


def test_release_requires_full_signer_provenance_and_all_meanings():
    meanings = [str(i) for i in range(10)]
    report = {
        "macroF1": 0.8,
        "perMeaningRecall": dict.fromkeys(meanings, 0.65),
        "splitAudit": {"mode": "signer-held-out", "passed": True},
        "testSampleCounts": dict.fromkeys(meanings, 1),
    }
    assert passes_release_gate("full", meanings, report, meanings)
    assert not passes_release_gate("pilot", meanings, report, meanings)
    report["splitAudit"]["mode"] = "session-only"
    assert not passes_release_gate("full", meanings, report, meanings)


def test_split_audit_rejects_shared_signer_or_session():
    rows = [
        {
            "sampleId": str(i),
            "split": split,
            "signerId": signer,
            "recordingSessionId": session,
        }
        for i, (split, signer, session) in enumerate(
            [("train", "one", "a"), ("validation", "two", "b"), ("test", "three", "c")]
        )
    ]
    assert audit_splits(rows, "full")["mode"] == "signer-held-out"
    rows[2]["signerId"] = "one"
    with pytest.raises(ValueError, match="signer"):
        audit_splits(rows, "full")
    rows[2]["signerId"] = ""
    with pytest.raises(ValueError, match="signer"):
        audit_splits(rows, "full")
    assert audit_splits(rows, "pilot")["mode"] == "session-only"
