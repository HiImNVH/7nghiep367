"""Serving feature-schema version comes from the shared schema file unless overridden (T037)."""

import json
from pathlib import Path

import pytest

from visign_api.config import REPO_ROOT, settings
from visign_api.domain.errors import ModelNotReadyException
from visign_api.inference.predictor import PredictorRegistry

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
ARTIFACTS_DIR = FIXTURES_DIR / "model-artifacts"
TEST_SCHEMA_PATH = FIXTURES_DIR / "feature_schema.json"
SHARED_SCHEMA_PATH = REPO_ROOT / "ai" / "configs" / "feature_schema.json"
FIXTURE_ARTIFACTS = ["fixture", "fixture-low-confidence"]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_schema(path: Path, version: str) -> Path:
    path.write_text(json.dumps({"featureSchemaVersion": version}), encoding="utf-8")
    return path


def test_version_is_read_from_schema_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "feature_schema_version", "")
    monkeypatch.setattr(settings, "feature_schema_path", str(_write_schema(tmp_path / "s.json", "from-file-v1")))

    assert settings.serving_feature_schema_version() == "from-file-v1"


def test_explicit_version_overrides_schema_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "feature_schema_version", "explicit-v1")
    monkeypatch.setattr(settings, "feature_schema_path", str(tmp_path / "missing.json"))

    assert settings.serving_feature_schema_version() == "explicit-v1"


@pytest.mark.parametrize("schema_content", [None, "{not json", json.dumps({"status": "DRAFT"})])
def test_unusable_schema_file_fails_artifact_load_closed(tmp_path, monkeypatch, schema_content):
    schema_path = tmp_path / "feature_schema.json"
    if schema_content is not None:
        schema_path.write_text(schema_content, encoding="utf-8")
    monkeypatch.setattr(settings, "feature_schema_version", "")
    monkeypatch.setattr(settings, "feature_schema_path", str(schema_path))

    with pytest.raises(ModelNotReadyException):
        PredictorRegistry().load_artifact(str(ARTIFACTS_DIR / "fixture"))


@pytest.mark.parametrize("artifact", FIXTURE_ARTIFACTS)
def test_fixture_artifacts_match_test_schema_copy(artifact):
    schema = _read_json(TEST_SCHEMA_PATH)
    info = _read_json(ARTIFACTS_DIR / artifact / "model_info.json")

    assert info["featureSchemaVersion"] == schema["featureSchemaVersion"]
    assert info["extractorVersion"] == schema["extractorVersion"]


@pytest.mark.skipif(not SHARED_SCHEMA_PATH.exists(), reason="ai/ package is not in this checkout")
def test_test_schema_copy_tracks_shared_ai_schema():
    """Fails when Cường bumps the shared schema: update the test copy and fixture artifacts with it."""
    shared = _read_json(SHARED_SCHEMA_PATH)
    test_copy = _read_json(TEST_SCHEMA_PATH)

    assert test_copy["featureSchemaVersion"] == shared["featureSchemaVersion"]
    assert test_copy["extractorVersion"] == shared["extractorVersion"]
