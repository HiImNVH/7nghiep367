"""Video clip validation for MIME, size, WebM magic bytes, and container integrity (T049)."""

from pathlib import Path
from typing import Optional
from visign_api.config import settings
from visign_api.domain.errors import (
    ClipDecodeFailedException,
    ClipTooLargeException,
    ClipTooLongException,
    ClipTooShortException,
    InvalidRequestException,
    UnsupportedMediaTypeException,
)

EBML_MAGIC_BYTES = b"\x1a\x45\xdf\xa3"


def validate_clip_metadata(
    content_type: Optional[str],
    content_length: Optional[int],
) -> None:
    """Validate HTTP headers prior to full body parsing when available."""
    if content_type:
        clean_content_type = content_type.split(";")[0].strip().lower()
        allowed_bases = [m.split(";")[0].strip().lower() for m in settings.allowed_mime_types]
        if clean_content_type not in allowed_bases:
            raise UnsupportedMediaTypeException(
                f"Định dạng '{content_type}' không được hỗ trợ. Vui lòng gửi video WebM."
            )

    if content_length is not None:
        if content_length <= 0:
            raise InvalidRequestException("Tệp video rỗng hoặc không có dữ liệu.")
        if content_length > settings.max_clip_size_bytes:
            raise ClipTooLargeException(
                f"Dung lượng video ({content_length} bytes) vượt quá giới hạn tối đa {settings.max_clip_size_bytes} bytes."
            )


def validate_clip_content(content: bytes) -> None:
    """Validate byte size and container magic bytes directly from binary content."""
    size = len(content)
    if size == 0:
        raise InvalidRequestException("Tệp video rỗng hoặc không có dữ liệu.")

    if size > settings.max_clip_size_bytes:
        raise ClipTooLargeException(
            f"Dung lượng video ({size} bytes) vượt quá giới hạn tối đa {settings.max_clip_size_bytes} bytes."
        )

    # Validate WebM EBML magic header
    if size < 4 or not content.startswith(EBML_MAGIC_BYTES):
        raise ClipDecodeFailedException(
            "Không thể giải mã video. Tệp không chứa WebM EBML header hợp lệ."
        )


def validate_clip_duration(duration_ms: int) -> None:
    """
    Validate clip duration measured from decoded frame PTS, never from client/container metadata.
    Called by the pilot/full predictor right after the VideoDecoder step (T015).
    """
    if duration_ms < settings.min_duration_ms:
        raise ClipTooShortException()
    if duration_ms > settings.max_duration_ms:
        raise ClipTooLongException()


def validate_clip_file(file_path: Path) -> None:
    """Validate disk file size and magic bytes."""
    if not file_path.exists():
        raise InvalidRequestException("Tệp video không tồn tại trên hệ thống.")

    size = file_path.stat().st_size
    if size == 0:
        raise InvalidRequestException("Tệp video rỗng.")

    if size > settings.max_clip_size_bytes:
        raise ClipTooLargeException(
            f"Dung lượng video ({size} bytes) vượt quá giới hạn cho phép."
        )

    with open(file_path, "rb") as f:
        header = f.read(4)
        if len(header) < 4 or header != EBML_MAGIC_BYTES:
            raise ClipDecodeFailedException("Không thể giải mã video. Thiếu WebM magic bytes.")
