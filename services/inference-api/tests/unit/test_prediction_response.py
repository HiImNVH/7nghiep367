"""Unit tests proving accepted/rejected prediction states cannot be combined incorrectly (T020)."""

import json
import uuid

import pytest
from pydantic import ValidationError

from visign_api.domain.prediction import PredictionResponse
from visign_api.inference.prediction_decision import FALLBACK_REJECTED_TEXT


def _response(**overrides) -> PredictionResponse:
    fields = dict(
        requestId=str(uuid.uuid4()),
        text="Xin chào",
        classLabel="XIN_CHAO_HCM_1",
        confidence=0.9,
        accepted=True,
        modelVersion="vsl-fixture-v0.1.0",
        processingTimeMs=10,
    )
    fields.update(overrides)
    return PredictionResponse(**fields)


def test_valid_accepted_response():
    response = _response()
    assert response.accepted is True
    assert response.timingsMs is None
    assert response.qualityHints is None


def test_valid_rejected_response():
    response = _response(accepted=False, text=FALLBACK_REJECTED_TEXT, classLabel=None, confidence=0.3)
    assert response.classLabel is None


def test_absent_diagnostics_are_omitted_but_null_class_label_is_kept():
    """openapi.yaml: timingsMs/qualityHints are optional (not nullable); classLabel is required nullable."""
    response = _response(accepted=False, text=FALLBACK_REJECTED_TEXT, classLabel=None, confidence=0.3)

    data = json.loads(response.model_dump_json())

    assert "timingsMs" not in data
    assert "qualityHints" not in data
    assert data["classLabel"] is None


def test_present_diagnostics_are_serialized():
    response = _response(
        timingsMs={"decode": 1, "extract": 2, "infer": 3},
        qualityHints={"handsDetectedRatio": 0.5, "frameCount": 10},
    )

    data = response.model_dump(mode="json")

    assert data["timingsMs"] == {"decode": 1, "extract": 2, "infer": 3}
    assert data["qualityHints"] == {"handsDetectedRatio": 0.5, "frameCount": 10}


@pytest.mark.parametrize(
    "overrides",
    [
        {"requestId": "not-a-uuid"},
        {"text": "   "},
        {"classLabel": None},
        {"accepted": False, "text": FALLBACK_REJECTED_TEXT, "classLabel": "XIN_CHAO_HCM_1"},
        {"confidence": 1.2},
        {"processingTimeMs": -1},
        {"timingsMs": {"decode": -1, "extract": 0, "infer": 0}},
        {"qualityHints": {"handsDetectedRatio": 1.5, "frameCount": 10}},
        {"qualityHints": {"handsDetectedRatio": 0.5, "frameCount": 0}},
    ],
)
def test_invalid_state_combinations_rejected(overrides):
    with pytest.raises(ValidationError):
        _response(**overrides)
