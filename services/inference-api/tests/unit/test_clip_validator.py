"""Unit tests for clip MIME, size and magic-byte validation (T049).
Duration limits are enforced by the AI pipeline; see test_gru_predictor.py."""

import pytest

from visign_api.config import settings
from visign_api.domain.errors import ErrorCode, ViSignApiException
from visign_api.inference.clip_validator import (
    EBML_MAGIC_BYTES,
    validate_clip_content,
    validate_clip_metadata,
)


@pytest.mark.parametrize(
    "content_type",
    ["video/webm", "video/webm;codecs=vp8", "video/webm; codecs=vp9,opus", "VIDEO/WEBM"],
)
def test_supported_webm_mime_types_accepted(content_type):
    validate_clip_metadata(content_type=content_type, content_length=1024)


@pytest.mark.parametrize(
    "content_type,content_length,expected_code",
    [
        ("video/mp4", 1024, ErrorCode.UNSUPPORTED_MEDIA_TYPE),
        ("image/png", 1024, ErrorCode.UNSUPPORTED_MEDIA_TYPE),
        ("video/webm", 0, ErrorCode.INVALID_REQUEST),
        ("video/webm", settings.max_clip_size_bytes + 1, ErrorCode.CLIP_TOO_LARGE),
    ],
)
def test_invalid_metadata_rejected(content_type, content_length, expected_code):
    with pytest.raises(ViSignApiException) as exc_info:
        validate_clip_metadata(content_type=content_type, content_length=content_length)
    assert exc_info.value.code == expected_code


def test_content_with_ebml_header_accepted():
    validate_clip_content(EBML_MAGIC_BYTES + b"payload")


@pytest.mark.parametrize(
    "content,expected_code",
    [
        (b"", ErrorCode.INVALID_REQUEST),
        (b"\x1a\x45", ErrorCode.CLIP_DECODE_FAILED),
        (b"RIFF0000WEBP", ErrorCode.CLIP_DECODE_FAILED),
    ],
)
def test_invalid_content_rejected(content, expected_code):
    with pytest.raises(ViSignApiException) as exc_info:
        validate_clip_content(content)
    assert exc_info.value.code == expected_code
