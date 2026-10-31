"""Shared setup for API integration tests."""

import pytest

from visign_api.config import settings
from visign_api.inference.predictor import predictor_registry


@pytest.fixture(autouse=True)
def load_default_artifact():
    """Start every test from the configured fixture artifact so tests can run in isolation."""
    predictor_registry.load_artifact(settings.model_artifact_path)
