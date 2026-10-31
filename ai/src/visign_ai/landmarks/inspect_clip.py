"""Explicit offline debugging export, kept separate from API request handling."""

import argparse

import numpy as np

from visign_ai.io import new_output, write_json

from .pipeline import process_video
from .sequence_transform import schema_digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--schema")
    parser.add_argument("--model-dir")
    args = parser.parse_args()
    result = process_video(args.clip, schema_path=args.schema, model_dir=args.model_dir)
    schema = result["schema"]
    with new_output(args.output) as output:
        np.savez_compressed(
            output / "features.npz",
            features=result["tensor"],
            missingMask=~result["tensor_mask"],
            timestampsMs=result["target"],
            schemaSha256=schema_digest(schema),
            featureSchemaVersion=schema["featureSchemaVersion"],
            extractorVersion=schema["extractorVersion"],
        )
        np.savez_compressed(
            output / "raw-landmarks.npz",
            xy=result["coords"],
            pointValid=result["point_valid"],
            timestampsMs=result["timestamps"],
        )
        write_json(output / "report.json", result["report"])
        write_json(output / "feature_schema.json", schema)
    print(result["report"]["inputStatus"], result["tensor"].shape)


if __name__ == "__main__":
    main()
