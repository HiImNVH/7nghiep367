"""Transport/export behavior only. All metrics and model fixtures are synthetic test data."""

import json
import shutil

import pytest
from visign_ai.io import write_json
from visign_api.domain.errors import ModelNotReadyException
from visign_api.inference.artifact_integrity import (
    DELIVERY_FILES,
    MANIFEST_NAME,
    file_sha256,
    verify_delivery,
)
from visign_api.inference.package_artifact import package_artifact
from visign_api.inference.predictor import PredictorRegistry


@pytest.fixture
def evaluated_delivery_input(synthetic_pilot_artifact):
    path = synthetic_pilot_artifact / "evaluated-input"
    path.mkdir()
    for name in ("model.pt", "model_info.json", "feature_schema.json"):
        shutil.copyfile(synthetic_pilot_artifact / name, path / name)
    metadata = json.loads((path / "model_info.json").read_text("utf-8"))
    metadata.update(accuracy=0.5, macroF1=0.5, perMeaningPrecision={"A":0.5,"B":0.5},
                    perMeaningRecall={"A":0.5,"B":0.5}, evaluatedAt="2026-11-01T00:00:00+00:00")
    write_json(path / "model_info.json", metadata)
    write_json(path / "training-report.json", {"scope":"synthetic test only"})
    write_json(path / "evaluation-report.json", metadata)
    (path / "confusion-matrix.png").write_bytes(b"synthetic test diagram placeholder")
    return path


def stub_preflight(monkeypatch, fail=False):
    def check(*args):
        if fail:
            raise ValueError("Parity failed")
        return {"parity":{"status":"PASSED"}, "prediction":{"text":"test only"},
                "demoReady":False}
    monkeypatch.setattr("visign_api.inference.package_artifact.check_artifact",check)


def test_export_checks_exact_staged_bytes_and_is_immutable(evaluated_delivery_input, tmp_path, monkeypatch):
    original = evaluated_delivery_input
    clip = tmp_path / "golden.webm"
    clip.write_bytes(b"test reference")
    def inspect_staging(staging, filename):
        assert staging != original
        for name in DELIVERY_FILES[:-1]:
            assert (staging / name).read_bytes() == (original / name).read_bytes()
        return {"parity":{"status":"PASSED"},"prediction":{"text":"Test only"}}
    monkeypatch.setattr("visign_api.inference.package_artifact.check_artifact",inspect_staging)
    output = tmp_path / "delivery"
    package_artifact(original, clip, output)
    assert verify_delivery(output, required=True)
    report=json.loads((output/"parity-report.json").read_text("utf-8"))
    assert report["goldenClipSha256"] == file_sha256(clip)
    assert "prediction" not in report
    assert not (original / MANIFEST_NAME).exists()
    with pytest.raises(FileExistsError):
        package_artifact(original, clip, output)


@pytest.mark.parametrize("failure",["parity","dataset","metric","missing"])
def test_export_never_publishes_failed_candidate(evaluated_delivery_input, tmp_path, monkeypatch, failure):
    stub_preflight(monkeypatch,fail=failure=="parity")
    artifact=evaluated_delivery_input
    if failure=="dataset" or failure=="metric":
        p=artifact/"evaluation-report.json"
        value=json.loads(p.read_text("utf-8"))
        value["datasetVersion" if failure=="dataset" else "accuracy"]="wrong"
        write_json(p,value)
    if failure=="missing":
        (artifact/"evaluation-report.json").unlink()
    with pytest.raises(ValueError):
        package_artifact(artifact,tmp_path/"unused.webm",tmp_path/"delivery")
    assert not (tmp_path/"delivery").exists()
    assert not list(tmp_path.glob(".visign-*"))


@pytest.mark.parametrize("name",DELIVERY_FILES)
def test_backend_rejects_tampered_delivery_before_predictor_load(evaluated_delivery_input,tmp_path,monkeypatch,name):
    stub_preflight(monkeypatch)
    clip=tmp_path/"golden.webm"
    clip.write_bytes(b"synthetic reference")
    output=tmp_path/"delivery"
    package_artifact(evaluated_delivery_input,clip,output)
    (output/name).write_bytes(b"changed after delivery")
    with pytest.raises(ValueError,match="checksum mismatch"):
        verify_delivery(output,required=True)
    with pytest.raises(ModelNotReadyException,match="checksum mismatch"):
        PredictorRegistry().load_artifact(str(output))


def test_delivery_manifest_cannot_claim_paths_outside_artifact(tmp_path):
    write_json(tmp_path/MANIFEST_NAME,{"algorithm":"SHA-256","sha256":{"../outside":"bad"}})
    with pytest.raises(ValueError,match="exactly"):
        verify_delivery(tmp_path,required=True)


def test_unpacked_training_artifacts_keep_legacy_compatibility(tmp_path):
    assert verify_delivery(tmp_path) is False
    with pytest.raises(ValueError,match="Missing delivery"):
        verify_delivery(tmp_path,required=True)


def test_delivery_cannot_be_written_inside_source(evaluated_delivery_input):
    with pytest.raises(ValueError, match="outside"):
        package_artifact(evaluated_delivery_input, "unused.webm", evaluated_delivery_input / "nested")
