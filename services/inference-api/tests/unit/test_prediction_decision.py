"""Unit tests for confidence decision boundaries and accepted/rejected mapping (T044)."""

import pytest
from visign_api.inference.prediction_decision import decide_prediction, FALLBACK_REJECTED_TEXT


def test_confidence_above_threshold_accepted():
    result = decide_prediction(
        confidence=0.85,
        threshold=0.70,
        predicted_class="XIN_CHAO_HCM_1",
        predicted_text="Xin chào",
    )
    assert result.accepted is True
    assert result.classLabel == "XIN_CHAO_HCM_1"
    assert result.text == "Xin chào"
    assert result.confidence == 0.85


def test_confidence_exactly_at_threshold_accepted():
    result = decide_prediction(
        confidence=0.70,
        threshold=0.70,
        predicted_class="CAM_ON_HCM_1",
        predicted_text="Cảm ơn",
    )
    assert result.accepted is True
    assert result.classLabel == "CAM_ON_HCM_1"
    assert result.text == "Cảm ơn"


def test_confidence_below_threshold_rejected():
    result = decide_prediction(
        confidence=0.699,
        threshold=0.70,
        predicted_class="CAM_ON_HCM_1",
        predicted_text="Cảm ơn",
    )
    assert result.accepted is False
    assert result.classLabel is None
    assert result.text == FALLBACK_REJECTED_TEXT
    assert result.confidence == 0.699


def test_zero_confidence_rejected():
    result = decide_prediction(
        confidence=0.0,
        threshold=0.70,
        predicted_class="XIN_CHAO_HCM_1",
        predicted_text="Xin chào",
    )
    assert result.accepted is False
    assert result.classLabel is None
    assert result.text == FALLBACK_REJECTED_TEXT


def test_missing_predicted_class_rejected_even_with_high_confidence():
    result = decide_prediction(
        confidence=0.99,
        threshold=0.70,
        predicted_class=None,
        predicted_text="Xin chào",
    )
    assert result.accepted is False
    assert result.classLabel is None
    assert result.text == FALLBACK_REJECTED_TEXT
