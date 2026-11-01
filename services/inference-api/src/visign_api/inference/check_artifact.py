"""Read-only pilot/full handoff check; never changes approval or active service state."""

import argparse
import json
from pathlib import Path
from uuid import uuid4

import numpy as np

from visign_api.config import settings
from visign_api.domain.model_version import ArtifactKind
from visign_api.inference.clip_validator import validate_clip_file
from visign_api.inference.predictor import PredictorRegistry


def check_artifact(artifact, clip=None):
    # A fresh registry prevents rollback from masking a rejected candidate.
    predictor = PredictorRegistry().load_artifact(str(artifact))
    if predictor.metadata.artifactKind == ArtifactKind.FIXTURE:
        raise ValueError("Handoff requires a pilot/full GRU, not a fixture")
    shared = predictor._predictor
    if not shared.label_binding_verified:
        raise ValueError("Unbound legacy labels: retrain before a new handoff")
    report = {
        "artifactLoadPassed": True,
        "modelVersion": predictor.metadata.modelVersion,
        "featureSchemaVersion": predictor.metadata.featureSchemaVersion,
        "extractorVersion": predictor.metadata.extractorVersion,
        "labelBindingVerified": True,
        "demoReady": predictor.metadata.demoReady,
        "parity": {"status": "NOT_RUN"},
        "scope": "Technical compatibility only; not VSL accuracy or web latency acceptance",
    }
    if clip is not None:
        from visign_ai.landmarks.pipeline import process_video

        clip = Path(clip)
        validate_clip_file(clip)  # Same WebM/size boundary as the API.
        options = {
            "min_duration_ms": settings.min_duration_ms,
            "max_duration_ms": settings.max_duration_ms,
        }
        offline = process_video(
            clip, schema_path=shared.schema_path, model_dir=shared.model_dir,
            expected_schema_version=predictor.metadata.featureSchemaVersion, **options
        )
        serving = shared.clip_to_tensor(clip, **options)
        for key in ("tensor", "point_valid", "masks", "tensor_mask"):
            if key == "tensor":
                if not np.isfinite(offline[key]).all() or not np.isfinite(serving[key]).all():
                    raise ValueError("Non-finite tensor")
                np.testing.assert_allclose(offline[key], serving[key], rtol=0, atol=1e-6)
            else:
                np.testing.assert_array_equal(offline[key], serving[key])
        report["parity"] = {
            "status": "PASSED", "shape": list(offline["tensor"].shape),
            "maxAbsDiff": float(np.abs(offline["tensor"] - serving["tensor"]).max()),
            "atol": 1e-6, "masksEqual": True,
        }
        # Exercises GRU scores and the API error mapping on the same clip.
        result = predictor.predict(clip, str(uuid4()))
        report["prediction"] = {
            "classLabel": result.classLabel, "confidence": result.confidence,
            "text": result.text, "qualityHints": result.qualityHints.model_dump(),
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--require-delivery", action="store_true")
    parser.add_argument("--output", help="Write a new JSON report file; refuses overwrite")
    parser.add_argument("--clip", help="Optional reviewed WebM; enables tensor/mask parity")
    args = parser.parse_args()
    try:
        if args.output and Path(args.output).exists():
            raise FileExistsError("Report exists; choose a new output file")
        if args.require_delivery:
            from visign_api.inference.artifact_integrity import verify_delivery

            verify_delivery(args.artifact, required=True)
        report = check_artifact(args.artifact, args.clip)
        if args.output:
            with Path(args.output).open("x", encoding="utf-8") as stream:
                json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
    except Exception as error:
        print(json.dumps({"artifactLoadPassed": False, "error": str(error)}, ensure_ascii=True))
        raise SystemExit(1) from error
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
