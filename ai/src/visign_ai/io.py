"""Publish a complete, immutable output directory only after a successful run."""

import json
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path


def write_json(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), "utf-8"
    )


@contextmanager
def new_output(path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Output exists, choose a new version: {path}")
    temporary = Path(tempfile.mkdtemp(prefix=".visign-", dir=path.parent))
    try:
        yield temporary
        # rename refuses an existing directory on Windows, including a concurrent publisher.
        temporary.rename(path)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
