"""Domain models for prediction requests, responses, timings, and quality hints (T020)."""

from typing import Optional
from uuid import UUID
from pydantic import (
    BaseModel,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)


class PredictionTimings(BaseModel):
    """Optional diagnostic timings measured by the server in milliseconds."""

    decode: int = Field(..., ge=0, description="WebM decode time in ms")
    extract: int = Field(..., ge=0, description="MediaPipe landmark extraction time in ms")
    infer: int = Field(..., ge=0, description="Model inference forward pass time in ms")


class PredictionQualityHints(BaseModel):
    """Optional non-biometric input quality hints. Does not contain raw frames or landmarks."""

    handsDetectedRatio: float = Field(..., ge=0.0, le=1.0, description="Ratio of frames with hands detected")
    frameCount: int = Field(..., ge=1, description="Total video frames decoded")


class PredictionResponse(BaseModel):
    """
    Response schema matching contracts/openapi.yaml #/components/schemas/PredictionResponse.
    States are strictly constrained:
    - When accepted=True: text must not be empty, classLabel must be provided.
    - When accepted=False: text represents unrecognized fallback (e.g. 'Không nhận diện được').
    """

    requestId: str = Field(..., description="UUID correlation ID echoing request header")
    text: str = Field(..., description="Vietnamese text prediction or fallback message")
    classLabel: Optional[str] = Field(..., description="Recognized class label; null when rejected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    accepted: bool = Field(..., description="True if confidence >= threshold and clip was valid")
    modelVersion: str = Field(..., description="Version of the model that performed inference")
    processingTimeMs: int = Field(..., ge=0, description="Total server-side processing time in ms")
    timingsMs: Optional[PredictionTimings] = Field(None, description="Optional diagnostic timings")
    qualityHints: Optional[PredictionQualityHints] = Field(None, description="Optional input quality indicators")

    @model_validator(mode="after")
    def validate_state_consistency(self) -> "PredictionResponse":
        # Validate requestId is a valid UUID string
        try:
            UUID(self.requestId)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid requestId UUID format: {self.requestId}")

        if self.accepted:
            if not self.text.strip():
                raise ValueError("Accepted prediction must contain non-empty Vietnamese text")
            if not self.classLabel:
                raise ValueError("Accepted prediction must contain a non-empty classLabel")
        elif self.classLabel is not None:
            raise ValueError("Rejected prediction must have classLabel = null")

        return self

    @model_serializer(mode="wrap")
    def omit_absent_diagnostics(self, handler: SerializerFunctionWrapHandler):
        """Diagnostics are optional but not nullable in openapi.yaml: omit them instead of sending null.
        No return annotation on purpose: it keeps the documented OpenAPI schema for this model."""
        data = handler(self)
        for key in ("timingsMs", "qualityHints"):
            if data.get(key) is None:
                data.pop(key, None)
        return data
