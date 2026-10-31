"""Measure real clip preprocessing and inference on the target laptop."""

import argparse
import platform
import time
from pathlib import Path

import numpy as np
import torch

from visign_ai.inference import GRUPredictor
from visign_ai.io import new_output, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--clips", nargs="+", required=True)
    parser.add_argument("--model-dir")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.repeats < 1:
        raise ValueError("repeats must be positive")
    start = time.perf_counter()
    predictor = GRUPredictor(args.artifact, args.model_dir)
    load_ms = (time.perf_counter() - start) * 1000
    times = []
    for _ in range(args.repeats):
        for clip in args.clips:
            start = time.perf_counter()
            predictor.predict(Path(clip))
            times.append((time.perf_counter() - start) * 1000)
    with new_output(args.output) as output:
        write_json(
            output / "benchmark.json",
            {
                "scope": "local clip decode + detector initialization + extraction + GRU; excludes HTTP/UI",
                "platform": platform.platform(),
                "processor": platform.processor(),
                "torchVersion": str(torch.__version__),
                "device": "cpu",
                "modelVersion": predictor.metadata["modelVersion"],
                "featureSchemaVersion": predictor.metadata["featureSchemaVersion"],
                "extractorVersion": predictor.metadata["extractorVersion"],
                "modelLoadMs": load_ms,
                "sampleCount": len(times),
                "p50Ms": float(np.percentile(times, 50)),
                "p95Ms": float(np.percentile(times, 95)),
                "withinThreeSecondsRatio": float(np.mean(np.array(times) <= 3000)),
                "durationsMs": times,
            },
        )


if __name__ == "__main__":
    main()
