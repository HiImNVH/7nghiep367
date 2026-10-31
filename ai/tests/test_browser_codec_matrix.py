import json
import os
from pathlib import Path

import numpy as np
import pytest
from visign_ai.landmarks.video_decoder import VideoDecoder


@pytest.mark.parametrize("browser", ["chrome", "msedge"])
@pytest.mark.parametrize("codec", ["vp8", "vp9"])
def test_real_browser_codec_decode(browser, codec):
    root = os.environ.get("VISIGN_BROWSER_FIXTURES")
    if not root:
        pytest.skip("Run record_browser_fixtures.mjs and set VISIGN_BROWSER_FIXTURES")
    root = Path(root)
    evidence = json.loads((root / "browser-versions.json").read_text("utf-8"))
    assert any(
        item["browser"] == browser and item["codec"] == codec for item in evidence
    )
    frames, pts, milliseconds = VideoDecoder().decode(root / f"{browser}-{codec}.webm")
    assert len(frames) > 10
    assert np.all(np.diff(pts) > 0) and np.all(np.diff(milliseconds) > 0)
    assert 2000 <= pts[-1] <= 3500
