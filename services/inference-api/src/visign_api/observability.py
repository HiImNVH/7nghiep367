"""Privacy-safe structured logging and observability (T023)."""

import json
import logging
import sys
from typing import Any, Dict, Optional


class StructuredJsonFormatter(logging.Formatter):
    """
    JSON log formatter strictly preserving privacy:
    - Never logs video binary, frames, or landmarks.
    - Captures request_id, model_version, stage_timings, accepted_status, and error_code.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Safely include structured context from extra kwargs
        for key in (
            "requestId",
            "modelVersion",
            "processingTimeMs",
            "timingsMs",
            "accepted",
            "errorCode",
            "classLabel",
            "confidence",
            "path",
            "method",
            "statusCode",
        ):
            if hasattr(record, key):
                log_obj[key] = getattr(record, key)

        # Stack traces only carry code locations and exception messages, never request payloads
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # ASCII escapes keep Vietnamese messages from being dropped when Windows stdout
        # is redirected with a legacy code page; JSON readers decode them transparently.
        return json.dumps(log_obj, ensure_ascii=True)


def setup_logger(name: str = "visign_api") -> logging.Logger:
    """Setup and configure a privacy-safe structured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logger()
