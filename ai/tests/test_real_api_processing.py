"""Real WebM and HTTP request with an isolated, synthetic GRU test checkpoint."""

import os
import time
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from visign_ai.io import write_json
from visign_ai.landmarks.pipeline import process_video
from visign_ai.landmarks.sequence_transform import load_schema
from visign_api.config import settings
from visign_api.inference.predictor import PredictorRegistry
from visign_api.main import app


def test_real_api_preprocessing_parity_cleanup_and_latency(
    synthetic_pilot_artifact, monkeypatch
):
    clip_path = os.environ.get("VISIGN_API_PERF_CLIP")
    if not clip_path:
        pytest.skip(
            "Provide VISIGN_API_PERF_CLIP with local WebM for integration measurement"
        )
    clip_path = Path(clip_path)
    schema_path = synthetic_pilot_artifact / "feature_schema.json"
    schema = load_schema(schema_path)
    monkeypatch.setattr(
        settings, "feature_schema_version", schema["featureSchemaVersion"]
    )
    monkeypatch.setattr(settings, "model_artifact_path", str(synthetic_pilot_artifact))
    temporary_clips = synthetic_pilot_artifact / "temporary-clips"
    temporary_clips.mkdir()
    monkeypatch.setattr(settings, "temp_dir", str(temporary_clips))
    registry = PredictorRegistry()
    for module in (
        "visign_api.main",
        "visign_api.api.predictions",
        "visign_api.api.system",
    ):
        monkeypatch.setattr(module + ".predictor_registry", registry)
    offline = process_video(clip_path, schema_path=schema_path)
    observed = []

    def capture(*args, **kwargs):
        result = process_video(*args, **kwargs)
        observed.append(result)
        return result

    monkeypatch.setattr("visign_ai.inference.process_video", capture)
    measurements = []
    content = clip_path.read_bytes()
    with TestClient(app) as client:
        for _ in range(5):
            start = time.perf_counter()
            response = client.post(
                "/api/v1/predictions",
                files={"clip": ("camera.webm", content, "video/webm")},
            )
            measurements.append((time.perf_counter() - start) * 1000)
            assert response.status_code == 200, response.text
            body = response.json()
            assert (
                body["modelVersion"] == "synthetic-test-only"
                and body["accepted"] is True
            )
            assert "landmarks" not in body and "frames" not in body
            assert not list(temporary_clips.iterdir())
            np.testing.assert_allclose(
                observed[-1]["tensor"], offline["tensor"], rtol=0, atol=1e-6
            )
    p95 = float(np.percentile(measurements, 95))
    write_json(
        synthetic_pilot_artifact / "api-performance.json",
        {
            "scope": "TestClient HTTP + real WebM preprocessing + synthetic GRU; excludes browser UI/network",
            "sampleCount": 5,
            "durationsMs": measurements,
            "p95Ms": p95,
            "demoReady": False,
        },
    )
    if os.environ.get("VISIGN_ENFORCE_LATENCY") == "1":
        assert p95 <= 3000, measurements
