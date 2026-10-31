"""System endpoints: health check and model-info (T060)."""

from typing import Literal, Optional
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from visign_api.domain.model_version import ModelInfoResponse
from visign_api.inference.predictor import predictor_registry

system_router = APIRouter(tags=["System"])


class HealthResponse(BaseModel):
    """Health check response matching contracts/openapi.yaml."""

    status: Literal["ok", "degraded"] = Field(..., description="'ok' or 'degraded'")
    modelReady: bool = Field(..., description="True if any model artifact is loaded")
    modelVersion: Optional[str] = Field(None, description="Active model version")


@system_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service and model readiness",
)
async def get_health(request: Request, response: Response) -> HealthResponse:
    request_id = getattr(request.state, "request_id", "")
    if request_id:
        response.headers["X-Request-ID"] = request_id

    is_ready = predictor_registry.is_ready
    model_version = (
        predictor_registry.active_predictor.metadata.modelVersion
        if is_ready
        else None
    )

    return HealthResponse(
        status="ok" if is_ready else "degraded",
        modelReady=is_ready,
        modelVersion=model_version,
    )


@system_router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    summary="Read active model metadata",
)
async def get_model_info(request: Request, response: Response) -> ModelInfoResponse:
    request_id = getattr(request.state, "request_id", "")
    if request_id:
        response.headers["X-Request-ID"] = request_id

    # If predictor is not loaded, this will raise ModelNotReadyException (503)
    predictor = predictor_registry.active_predictor
    return ModelInfoResponse.from_metadata(predictor.metadata)
