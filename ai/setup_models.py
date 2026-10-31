"""Fetch the pinned MediaPipe detectors and validate hashes before publishing."""

import hashlib
import json
import urllib.request
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    manifest = root / "configs/download-manifest.json"
    destination = root / "models"
    destination.mkdir(exist_ok=True)
    for item in json.loads(manifest.read_text("utf-8-sig")):
        target = destination / item["name"]
        if (
            target.exists()
            and hashlib.sha256(target.read_bytes()).hexdigest()
            == item["sha256"].lower()
        ):
            continue
        data = urllib.request.urlopen(item["url"], timeout=60).read()
        if hashlib.sha256(data).hexdigest() != item["sha256"].lower():
            raise ValueError(f"Detector checksum mismatch: {item['name']}")
        temporary = target.with_suffix(".download")
        temporary.write_bytes(data)
        temporary.replace(target)
    (destination / "download-manifest.json").write_bytes(manifest.read_bytes())
    print("Pinned detector assets ready")


if __name__ == "__main__":
    main()
