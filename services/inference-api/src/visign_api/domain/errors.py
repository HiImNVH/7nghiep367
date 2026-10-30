"""Error catalog and standardized ErrorEnvelope schema (T021)."""

from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class ErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    CLIP_TOO_LARGE = "CLIP_TOO_LARGE"
    CLIP_TOO_SHORT = "CLIP_TOO_SHORT"
    CLIP_TOO_LONG = "CLIP_TOO_LONG"
    NO_PERSON_DETECTED = "NO_PERSON_DETECTED"
    INSUFFICIENT_LANDMARKS = "INSUFFICIENT_LANDMARKS"
    CLIP_DECODE_FAILED = "CLIP_DECODE_FAILED"
    SERVICE_BUSY = "SERVICE_BUSY"
    MODEL_NOT_READY = "MODEL_NOT_READY"
    PREDICTION_FAILED = "PREDICTION_FAILED"


class ErrorEnvelope(BaseModel):
    """Schema matching contracts/openapi.yaml #/components/schemas/ErrorEnvelope."""

    code: ErrorCode = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    requestId: str = Field(..., description="UUID correlation ID")

    @model_validator(mode="after")
    def validate_request_id_uuid(self) -> "ErrorEnvelope":
        try:
            UUID(self.requestId)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid requestId UUID format: {self.requestId}")
        return self


class ViSignApiException(Exception):
    """Base exception for all ViSign domain and HTTP exceptions."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after


class InvalidRequestException(ViSignApiException):
    def __init__(self, message: str = "Yêu cầu không hợp lệ hoặc thiếu dữ liệu video."):
        super().__init__(ErrorCode.INVALID_REQUEST, message, status_code=400)


class UnsupportedMediaTypeException(ViSignApiException):
    def __init__(self, message: str = "Định dạng video không được hỗ trợ. Vui lòng gửi video WebM."):
        super().__init__(ErrorCode.UNSUPPORTED_MEDIA_TYPE, message, status_code=415)


class ClipTooLargeException(ViSignApiException):
    def __init__(self, message: str = "Dung lượng video vượt quá giới hạn cho phép."):
        super().__init__(ErrorCode.CLIP_TOO_LARGE, message, status_code=413)


class ClipTooShortException(ViSignApiException):
    def __init__(self, message: str = "Đoạn video quá ngắn để nhận diện ký hiệu."):
        super().__init__(ErrorCode.CLIP_TOO_SHORT, message, status_code=422)


class ClipTooLongException(ViSignApiException):
    def __init__(self, message: str = "Đoạn video quá dài so với giới hạn của ký hiệu đơn lẻ."):
        super().__init__(ErrorCode.CLIP_TOO_LONG, message, status_code=422)


class NoPersonDetectedException(ViSignApiException):
    def __init__(self, message: str = "Không phát hiện người trong khung hình camera."):
        super().__init__(ErrorCode.NO_PERSON_DETECTED, message, status_code=422)


class InsufficientLandmarksException(ViSignApiException):
    def __init__(self, message: str = "Không phát hiện đủ các điểm khớp bàn tay/cơ thể để nhận diện."):
        super().__init__(ErrorCode.INSUFFICIENT_LANDMARKS, message, status_code=422)


class ClipDecodeFailedException(ViSignApiException):
    def __init__(self, message: str = "Không thể giải mã video. Tệp có thể bị hỏng hoặc thiếu timestamp."):
        super().__init__(ErrorCode.CLIP_DECODE_FAILED, message, status_code=422)


class ServiceBusyException(ViSignApiException):
    def __init__(self, retry_after: int = 3, message: str = "Hệ thống đang bận xử lý yêu cầu khác. Vui lòng thử lại sau."):
        super().__init__(ErrorCode.SERVICE_BUSY, message, status_code=503, retry_after=retry_after)


class ModelNotReadyException(ViSignApiException):
    def __init__(self, retry_after: int = 5, message: str = "Mô hình nhận diện chưa sẵn sàng."):
        super().__init__(ErrorCode.MODEL_NOT_READY, message, status_code=503, retry_after=retry_after)


class PredictionFailedException(ViSignApiException):
    def __init__(self, message: str = "Xử lý nhận diện thất bại do lỗi không xác định."):
        super().__init__(ErrorCode.PREDICTION_FAILED, message, status_code=500)
