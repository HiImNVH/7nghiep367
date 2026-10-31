"""Synthetic numbers exercise plumbing only, never reported as recognition quality."""

import csv
import json
import subprocess
import sys

import numpy as np
import pytest
from visign_ai.dataset.manifest import confined_path, read_manifest
from visign_ai.io import new_output
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest


def run_module(module, *args):
    result = subprocess.run(
        [sys.executable, "-m", module, *map(str, args)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_synthetic_train_evaluate_and_immutable_output(tmp_path):
    schema = load_schema()
    schema["status"] = "APPROVED"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), "utf-8")
    mapping = {
        "A_HCM": {"meaningId": "A", "displayText": "Test A"},
        "B_HCM": {"meaningId": "B", "displayText": "Test B"},
    }
    map_path = tmp_path / "classes.json"
    map_path.write_text(json.dumps(mapping), "utf-8")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "seed: 42\nhidden_size: 4\nnum_layers: 1\nbatch_size: 2\nepochs: 1\nlearning_rate: 0.001\nthreshold_candidates: [0.5, 0.7]\n"
    )
    rows = []
    for split in ("train", "validation", "test"):
        for index, label in enumerate(mapping):
            filename = f"{split}-{label}.npz"
            features = np.zeros((32, 234), np.float32)
            features[:, :156] = index
            features[:, 156:] = 1
            np.savez_compressed(
                tmp_path / filename,
                features=features,
                featureSchemaVersion=schema["featureSchemaVersion"],
                extractorVersion=schema["extractorVersion"],
                schemaSha256=schema_digest(schema),
            )
            rows.append(
                {
                    "sampleId": split + label,
                    "classLabel": label,
                    "signerId": split,
                    "recordingSessionId": split,
                    "sourceUri": "synthetic-test-only",
                    "rawPath": filename,
                    "landmarkPath": filename,
                    "split": split,
                    "licenseStatus": "approved",
                    "verificationStatus": "verified",
                }
            )
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    arguments = [
        "--manifest",
        manifest,
        "--feature-root",
        tmp_path,
        "--class-map",
        map_path,
        "--schema",
        schema_path,
        "--config",
        config_path,
        "--kind",
        "pilot",
        "--model-version",
        "synthetic-test-only",
    ]
    run_module("visign_ai.training.train", *arguments, "--output", tmp_path / "run-one")
    run_module("visign_ai.training.train", *arguments, "--output", tmp_path / "run-two")
    import torch

    first = torch.load(tmp_path / "run-one/model.pt", weights_only=True)
    second = torch.load(tmp_path / "run-two/model.pt", weights_only=True)
    for key in first["stateDict"]:
        torch.testing.assert_close(
            first["stateDict"][key], second["stateDict"][key], rtol=0, atol=0
        )
    run_module(
        "visign_ai.evaluation.evaluate",
        "--artifact",
        tmp_path / "run-one",
        "--manifest",
        manifest,
        "--feature-root",
        tmp_path,
        "--output",
        tmp_path / "evaluated",
    )
    info = json.loads((tmp_path / "evaluated/model_info.json").read_text("utf-8"))
    assert info["demoReady"] is False and info["artifactKind"] == "pilot"
    assert (tmp_path / "evaluated/confusion-matrix.png").is_file()
    assert (
        json.loads((tmp_path / "run-one/model_info.json").read_text("utf-8"))[
            "accuracy"
        ]
        is None
    )
    with pytest.raises(FileExistsError), new_output(tmp_path / "run-one"):
        pass
    rows[0]["licenseStatus"] = "unknown"
    with manifest.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="approved"):
        read_manifest(manifest)


def test_manifest_path_cannot_escape_data_root(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        confined_path(tmp_path, "../outside.npz")
