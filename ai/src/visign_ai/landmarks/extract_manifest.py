"""Extract approved samples without changing the handed-off class labels or splits."""

import argparse
import csv

import numpy as np

from visign_ai.dataset.manifest import confined_path, dataset_version, read_manifest
from visign_ai.io import new_output, write_json

from .pipeline import PipelineError, process_video
from .sequence_transform import schema_digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--schema")
    parser.add_argument("--model-dir")
    args = parser.parse_args()
    rows = read_manifest(args.manifest)
    accepted, rejected = [], []
    with new_output(args.output) as output:
        (output / "sequences").mkdir()
        for index, row in enumerate(rows):
            path = confined_path(args.raw_root, row["rawPath"])
            try:
                result = process_video(
                    path, schema_path=args.schema, model_dir=args.model_dir
                )
                if result["report"]["inputStatus"] != "HAS_USABLE_FRAMES":
                    raise PipelineError("INSUFFICIENT_LANDMARKS", "No usable frames")
            except PipelineError as error:
                rejected.append({"sampleId": row["sampleId"], "code": error.code})
                continue
            relative = f"sequences/{index:06d}.npz"
            schema = result["schema"]
            np.savez_compressed(
                output / relative,
                features=result["tensor"],
                missingMask=~result["tensor_mask"],
                timestampsMs=result["target"],
                featureSchemaVersion=schema["featureSchemaVersion"],
                extractorVersion=schema["extractorVersion"],
                schemaSha256=schema_digest(schema),
            )
            accepted.append({**row, "landmarkPath": relative})
        fields = list(dict.fromkeys([*rows[0], "landmarkPath"]))
        with (output / "manifest.csv").open(
            "w", encoding="utf-8", newline=""
        ) as target:
            writer = csv.DictWriter(target, fields)
            writer.writeheader()
            writer.writerows(accepted)
        write_json(
            output / "extraction-report.json",
            {
                "sourceDatasetVersion": dataset_version(args.manifest),
                "acceptedCount": len(accepted),
                "rejected": rejected,
                "reviewRequiredAfterRejection": bool(rejected),
            },
        )
    print(
        f"Extracted {len(accepted)} samples, rejected {len(rejected)}. Review report before training."
    )


if __name__ == "__main__":
    main()
