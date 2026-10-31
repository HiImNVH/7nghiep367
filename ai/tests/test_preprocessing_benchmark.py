import json
import sys

import numpy as np
from visign_ai.evaluation import benchmark_preprocessing


def test_preprocessing_benchmark_reports_its_scope_and_is_reproducible(
    tmp_path, monkeypatch
):
    clip = tmp_path / "synthetic.webm"
    clip.write_bytes(b"synthetic-input-for-test-only")
    output = tmp_path / "report"
    monkeypatch.setattr(
        sys,
        "argv",
        ["benchmark", "--clips", str(clip), "--repeats", "2", "--output", str(output)],
    )
    report = {
        "ptsSpanMs": 4000,
        "featureSchemaVersion": "test-only",
        "decodedFrameCount": 121,
        "frameCount": 64,
        "inputStatus": "HAS_USABLE_FRAMES",
        "detectionRatios": {},
        "usableTensorFrameRatio": 1.0,
        "cpuRuntime": {"mode": "system-default", "applied": False},
        "timingsMs": {},
    }
    monkeypatch.setattr(
        benchmark_preprocessing,
        "process_video",
        lambda *args, **kwargs: {"tensor": np.ones((32, 234)), "report": report},
    )
    benchmark_preprocessing.main()
    value = json.loads((output / "benchmark.json").read_text("utf-8"))
    assert value["measurementCount"] == 2
    assert "excludes GRU, HTTP and UI" in value["scope"]
    assert all(record["tensorMaxAbsDiffAcrossRuns"] == 0 for record in value["runs"])
