"""Pytest configuration and shared fixtures for inference API tests."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from visign_api.config import settings
from visign_api.inference.predictor import predictor_registry
from visign_api.main import app

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "model-artifacts" / "fixture"


@pytest.fixture(scope="session", autouse=True)
def setup_test_settings():
    """Ensure test runs with the fixture model artifact."""
    settings.model_artifact_path = str(FIXTURE_PATH)
    predictor_registry.load_artifact(str(FIXTURE_PATH))


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client
