"""GRU adapter maps every AI pipeline error to a stable API error (T037, T049).

These tests never import the real visign_ai package: a stub PipelineError is installed in
sys.modules, so they run in backend-only checkouts as well.
"""

import io
import sys
import types

import pytest
from fastapi.testclient import TestClient

from visign_api.config import settings
from visign_api.domain.errors import ErrorCode, ViSignApiException
from visign_api.inference.gru_predictor import GRUApiPredictor, map_pipeline_error
from visign_api.inference.predictor import predictor_registry

VALID_WEBM_BYTES = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01mock_valid_payload"


@pytest.mark.parametrize(
    "pipeline_code,expected_code,expected_status",
    [
        # Problems with the user's clip: 4xx, user can record again
        ("CLIP_TOO_SHORT", ErrorCode.CLIP_TOO_SHORT, 422),
        ("CLIP_TOO_LONG", ErrorCode.CLIP_TOO_LONG, 422),
        ("NO_PERSON_DETECTED", ErrorCode.NO_PERSON_DETECTED, 422),
        ("INSUFFICIENT_LANDMARKS", ErrorCode.INSUFFICIENT_LANDMARKS, 422),
        ("CLIP_DECODE_FAILED", ErrorCode.CLIP_DECODE_FAILED, 422),
        ("INVALID_TIMESTAMPS", ErrorCode.CLIP_DECODE_FAILED, 422),
        ("INVALID_REQUEST", ErrorCode.CLIP_DECODE_FAILED, 422),
        ("UNSUPPORTED_MEDIA_TYPE", ErrorCode.UNSUPPORTED_MEDIA_TYPE, 415),
        ("CLIP_TOO_LARGE", ErrorCode.CLIP_TOO_LARGE, 413),
        # Server-side schema/extractor/detector mismatch: never blame the clip
        ("FEATURE_SCHEMA_MISMATCH", ErrorCode.MODEL_NOT_READY, 503),
        ("EXTRACTOR_VERSION_MISMATCH", ErrorCode.MODEL_NOT_READY, 503),
        ("MODEL_ASSET_MISMATCH", ErrorCode.MODEL_NOT_READY, 503),
        # Codes added later in the AI package must not be reported as a broken clip
        ("SOME_FUTURE_CODE", ErrorCode.PREDICTION_FAILED, 500),
    ],
)
def test_pipeline_codes_map_to_stable_api_errors(pipeline_code, expected_code, expected_status):
    error = map_pipeline_error(pipeline_code)

    assert isinstance(error, ViSignApiException)
    assert error.code == expected_code
    assert error.status_code == expected_status


class _StubPipelineError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class _RaisingInnerPredictor:
    def __init__(self, code):
        self._code = code

    def predict(self, clip, **kwargs):
        raise _StubPipelineError(self._code, "internal pipeline detail")


@pytest.fixture
def stub_visign_ai(monkeypatch):
    errors_module = types.ModuleType("visign_ai.landmarks.errors")
    errors_module.PipelineError = _StubPipelineError
    monkeypatch.setitem(sys.modules, "visign_ai", types.ModuleType("visign_ai"))
    monkeypatch.setitem(sys.modules, "visign_ai.landmarks", types.ModuleType("visign_ai.landmarks"))
    monkeypatch.setitem(sys.modules, "visign_ai.landmarks.errors", errors_module)


def _adapter_raising(code: str) -> GRUApiPredictor:
    """Adapter wired to a failing inner predictor, bypassing the real model loading in __init__."""
    adapter = object.__new__(GRUApiPredictor)
    adapter._metadata = predictor_registry.active_predictor.metadata
    adapter._predictor = _RaisingInnerPredictor(code)
    return adapter


class _RecordingInnerPredictor:
    """Successful inner predictor that records the duration limits it was called with."""

    def __init__(self):
        self.calls = []

    def predict(self, clip, **kwargs):
        self.calls.append(kwargs)
        return {
            "classLabel": "CAM_ON_HCM_1",
            "confidence": 0.81,
            "text": "Cảm ơn",
            "timingsMs": {"decode": 10, "extract": 900, "infer": 5},
            "qualityHints": {"handsDetectedRatio": 0.75, "frameCount": 64},
        }


def test_adapter_passes_configured_duration_limits_and_converts_result(stub_visign_ai, tmp_path, monkeypatch):
    """The AI pipeline owns the PTS duration check; the API must hand it the configured limits."""
    monkeypatch.setattr(settings, "min_duration_ms", 450)
    monkeypatch.setattr(settings, "max_duration_ms", 4000)
    adapter = object.__new__(GRUApiPredictor)
    adapter._metadata = predictor_registry.active_predictor.metadata
    adapter._predictor = _RecordingInnerPredictor()

    result = adapter.predict(tmp_path / "clip.webm", "00000000-0000-0000-0000-000000000000")

    assert adapter._predictor.calls == [{"min_duration_ms": 450, "max_duration_ms": 4000}]
    assert (result.classLabel, result.text, result.confidence) == ("CAM_ON_HCM_1", "Cảm ơn", 0.81)
    assert result.timingsMs.extract == 900
    assert result.qualityHints.frameCount == 64


def test_adapter_predict_raises_mapped_error_chained_to_pipeline_error(stub_visign_ai, tmp_path):
    adapter = _adapter_raising("FEATURE_SCHEMA_MISMATCH")

    with pytest.raises(ViSignApiException) as exc_info:
        adapter.predict(tmp_path / "clip.webm", "00000000-0000-0000-0000-000000000000")

    assert exc_info.value.code == ErrorCode.MODEL_NOT_READY
    assert isinstance(exc_info.value.__cause__, _StubPipelineError)


@pytest.mark.parametrize(
    "pipeline_code,expected_status,expected_code",
    [
        ("FEATURE_SCHEMA_MISMATCH", 503, "MODEL_NOT_READY"),
        ("INSUFFICIENT_LANDMARKS", 422, "INSUFFICIENT_LANDMARKS"),
    ],
)
def test_pipeline_errors_reach_the_client_as_contract_errors(
    client: TestClient, monkeypatch, tmp_path, stub_visign_ai, pipeline_code, expected_status, expected_code
):
    monkeypatch.setattr(predictor_registry, "_active_predictor", _adapter_raising(pipeline_code))
    monkeypatch.setattr(settings, "temp_dir", str(tmp_path))

    files = {"clip": ("camera_clip.webm", io.BytesIO(VALID_WEBM_BYTES), "video/webm")}
    response = client.post("/api/v1/predictions", files=files)

    assert response.status_code == expected_status
    data = response.json()
    assert data["code"] == expected_code
    assert data["requestId"] == response.headers["X-Request-ID"]
    assert "internal pipeline detail" not in response.text
    assert list(tmp_path.iterdir()) == []
