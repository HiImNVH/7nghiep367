"""Unit tests for temporary clip lifecycle and guaranteed cleanup (T025)."""

import pytest
from pathlib import Path
from visign_api.inference.temporary_clip import manage_temporary_clip, TemporaryClip


def test_temporary_clip_created_and_deleted_on_success():
    """Verify clip is created with contents and deleted after clean exit."""
    dummy_data = b"dummy webm test data bytes"
    recorded_path: Path | None = None

    with manage_temporary_clip(dummy_data) as clip:
        assert isinstance(clip, TemporaryClip)
        assert clip.path.exists()
        assert clip.path.read_bytes() == dummy_data
        assert clip.size_bytes == len(dummy_data)
        recorded_path = clip.path

    # Once exited, file must be deleted immediately
    assert recorded_path is not None
    assert not recorded_path.exists()


def test_temporary_clip_deleted_on_exception():
    """Verify clip is deleted even when an exception is raised inside the context."""
    dummy_data = b"exception test data"
    recorded_path: Path | None = None

    with pytest.raises(RuntimeError, match="Simulated inference failure"):
        with manage_temporary_clip(dummy_data) as clip:
            recorded_path = clip.path
            assert recorded_path.exists()
            raise RuntimeError("Simulated inference failure")

    assert recorded_path is not None
    assert not recorded_path.exists()


def test_temporary_clip_idempotent_cleanup():
    """Verify calling cleanup multiple times does not raise errors."""
    dummy_data = b"idempotent cleanup test"

    with manage_temporary_clip(dummy_data) as clip:
        path = clip.path
        assert path.exists()
        # Manually cleanup once
        clip.cleanup()
        assert not path.exists()
        # Cleanup again should be safe
        clip.cleanup()

    assert not path.exists()
