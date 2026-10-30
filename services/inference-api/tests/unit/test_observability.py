"""Unit tests for the privacy-safe structured JSON log formatter (T023)."""

import json
import logging
import sys

from visign_api.observability import StructuredJsonFormatter


def _record(message: str, exc_info=None, **extra) -> logging.LogRecord:
    record = logging.LogRecord("visign_api", logging.WARNING, __file__, 1, message, None, exc_info)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_vietnamese_messages_are_ascii_safe_for_windows_consoles():
    """Redirected stdout on Windows uses cp1252; logs with Vietnamese text must not be dropped."""
    message = "Không thể giải mã video. Định dạng không được hỗ trợ."

    output = StructuredJsonFormatter().format(_record(message, errorCode="CLIP_DECODE_FAILED"))

    output.encode("cp1252")  # must not raise UnicodeEncodeError
    assert json.loads(output)["message"] == message


def test_only_whitelisted_extra_keys_are_emitted():
    output = StructuredJsonFormatter().format(
        _record("done", requestId="abc", frames=[1, 2, 3], videoBytes=b"secret")
    )

    data = json.loads(output)
    assert data["requestId"] == "abc"
    assert "frames" not in data
    assert "videoBytes" not in data


def test_exception_trace_is_included():
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        output = StructuredJsonFormatter().format(_record("failed", exc_info=sys.exc_info()))

    assert "RuntimeError: boom" in json.loads(output)["exception"]
