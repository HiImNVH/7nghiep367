"""Deterministic sampling over the entire PTS span before landmark extraction."""

import numpy as np

from .errors import PipelineError


def select_frame_indices(timestamps, schema):
    timestamps = np.asarray(timestamps, dtype=np.float64)
    if (
        timestamps.ndim != 1
        or not len(timestamps)
        or not np.isfinite(timestamps).all()
        or np.any(np.diff(timestamps) <= 0)
    ):
        raise PipelineError("INVALID_TIMESTAMPS", "Expected finite, increasing PTS")
    policy = schema.get("preExtractionSampling")
    if policy is None:
        return np.arange(len(timestamps))
    count = policy.get("maxFrames")
    if (
        policy.get("method") != "uniform-pts-nearest"
        or type(count) is not int
        or count < 2
    ):
        raise PipelineError(
            "FEATURE_SCHEMA_MISMATCH", "Unsupported pre-extraction sampling policy"
        )
    if len(timestamps) <= count:
        return np.arange(len(timestamps))
    targets = np.linspace(timestamps[0], timestamps[-1], count)
    right = np.searchsorted(timestamps, targets).clip(0, len(timestamps) - 1)
    left = np.maximum(right - 1, 0)
    # Prefer the earlier source frame for equal distances. Include both clip endpoints.
    choose_left = targets - timestamps[left] <= timestamps[right] - targets
    return np.unique(np.where(choose_left, left, right))
