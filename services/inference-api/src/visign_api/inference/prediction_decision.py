"""Pure confidence decision rule for accepted vs rejected states (T048)."""

from dataclasses import dataclass
from typing import Optional

FALLBACK_REJECTED_TEXT = "Không nhận diện được"


@dataclass(frozen=True)
class DecisionResult:
    accepted: bool
    text: str
    classLabel: Optional[str]
    confidence: float


def decide_prediction(
    confidence: float,
    threshold: float,
    predicted_class: Optional[str],
    predicted_text: Optional[str],
) -> DecisionResult:
    """
    Pure decision rule according to constitution and spec:
    - If confidence >= threshold and predicted_class is present:
        accepted = True, text = predicted_text, classLabel = predicted_class
    - Otherwise (low confidence or missing class):
        accepted = False, text = 'Không nhận diện được', classLabel = None
    """
    if confidence >= threshold and predicted_class and predicted_text:
        return DecisionResult(
            accepted=True,
            text=predicted_text,
            classLabel=predicted_class,
            confidence=confidence,
        )

    return DecisionResult(
        accepted=False,
        text=FALLBACK_REJECTED_TEXT,
        classLabel=None,
        confidence=confidence,
    )
