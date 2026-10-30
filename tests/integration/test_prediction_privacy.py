"""Privacy audit test asserting zero video bytes, frames, or PII are leaked in logs (T066)."""

import io
import json
import logging
import uuid
from fastapi.testclient import TestClient

from visign_api.config import settings
from visign_api.inference.predictor import BasePredictor, predictor_registry
from visign_api.main import app
from visign_api.observability import StructuredJsonFormatter, logger

VALID_WEBM_BYTES = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01mock_sensitive_video_payload_bytes"


def test_privacy_audit_zero_video_and_pii_leakage():
    """Verify logs contain only safe telemetry (durations, IDs) and never raw payload or biometric frames."""
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(StructuredJsonFormatter())
    logger.addHandler(handler)

    try:
        with TestClient(app) as client:
            req_id = str(uuid.uuid4())
            files = {"clip": ("sensitive_camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
            response = client.post("/api/v1/predictions", files=files, headers={"X-Request-ID": req_id})
            assert response.status_code == 200

        logged_content = log_stream.getvalue()

        # 1. Assert request ID is present for correlation
        assert req_id in logged_content

        # 2. Assert raw binary payload or clip filename is NOT in logs
        assert "mock_sensitive_video_payload_bytes" not in logged_content
        assert "sensitive_camera_clip" not in logged_content

        # 3. Assert no raw coordinates, frames or landmarks are logged
        assert "landmarks" not in logged_content
        assert "coordinates" not in logged_content

        # 4. Assert only safe telemetry keys are captured
        assert "processingTimeMs" in logged_content
        assert "modelVersion" in logged_content

    finally:
        logger.removeHandler(handler)


class _ExplodingPredictor(BasePredictor):
    def __init__(self, metadata):
        self._metadata = metadata

    @property
    def metadata(self):
        return self._metadata

    def predict(self, clip_path, request_id):
        raise RuntimeError("decoder crashed")


def test_privacy_failure_path_deletes_clip_and_logs_no_payload(monkeypatch, tmp_path):
    """On inference failure the clip is deleted and logs keep the error trace but not the video."""
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(StructuredJsonFormatter())
    logger.addHandler(handler)
    monkeypatch.setattr(settings, "temp_dir", str(tmp_path))

    try:
        with TestClient(app) as client:
            monkeypatch.setattr(
                predictor_registry,
                "_active_predictor",
                _ExplodingPredictor(predictor_registry.active_predictor.metadata),
            )
            req_id = str(uuid.uuid4())
            files = {"clip": ("sensitive_camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
            response = client.post("/api/v1/predictions", files=files, headers={"X-Request-ID": req_id})
            assert response.status_code == 500

        assert list(tmp_path.iterdir()) == []

        log_lines = [json.loads(line) for line in log_stream.getvalue().splitlines()]
        failure_logs = [r for r in log_lines if r.get("errorCode") == "PREDICTION_FAILED"]
        assert failure_logs, "prediction failure must be logged with its error code"
        assert any(r.get("requestId") == req_id for r in failure_logs)
        # Stack trace is kept for debugging...
        assert any("decoder crashed" in r.get("exception", "") for r in failure_logs)

        logged_content = log_stream.getvalue()
        # ...but never the payload or the client filename
        assert "mock_sensitive_video_payload_bytes" not in logged_content
        assert "sensitive_camera_clip" not in logged_content
    finally:
        logger.removeHandler(handler)
