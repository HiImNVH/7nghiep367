"""Temporary clip lifecycle management with guaranteed deletion (T024)."""

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
from visign_api.config import settings
from visign_api.observability import logger


class TemporaryClip:
    """Encapsulates a temporary video clip on disk with guaranteed cleanup."""

    def __init__(self, file_path: Path):
        self.path = file_path

    @property
    def size_bytes(self) -> int:
        if self.path.exists():
            return self.path.stat().st_size
        return 0

    def cleanup(self) -> None:
        """Explicitly remove the temporary file if it exists."""
        try:
            if self.path.exists():
                self.path.unlink()
                logger.debug(f"Temporary clip deleted: {self.path.name}")
        except Exception as e:
            logger.warning(f"Failed to delete temporary clip {self.path}: {e}")


@contextmanager
def manage_temporary_clip(
    content: bytes,
    suffix: str = ".webm",
    temp_dir: Optional[str] = None,
) -> Generator[TemporaryClip, None, None]:
    """
    Context manager to safely create and guarantee immediate deletion of uploaded camera clips.
    Guarantees deletion in both success and exception paths.
    """
    target_dir = temp_dir or settings.temp_dir or None
    if target_dir:
        Path(target_dir).mkdir(parents=True, exist_ok=True)

    fd, raw_path = tempfile.mkstemp(prefix="visign_clip_", suffix=suffix, dir=target_dir)
    file_path = Path(raw_path)
    clip = TemporaryClip(file_path)

    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        yield clip
    finally:
        clip.cleanup()
