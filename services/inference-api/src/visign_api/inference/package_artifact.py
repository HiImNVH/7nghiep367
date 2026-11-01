"""Export a versioned delivery only after WebM tensor parity and artifact checks."""

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from visign_api.inference.artifact_integrity import (
    DELIVERY_FILES,
    MANIFEST_NAME,
    file_sha256,
    verify_delivery,
)
from visign_api.inference.check_artifact import check_artifact


def package_artifact(artifact, clip, output):
    from visign_ai.io import new_output, write_json

    artifact, output = Path(artifact).resolve(), Path(output).resolve()
    if output == artifact or artifact in output.parents:
        raise ValueError("Delivery output must be outside the input artifact")
    if output.exists():
        raise FileExistsError("Output exists; choose a new delivery version")
    source_files = DELIVERY_FILES[:-1]
    for name in source_files:
        source = artifact / name
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Missing or non-regular evaluated artifact file: {name}")
    # Check a staged copy, so the exported bytes are the bytes actually tested.
    with new_output(output) as staging:
        for name in source_files:
            shutil.copyfile(artifact / name, staging / name)
        evaluation = json.loads((staging / "evaluation-report.json").read_text("utf-8"))
        metadata = json.loads((staging / "model_info.json").read_text("utf-8"))
        if evaluation.get("datasetVersion") != metadata.get("datasetVersion"):
            raise ValueError("Evaluation dataset differs from artifact")
        for key in ("accuracy", "macroF1", "perMeaningPrecision", "perMeaningRecall", "evaluatedAt"):
            if evaluation.get(key) is None or evaluation[key] != metadata.get(key):
                raise ValueError(f"Evaluation metadata mismatch: {key}")
        before = {name: file_sha256(staging / name) for name in source_files}
        report = check_artifact(staging, clip)
        if report["parity"]["status"] != "PASSED":
            raise ValueError("Golden clip parity is required")
        if any(file_sha256(staging / name) != before[name] for name in source_files):
            raise ValueError("Artifact changed during preflight")
        # Do not put raw clip paths, frames, landmarks or a synthetic accuracy claim in reports.
        report.pop("prediction", None)
        report["goldenClipSha256"] = file_sha256(clip)
        report["checkedAt"] = datetime.now(UTC).isoformat()
        write_json(staging / "parity-report.json", report)
        write_json(staging / MANIFEST_NAME, {
            "algorithm": "SHA-256",
            "sha256": {name: file_sha256(staging / name) for name in DELIVERY_FILES},
        })
        verify_delivery(staging, required=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("artifact", "clip", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    output = package_artifact(args.artifact, args.clip, args.output)
    print(f"Delivery written: {output}. Release approval is separate.")


if __name__ == "__main__":
    main()
