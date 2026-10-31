import numpy as np
import pytest
from visign_ai.landmarks import pipeline


@pytest.mark.parametrize(
    "span,limits,code",
    [
        (100, {"min_duration_ms": 300}, "CLIP_TOO_SHORT"),
        (7000, {"max_duration_ms": 6000}, "CLIP_TOO_LONG"),
    ],
)
def test_invalid_duration_rejected_before_detector_initialization(
    monkeypatch, span, limits, code
):
    schema = pipeline.load_schema()
    monkeypatch.setattr(
        pipeline,
        "extractor_identity",
        lambda *args: {"version": schema["extractorVersion"]},
    )
    frames = [np.zeros((4, 4, 3), np.uint8)] * 2
    stamps = np.array([0, span])
    monkeypatch.setattr(
        pipeline.VideoDecoder, "decode", lambda *args: (frames, stamps, stamps)
    )
    monkeypatch.setattr(
        pipeline, "extract", lambda *args: pytest.fail("Detector must not run")
    )
    with pytest.raises(pipeline.PipelineError) as error:
        pipeline.process_video("unused.webm", **limits)
    assert error.value.code == code
