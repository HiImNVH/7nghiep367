"""Opt-in real camera evidence. Paths are local and never added to Git."""

import os
from pathlib import Path

import numpy as np
import pytest
from visign_ai.inference import GRUPredictor
from visign_ai.landmarks.pipeline import process_video
from visign_ai.landmarks.video_decoder import decode_video


@pytest.mark.parametrize("browser", ["CHROME", "EDGE"])
def test_real_browser_webm_timestamps_and_repeatability(browser):
    path = os.environ.get("VISIGN_" + browser + "_WEBM")
    if not path:
        pytest.skip(f"Provide VISIGN_{browser}_WEBM from a real browser recording")
    frames, pts, integer_pts = decode_video(path)
    assert len(frames) > 1
    assert np.all(np.diff(pts) > 0) and np.all(np.diff(integer_pts) > 0)
    first = process_video(path)
    second = process_video(path)
    np.testing.assert_allclose(first["tensor"], second["tensor"], rtol=0, atol=1e-6)


def test_real_training_serving_tensor_parity():
    clip, artifact = (
        os.environ.get("VISIGN_PARITY_CLIP"),
        os.environ.get("VISIGN_PARITY_ARTIFACT"),
    )
    if not clip or not artifact:
        pytest.skip("Requires a real reviewed clip and a trained artifact")
    offline = process_video(clip, schema_path=Path(artifact) / "feature_schema.json")
    serving = GRUPredictor(artifact).clip_to_tensor(clip)
    np.testing.assert_allclose(offline["tensor"], serving["tensor"], rtol=0, atol=1e-6)
