"""Read approved handoffs without modifying their labels or split assignments."""

import csv
import hashlib
import json
from pathlib import Path


def read_manifest(path):
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError("Manifest is empty")
    seen = set()
    required = ("sampleId", "classLabel", "recordingSessionId", "sourceUri", "rawPath")
    for row in rows:
        if any(not row.get(key, "").strip() for key in required):
            raise ValueError("Missing required manifest fields")
        if row["sampleId"] in seen:
            raise ValueError("Duplicate sampleId")
        seen.add(row["sampleId"])
        if (
            row.get("licenseStatus") != "approved"
            or row.get("verificationStatus") != "verified"
        ):
            raise ValueError("Only approved, verified samples can be processed")
        if row.get("split") not in ("train", "validation", "test"):
            raise ValueError("A reviewed train/validation/test split is required")
    return rows


def dataset_version(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def confined_path(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute():
        raise ValueError("Manifest paths must be relative")
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError("Manifest path escapes its data root")
    return result


def read_class_map(path):
    mapping = json.loads(Path(path).read_text("utf-8-sig"))
    if not mapping:
        raise ValueError("Class map is empty")
    for label, item in mapping.items():
        if (
            not label
            or not item.get("meaningId")
            or not item.get("displayText", "").strip()
        ):
            raise ValueError("Each class needs meaningId and displayText")
    return mapping


def audit_splits(rows, kind):
    """Reject leakage in all partitions, never generate a new split for the consumer."""
    sessions, signers = {}, {}
    for row in rows:
        partition = row["split"]
        session = row["recordingSessionId"]
        if session in sessions and sessions[session] != partition:
            raise ValueError("recordingSessionId leakage across splits")
        sessions[session] = partition
        signer = row.get("signerId", "").strip()
        if signer:
            if signer in signers and signers[signer] != partition:
                raise ValueError("signerId leakage across splits")
            signers[signer] = partition
    has_signers = all(row.get("signerId", "").strip() for row in rows)
    if kind == "full" and not has_signers:
        raise ValueError("Full training requires signerId on every sample")
    return {
        "mode": "signer-held-out" if has_signers else "session-only",
        "passed": True,
        "sampleCounts": {
            split: sum(row["split"] == split for row in rows)
            for split in ("train", "validation", "test")
        },
        "signerCounts": {
            split: len(
                {
                    row.get("signerId")
                    for row in rows
                    if row["split"] == split and row.get("signerId")
                }
            )
            for split in ("train", "validation", "test")
        },
    }
