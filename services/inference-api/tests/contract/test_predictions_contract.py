"""Contract tests for POST /api/v1/predictions across happy paths, edge cases, and errors (T030, T045)."""

import asyncio
import io
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from visign_api.api import predictions as predictions_module
from visign_api.api.predictions import InferenceCoordinator
from visign_api.config import settings
from visign_api.inference.prediction_decision import FALLBACK_REJECTED_TEXT
from visign_api.inference.predictor import BasePredictor, PredictorRegistry, predictor_registry

LOW_CONFIDENCE_FIXTURE_PATH = (
    Path(__file__).parents[1] / "fixtures" / "model-artifacts" / "fixture-low-confidence"
)

# Standard WebM EBML header followed by mock video data
VALID_WEBM_BYTES = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01mock_valid_payload"


def test_prediction_happy_path_fixture(client: TestClient):
    """Test standard happy path prediction returning accepted=True and valid contract schema."""
    custom_request_id = str(uuid.uuid4())
    files = {"clip": ("camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
    headers = {"X-Request-ID": custom_request_id}

    response = client.post("/api/v1/predictions", files=files, headers=headers)

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_request_id

    data = response.json()
    assert data["requestId"] == custom_request_id
    assert data["accepted"] is True
    assert data["classLabel"] == "XIN_CHAO_HCM_1"
    assert data["text"] == "Xin chào"
    assert data["confidence"] >= 0.70
    assert data["modelVersion"] == "vsl-fixture-v0.1.0"
    assert data["processingTimeMs"] >= 0

    # Optional diagnostics checks
    timings = data["timingsMs"]
    assert timings is not None
    assert timings["decode"] >= 0
    assert timings["extract"] >= 0
    assert timings["infer"] >= 0

    quality = data["qualityHints"]
    assert quality is not None
    assert 0.0 <= quality["handsDetectedRatio"] <= 1.0
    assert quality["frameCount"] >= 1


def test_prediction_generates_request_id_when_omitted(client: TestClient):
    """Test server generates and returns a valid UUID request ID when header is omitted."""
    files = {"clip": ("camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}

    response = client.post("/api/v1/predictions", files=files)

    assert response.status_code == 200
    response_req_id = response.headers.get("X-Request-ID")
    assert response_req_id is not None
    # Validate it is a valid UUID
    uuid_obj = uuid.UUID(response_req_id)
    assert str(uuid_obj) == response_req_id

    data = response.json()
    assert data["requestId"] == response_req_id


def test_prediction_missing_clip_file_400(client: TestClient):
    """Missing clip multipart field must return 400 INVALID_REQUEST."""
    response = client.post("/api/v1/predictions", data={})

    assert response.status_code == 400
    assert "X-Request-ID" in response.headers
    data = response.json()
    assert data["code"] == "INVALID_REQUEST"
    assert "requestId" in data


def test_prediction_unsupported_media_type_415(client: TestClient):
    """Unsupported MIME type must return 415 UNSUPPORTED_MEDIA_TYPE."""
    files = {"clip": ("camera_clip.mp4", io.BytesIO(VALID_WEBM_BYTES), "video/mp4")}

    response = client.post("/api/v1/predictions", files=files)

    assert response.status_code == 415
    assert "X-Request-ID" in response.headers
    data = response.json()
    assert data["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert "requestId" in data


def test_prediction_clip_too_large_413(client: TestClient):
    """Oversized clip exceeding max_clip_size_bytes must return 413 CLIP_TOO_LARGE."""
    oversized_data = VALID_WEBM_BYTES + (b"0" * (10 * 1024 * 1024 + 100))
    files = {"clip": ("camera_clip.webm", io.BytesIO(oversized_data), "video/webm")}

    response = client.post("/api/v1/predictions", files=files)

    assert response.status_code == 413
    assert "X-Request-ID" in response.headers
    data = response.json()
    assert data["code"] == "CLIP_TOO_LARGE"


def test_prediction_corrupt_or_non_webm_magic_bytes_422(client: TestClient):
    """A clip lacking EBML header bytes must fail with 422 CLIP_DECODE_FAILED."""
    corrupted_data = b"not_webm_header_bytes_random_junk"
    files = {"clip": ("camera_clip.webm", io.BytesIO(corrupted_data), "video/webm")}

    response = client.post("/api/v1/predictions", files=files)

    assert response.status_code == 422
    assert "X-Request-ID" in response.headers
    data = response.json()
    assert data["code"] == "CLIP_DECODE_FAILED"


def test_prediction_service_busy_503(client: TestClient, monkeypatch):
    """When coordinator cannot acquire slot, returns 503 SERVICE_BUSY with Retry-After header."""
    busy_coordinator = InferenceCoordinator(max_concurrent=1, timeout_seconds=0.05, retry_after=3)
    busy_coordinator._semaphore = asyncio.Semaphore(0)
    monkeypatch.setattr(predictions_module, "inference_coordinator", busy_coordinator)

    files = {"clip": ("camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
    response = client.post("/api/v1/predictions", files=files)

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "3"
    data = response.json()
    assert data["code"] == "SERVICE_BUSY"
    assert data["requestId"] == response.headers["X-Request-ID"]


def test_prediction_low_confidence_returns_rejected_200(client: TestClient, monkeypatch):
    """Low confidence is a normal HTTP 200 outcome with accepted=false and the fallback text."""
    low_confidence_predictor = PredictorRegistry().load_artifact(str(LOW_CONFIDENCE_FIXTURE_PATH))
    monkeypatch.setattr(predictor_registry, "_active_predictor", low_confidence_predictor)

    files = {"clip": ("camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
    response = client.post("/api/v1/predictions", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] is False
    assert data["classLabel"] is None
    assert data["text"] == FALLBACK_REJECTED_TEXT
    assert data["confidence"] == pytest.approx(0.42)
    assert data["modelVersion"] == "vsl-fixture-low-confidence-v0.1.0"
    assert data["requestId"] == response.headers["X-Request-ID"]


def test_prediction_model_not_ready_503(client: TestClient, monkeypatch):
    """Without a loaded artifact the endpoint returns 503 MODEL_NOT_READY with Retry-After."""
    monkeypatch.setattr(predictor_registry, "_active_predictor", None)

    files = {"clip": ("camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
    response = client.post("/api/v1/predictions", files=files)

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    data = response.json()
    assert data["code"] == "MODEL_NOT_READY"
    assert data["requestId"] == response.headers["X-Request-ID"]


class _FailingPredictor(BasePredictor):
    """Test double whose inference raises an internal error."""

    def __init__(self, metadata):
        self._metadata = metadata

    @property
    def metadata(self):
        return self._metadata

    def predict(self, clip_path, request_id):
        raise RuntimeError("internal-secret-detail C:\\models\\weights.pt")


def test_prediction_unexpected_failure_500_hides_internal_detail(client: TestClient, monkeypatch, tmp_path):
    """Unexpected predictor errors map to 500 PREDICTION_FAILED without leaking exception text."""
    failing = _FailingPredictor(predictor_registry.active_predictor.metadata)
    monkeypatch.setattr(predictor_registry, "_active_predictor", failing)
    monkeypatch.setattr(settings, "temp_dir", str(tmp_path))
    custom_id = str(uuid.uuid4())

    files = {"clip": ("camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
    response = client.post("/api/v1/predictions", files=files, headers={"X-Request-ID": custom_id})

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == custom_id
    data = response.json()
    assert data["code"] == "PREDICTION_FAILED"
    assert data["requestId"] == custom_id
    assert "internal-secret-detail" not in response.text
    assert "weights.pt" not in response.text
    # Temporary clip must be deleted on the failure path as well
    assert list(tmp_path.iterdir()) == []


def test_prediction_accepts_webm_with_codec_parameters(client: TestClient):
    files = {"clip": ("camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm;codecs=vp9")}

    response = client.post("/api/v1/predictions", files=files)

    assert response.status_code == 200


def test_prediction_empty_clip_400(client: TestClient):
    files = {"clip": ("camera_clip.webm", io.BytesIO(b""), "video/webm")}

    response = client.post("/api/v1/predictions", files=files)

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


def test_prediction_replaces_invalid_request_id(client: TestClient):
    """A non-UUID X-Request-ID is not echoed; the server generates a valid UUID instead."""
    files = {"clip": ("camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}

    response = client.post("/api/v1/predictions", files=files, headers={"X-Request-ID": "abc<script>"})

    assert response.status_code == 200
    effective_id = response.headers["X-Request-ID"]
    assert effective_id != "abc<script>"
    assert str(uuid.UUID(effective_id)) == effective_id
    assert response.json()["requestId"] == effective_id


@pytest.mark.parametrize(
    "files,expected_status",
    [
        (None, 400),
        ({"clip": ("c.mp4", io.BytesIO(VALID_WEBM_BYTES), "video/mp4")}, 415),
        ({"clip": ("c.webm", io.BytesIO(b"not_webm"), "video/webm")}, 422),
    ],
)
def test_error_responses_echo_caller_request_id(client: TestClient, files, expected_status):
    """Every error envelope carries the caller's X-Request-ID in both header and body."""
    custom_id = str(uuid.uuid4())

    response = client.post("/api/v1/predictions", files=files, headers={"X-Request-ID": custom_id})

    assert response.status_code == expected_status
    assert response.headers["X-Request-ID"] == custom_id
    assert response.json()["requestId"] == custom_id
