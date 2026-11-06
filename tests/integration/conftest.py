"""Shared setup for API integration tests."""

from pathlib import Path

import pytest

from visign_api.config import settings
from visign_api.inference.predictor import predictor_registry

TEST_SCHEMA_PATH = (
    Path(__file__).parents[2] / "services" / "inference-api" / "tests" / "fixtures" / "feature_schema.json"
)


@pytest.fixture(autouse=True)
def load_default_artifact(monkeypatch):
    """Start every test from the configured fixture artifact so tests can run in isolation."""
    monkeypatch.setattr(settings, "feature_schema_path", str(TEST_SCHEMA_PATH))
    monkeypatch.setattr(settings, "feature_schema_version", "")
    predictor_registry.load_artifact(settings.model_artifact_path)
