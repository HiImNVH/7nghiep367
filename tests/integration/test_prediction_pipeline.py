"""Integration tests for end-to-end prediction pipeline and artifact swapping (T064)."""

import asyncio
import io
import json
import threading
import time
import uuid
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from visign_api.api import predictions as predictions_module
from visign_api.api.predictions import InferenceCoordinator
from visign_api.config import settings
from visign_api.domain.model_version import ArtifactKind
from visign_api.inference.predictor import (
    PREDICTOR_FACTORIES,
    BasePredictor,
    FixturePredictor,
    predictor_registry,
)
from visign_api.main import app

VALID_WEBM_BYTES = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01mock_valid_payload"

PILOT_METADATA = {
    "modelVersion": "vsl-pilot-v0.2.0",
    "artifactKind": "pilot",
    "datasetVersion": "pilot-manifest-hash-123",
    "featureSchemaVersion": "vsl-feature-v1.0",
    "extractorVersion": "mediapipe-holistic-0.10.14",
    "meanings": ["XIN_CHAO", "CAM_ON"],
    "classLabels": ["XIN_CHAO_HCM_1", "CAM_ON_HCM_1"],
    "meaningMap": {"XIN_CHAO_HCM_1": "XIN_CHAO", "CAM_ON_HCM_1": "CAM_ON"},
    "displayTextMap": {"XIN_CHAO": "Xin chào", "CAM_ON": "Cảm ơn"},
    "acceptanceThreshold": 0.70,
    "accuracy": 0.88,
    "macroF1": 0.85,
    "perMeaningPrecision": {"XIN_CHAO": 0.9, "CAM_ON": 0.85},
    "perMeaningRecall": {"XIN_CHAO": 0.88, "CAM_ON": 0.82},
    "evaluatedAt": "2026-10-29T10:00:00Z",
    "demoReady": False,
}


def _write_pilot_artifact(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory / "model_info.json", "w", encoding="utf-8") as f:
        json.dump(PILOT_METADATA, f, ensure_ascii=False)
    return directory


def _pilot_test_double_factory(artifact_dir, metadata, display_text_map, extras):
    """Stands in for the GRU predictor so the swap path can be exercised before T036 lands."""
    return FixturePredictor(metadata, display_text_map)


def test_e2e_prediction_pipeline_with_cleanup(monkeypatch, tmp_path):
    """Verify full HTTP request -> prediction -> guaranteed temporary file cleanup."""
    monkeypatch.setattr(settings, "temp_dir", str(tmp_path))

    with TestClient(app) as client:
        req_id = str(uuid.uuid4())
        files = {"clip": ("camera.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
        response = client.post("/api/v1/predictions", files=files, headers={"X-Request-ID": req_id})

        assert response.status_code == 200
        data = response.json()
        assert data["requestId"] == req_id
        assert data["accepted"] is True
        assert data["classLabel"] == "XIN_CHAO_HCM_1"

    assert list(tmp_path.iterdir()) == []


def test_artifact_swap_without_changing_contract(monkeypatch, tmp_path):
    """Verify swapping from fixture to pilot artifact updates model-info while maintaining endpoint contract."""
    monkeypatch.setitem(PREDICTOR_FACTORIES, ArtifactKind.PILOT, _pilot_test_double_factory)
    pilot_dir = _write_pilot_artifact(tmp_path / "pilot-artifact")
    old_artifact_path = settings.model_artifact_path

    # 1. Point MODEL_ARTIFACT_PATH at the pilot and "restart" via the lifespan
    settings.model_artifact_path = str(pilot_dir)
    try:
        with TestClient(app) as client:
            info_res = client.get("/api/v1/model-info")
            assert info_res.status_code == 200
            info_data = info_res.json()
            assert info_data["modelVersion"] == "vsl-pilot-v0.2.0"
            assert info_data["artifactKind"] == "pilot"
            assert info_data["meanings"] == ["XIN_CHAO", "CAM_ON"]
            assert info_data["demoReady"] is False
            assert info_data["macroF1"] == 0.85

            # Prediction still functions with identical response schema
            files = {"clip": ("camera.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
            pred_res = client.post("/api/v1/predictions", files=files)
            assert pred_res.status_code == 200
            pred_data = pred_res.json()
            assert pred_data["modelVersion"] == "vsl-pilot-v0.2.0"
            assert set(pred_data) >= {
                "requestId", "text", "classLabel", "confidence",
                "accepted", "modelVersion", "processingTimeMs",
            }
    finally:
        # 2. Roll back to the original fixture artifact
        settings.model_artifact_path = old_artifact_path
        predictor_registry.load_artifact(old_artifact_path)

    with TestClient(app) as client:
        info_res = client.get("/api/v1/model-info")
        assert info_res.status_code == 200
        assert info_res.json()["modelVersion"] == "vsl-fixture-v0.1.0"


def test_pilot_artifact_without_predictor_keeps_previous_model(monkeypatch, tmp_path):
    """Pilot weights cannot be served yet: startup must fail closed and keep the last working artifact."""
    pilot_dir = _write_pilot_artifact(tmp_path / "pilot-artifact")
    monkeypatch.setattr(settings, "model_artifact_path", str(pilot_dir))

    with TestClient(app) as client:
        info_res = client.get("/api/v1/model-info")
        assert info_res.status_code == 200
        assert info_res.json()["artifactKind"] == "fixture"


def test_startup_with_broken_artifact_runs_degraded(monkeypatch, tmp_path):
    """With no previous artifact, a failed load leaves the API up but not ready."""
    monkeypatch.setattr(predictor_registry, "_active_predictor", None)
    monkeypatch.setattr(settings, "model_artifact_path", str(tmp_path / "missing-artifact"))

    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "degraded"

        files = {"clip": ("camera.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
        pred_res = client.post("/api/v1/predictions", files=files)
        assert pred_res.status_code == 503
        assert pred_res.json()["code"] == "MODEL_NOT_READY"


class _SlowPredictor(BasePredictor):
    """Blocking predictor simulating CPU-bound MediaPipe/GRU inference."""

    def __init__(self, inner: BasePredictor, delay_seconds: float):
        self._inner = inner
        self._delay_seconds = delay_seconds
        self.started = threading.Event()
        self.running = threading.Event()

    @property
    def metadata(self):
        return self._inner.metadata

    def predict(self, clip_path, request_id):
        self.started.set()
        self.running.set()
        try:
            time.sleep(self._delay_seconds)
            return self._inner.predict(clip_path, request_id)
        finally:
            self.running.clear()


def test_concurrent_request_gets_service_busy_while_inference_runs(monkeypatch):
    """A second request waiting longer than the inference timeout receives 503 SERVICE_BUSY."""
    slow = _SlowPredictor(predictor_registry.active_predictor, delay_seconds=0.6)
    monkeypatch.setattr(predictor_registry, "_active_predictor", slow)
    monkeypatch.setattr(
        predictions_module,
        "inference_coordinator",
        InferenceCoordinator(max_concurrent=1, timeout_seconds=0.1, retry_after=3),
    )

    async def send_two_requests():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            async def post():
                files = {"clip": ("camera.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
                return await client.post("/api/v1/predictions", files=files)

            return await asyncio.gather(post(), post())

    responses = asyncio.run(send_two_requests())

    statuses = sorted(r.status_code for r in responses)
    assert statuses == [200, 503]
    busy = next(r for r in responses if r.status_code == 503)
    assert busy.json()["code"] == "SERVICE_BUSY"
    assert busy.headers["Retry-After"] == "3"


def test_health_stays_responsive_during_inference(monkeypatch):
    """Inference must not block the event loop; health answers while a prediction is running."""
    slow = _SlowPredictor(predictor_registry.active_predictor, delay_seconds=0.6)
    monkeypatch.setattr(predictor_registry, "_active_predictor", slow)
    monkeypatch.setattr(
        predictions_module,
        "inference_coordinator",
        InferenceCoordinator(max_concurrent=1, timeout_seconds=3.0, retry_after=3),
    )

    async def predict_and_probe_health():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            files = {"clip": ("camera.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
            prediction = asyncio.create_task(client.post("/api/v1/predictions", files=files))
            for _ in range(200):
                if slow.started.is_set():
                    break
                await asyncio.sleep(0.01)
            health = await client.get("/api/v1/health")
            # If predict() blocked the event loop, health could only answer after it finished
            predictor_still_running = slow.running.is_set()
            return await prediction, health, predictor_still_running

    prediction, health, predictor_still_running = asyncio.run(predict_and_probe_health())

    assert prediction.status_code == 200
    assert health.status_code == 200
    assert predictor_still_running is True
