"""Predictions controller: clip upload, bounded coordinator, and inference pipeline (T038, T050)."""

import asyncio
import time
from typing import Optional
from fastapi import APIRouter, File, Request, Response, UploadFile
from starlette.concurrency import run_in_threadpool

from visign_api.config import settings
from visign_api.domain.errors import (
    ErrorCode,
    InvalidRequestException,
    PredictionFailedException,
    ServiceBusyException,
    ViSignApiException,
)
from visign_api.domain.prediction import PredictionResponse
from visign_api.inference.clip_validator import validate_clip_content, validate_clip_metadata
from visign_api.inference.prediction_decision import decide_prediction
from visign_api.inference.predictor import predictor_registry
from visign_api.inference.temporary_clip import manage_temporary_clip
from visign_api.observability import logger

predictions_router = APIRouter(tags=["Predictions"])


class InferenceCoordinator:
    """Bounded coordinator limiting concurrent inferences to 1 with bounded wait timeout."""

    def __init__(self, max_concurrent: int = 1, timeout_seconds: float = 3.0, retry_after: int = 3):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout_seconds = timeout_seconds
        self.retry_after = retry_after

    async def acquire_slot(self):
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self.timeout_seconds)
        except (asyncio.TimeoutError, TimeoutError):
            raise ServiceBusyException(retry_after=self.retry_after)

    def release_slot(self):
        self._semaphore.release()


inference_coordinator = InferenceCoordinator(
    max_concurrent=1,
    timeout_seconds=settings.inference_timeout_seconds,
    retry_after=settings.busy_retry_after_seconds,
)


@predictions_router.post(
    "/predictions",
    response_model=PredictionResponse,
    summary="Classify one isolated sign captured from the camera",
)
async def create_prediction(
    request: Request,
    response: Response,
    clip: Optional[UploadFile] = File(None, description="Camera clip WebM recording"),
) -> PredictionResponse:
    start_time = time.perf_counter()
    request_id = getattr(request.state, "request_id", "")
    if request_id:
        response.headers["X-Request-ID"] = request_id

    # Validate file presence
    if clip is None:
        raise InvalidRequestException("Yêu cầu thiếu tệp video (multipart field 'clip' is required).")

    # Validate Content-Type
    validate_clip_metadata(
        content_type=clip.content_type,
        content_length=clip.size,
    )

    # Read binary bytes
    content = await clip.read()
    validate_clip_content(content)

    # Predictor must be ready
    predictor = predictor_registry.active_predictor

    # Bounded execution coordinator
    coordinator = inference_coordinator
    await coordinator.acquire_slot()

    try:
        with manage_temporary_clip(content) as temp_clip:
            # CPU-bound decode/extract/infer runs off the event loop so health checks and
            # SERVICE_BUSY timeouts keep working; the slot is held until the thread finishes.
            try:
                raw_result = await run_in_threadpool(predictor.predict, temp_clip.path, request_id)
            except ViSignApiException:
                raise
            except Exception as exc:
                logger.error(
                    "Predictor raised an unexpected error",
                    extra={
                        "requestId": request_id,
                        "modelVersion": predictor.metadata.modelVersion,
                        "errorCode": ErrorCode.PREDICTION_FAILED.value,
                    },
                    exc_info=True,
                )
                raise PredictionFailedException() from exc
    finally:
        coordinator.release_slot()
        await clip.close()

    decision = decide_prediction(
        confidence=raw_result.confidence,
        threshold=predictor.metadata.acceptanceThreshold,
        predicted_class=raw_result.classLabel,
        predicted_text=raw_result.text,
    )

    total_duration_ms = int((time.perf_counter() - start_time) * 1000)

    # Assemble response
    pred_response = PredictionResponse(
        requestId=request_id,
        text=decision.text,
        classLabel=decision.classLabel,
        confidence=decision.confidence,
        accepted=decision.accepted,
        modelVersion=predictor.metadata.modelVersion,
        processingTimeMs=max(0, total_duration_ms),
        timingsMs=raw_result.timingsMs,
        qualityHints=raw_result.qualityHints,
    )

    logger.info(
        "Prediction completed successfully",
        extra={
            "requestId": request_id,
            "modelVersion": predictor.metadata.modelVersion,
            "processingTimeMs": total_duration_ms,
            "timingsMs": raw_result.timingsMs.model_dump() if raw_result.timingsMs else None,
            "accepted": decision.accepted,
            "classLabel": decision.classLabel,
            "confidence": decision.confidence,
        },
    )
    return pred_response
