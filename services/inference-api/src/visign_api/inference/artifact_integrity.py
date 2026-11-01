"""Validate transport checksums without importing the optional AI package."""

import hashlib
import json
from pathlib import Path

MANIFEST_NAME = "FILES-SHA256.json"
DELIVERY_FILES = (
    "model.pt", "feature_schema.json", "model_info.json", "training-report.json",
    "evaluation-report.json", "confusion-matrix.png", "parity-report.json",
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_delivery(artifact, required=False):
    root = Path(artifact).resolve()
    path = root / MANIFEST_NAME
    if not path.exists():
        if required:
            raise ValueError("Missing delivery checksum manifest")
        return False  # Raw training artifacts and legacy fixtures remain compatible.
    manifest = json.loads(path.read_text("utf-8"))
    files = manifest.get("sha256")
    if manifest.get("algorithm") != "SHA-256" or not isinstance(files, dict):
        raise ValueError("Invalid delivery checksum manifest")
    if set(files) != set(DELIVERY_FILES):
        raise ValueError("Delivery manifest must cover exactly the required files")
    for name in DELIVERY_FILES:
        candidate = root / name
        if candidate.is_symlink() or candidate.resolve().parent != root:
            raise ValueError("Delivery files must be regular files within artifact")
        if not candidate.is_file() or file_sha256(candidate) != files[name]:
            raise ValueError(f"Artifact checksum mismatch: {name}")
    return True
