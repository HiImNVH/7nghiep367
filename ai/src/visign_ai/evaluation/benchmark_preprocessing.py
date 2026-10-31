"""Measure preprocessing independently while the reviewed GRU artifact is pending."""

import argparse
import hashlib
import platform
import time
from pathlib import Path

import numpy as np

from visign_ai.io import new_output, write_json
from visign_ai.landmarks.pipeline import process_video


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clips", nargs="+", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", required=True)
    parser.add_argument("--schema")
    parser.add_argument("--model-dir")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    records, references = [], {}
    for repeat in range(args.repeats):
        for filename in args.clips:
            clip = Path(filename)
            start = time.perf_counter()
            result = process_video(
                clip, schema_path=args.schema, model_dir=args.model_dir
            )
            elapsed = (time.perf_counter() - start) * 1000
            original = references.setdefault(
                str(clip.resolve()), result["tensor"].copy()
            )
            report = result["report"]
            records.append(
                {
                    "clipName": clip.name,
                    "clipSha256": hashlib.sha256(clip.read_bytes()).hexdigest(),
                    "repeat": repeat,
                    "wallMs": elapsed,
                    "ptsSpanMs": report["ptsSpanMs"],
                    "featureSchemaVersion": report["featureSchemaVersion"],
                    "decodedFrameCount": report["decodedFrameCount"],
                    "extractedFrameCount": report["frameCount"],
                    "inputStatus": report["inputStatus"],
                    "detectionRatios": report["detectionRatios"],
                    "usableTensorFrameRatio": report["usableTensorFrameRatio"],
                    "cpuRuntime": report["cpuRuntime"],
                    "timingsMs": report["timingsMs"],
                    "tensorMaxAbsDiffAcrossRuns": float(
                        np.max(np.abs(original - result["tensor"]))
                    ),
                }
            )
    durations = np.array([record["wallMs"] for record in records])
    with new_output(args.output) as output:
        write_json(
            output / "benchmark.json",
            {
                "scope": "Preprocessing including asset verification and detector initialization; excludes GRU, HTTP and UI",
                "platform": platform.platform(),
                "sampledClipCount": len(args.clips),
                "measurementCount": len(records),
                "p50Ms": float(np.percentile(durations, 50)),
                "p95Ms": float(np.percentile(durations, 95)),
                "maxMs": float(durations.max()),
                "underThreeSecondsRatio": float(np.mean(durations <= 3000)),
                "runs": records,
            },
        )
    print(
        f"{len(records)} measurements; preprocessing p95={np.percentile(durations, 95):.2f} ms"
    )


if __name__ == "__main__":
    main()
