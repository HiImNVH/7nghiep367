"""FastAPI application entrypoint, middleware, exception mapping, and lifespan (T026)."""

import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from visign_api.api.router import api_v1_router
from visign_api.config import settings
from visign_api.domain.errors import (
    ErrorCode,
    ErrorEnvelope,
    InvalidRequestException,
    PredictionFailedException,
    ViSignApiException,
)
from visign_api.inference.predictor import predictor_registry
from visign_api.observability import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing initial model loading."""
    logger.info("Initializing ViSign Inference API...")
    try:
        predictor_registry.load_artifact(settings.model_artifact_path)
    except Exception as e:
        logger.warning(
            f"Could not load initial artifact from '{settings.model_artifact_path}': {e}. "
            "Service starting in degraded mode."
        )
    yield
    logger.info("Shutting down ViSign Inference API...")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="FastAPI inference service for isolated Vietnamese Sign Language MVP",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
    expose_headers=["X-Request-ID", "Retry-After"],
)


@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next):
    """
    Middleware to receive or generate X-Request-ID UUID, inject it into request.state,
    and guarantee it is echoed in response headers.
    """
    raw_req_id = request.headers.get("X-Request-ID")
    effective_req_id: str

    if raw_req_id:
        try:
            effective_req_id = str(uuid.UUID(raw_req_id))
        except (ValueError, TypeError):
            effective_req_id = str(uuid.uuid4())
    else:
        effective_req_id = str(uuid.uuid4())

    request.state.request_id = effective_req_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = effective_req_id
    return response


# --- Exception Handlers ---


@app.exception_handler(ViSignApiException)
async def visign_api_exception_handler(request: Request, exc: ViSignApiException):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    headers = {"X-Request-ID": req_id}
    if exc.retry_after is not None:
        headers["Retry-After"] = str(exc.retry_after)

    envelope = ErrorEnvelope(
        code=exc.code,
        message=exc.message,
        requestId=req_id,
    )

    logger.warning(
        f"API handled exception [{exc.code.value}]: {exc.message}",
        extra={
            "requestId": req_id,
            "errorCode": exc.code.value,
            "statusCode": exc.status_code,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=envelope.model_dump(),
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    headers = {"X-Request-ID": req_id}

    envelope = ErrorEnvelope(
        code=ErrorCode.INVALID_REQUEST,
        message="Dữ liệu yêu cầu không đúng định dạng hoặc thiếu trường bắt buộc.",
        requestId=req_id,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=envelope.model_dump(),
        headers=headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    headers = {"X-Request-ID": req_id}

    logger.error(
        f"Unhandled server error: {exc}",
        extra={
            "requestId": req_id,
            "errorCode": ErrorCode.PREDICTION_FAILED.value,
            "statusCode": 500,
        },
        exc_info=True,
    )

    envelope = ErrorEnvelope(
        code=ErrorCode.PREDICTION_FAILED,
        message="Hệ thống gặp sự cố không mong muốn trong quá trình xử lý.",
        requestId=req_id,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=envelope.model_dump(),
        headers=headers,
    )


app.include_router(api_v1_router)
