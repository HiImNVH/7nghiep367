import numpy as np
import pytest
from visign_ai.landmarks.errors import PipelineError
from visign_ai.landmarks.temporal_sampling import select_frame_indices


def policy(count):
    return {
        "preExtractionSampling": {"method": "uniform-pts-nearest", "maxFrames": count}
    }


def test_sampling_covers_full_clip_without_inventing_frames():
    timestamps = np.arange(121) * (1000 / 30)
    indices = select_frame_indices(timestamps, policy(64))
    assert len(indices) == 64
    assert indices[0] == 0 and indices[-1] == 120
    assert np.all(np.diff(indices) > 0)
    np.testing.assert_array_equal(indices, select_frame_indices(timestamps, policy(64)))


def test_sampling_uses_time_instead_of_frame_number_for_variable_fps():
    timestamps = np.array([0, 1, 2, 3, 500, 1000], dtype=float)
    np.testing.assert_array_equal(
        select_frame_indices(timestamps, policy(3)), [0, 4, 5]
    )


@pytest.mark.parametrize("length", [1, 2, 16, 32, 64])
def test_short_clips_keep_every_source_frame(length):
    timestamps = np.arange(length) * 100
    np.testing.assert_array_equal(
        select_frame_indices(timestamps, policy(64)), np.arange(length)
    )


def test_legacy_schema_preserves_all_source_frames():
    np.testing.assert_array_equal(
        select_frame_indices(np.arange(121), {}), np.arange(121)
    )


@pytest.mark.parametrize("timestamps", [[], [0, 0], [1, 0], [0, np.nan], [0, np.inf]])
def test_invalid_timestamps_fail_closed(timestamps):
    with pytest.raises(PipelineError) as error:
        select_frame_indices(timestamps, policy(64))
    assert error.value.code == "INVALID_TIMESTAMPS"


@pytest.mark.parametrize("count", [True, 0, 1, -3, 3.5, "64"])
def test_invalid_frame_budget_is_rejected(count):
    with pytest.raises(PipelineError) as error:
        select_frame_indices([0, 100, 200], policy(count))
    assert error.value.code == "FEATURE_SCHEMA_MISMATCH"


def test_sampling_does_not_duplicate_frames_across_long_timestamp_gaps():
    indices = select_frame_indices([0, 1, 2, 10000, 10001], policy(4))
    assert len(indices) == len(set(indices)) <= 4
    assert indices[0] == 0 and indices[-1] == 4
