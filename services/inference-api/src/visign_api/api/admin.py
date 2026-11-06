"""Opt-in local admin tools for inspecting clips."""

import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from threading import Lock

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

router = APIRouter(prefix="/api/admin")
LIMIT = 100 * 1024 * 1024
INSPECTION = Lock()
REPO = Path(__file__).resolve().parents[5]
WORKER = REPO / "admin" / "train model" / "inspect_video.py"


def authorize(authorization: str = Header(default="")) -> None:
    token = os.environ.get("VISIGN_ADMIN_TOKEN")
    if not token:
        raise HTTPException(404, "Chưa bật dịch vụ admin trên backend.")
    if not secrets.compare_digest(authorization.encode(), f"Bearer {token}".encode()):
        raise HTTPException(401, "Mã truy cập admin không đúng.")


@router.post("/inspect", dependencies=[Depends(authorize)])
def inspect(video: UploadFile):
    if video.size is not None and video.size > LIMIT:
        raise HTTPException(413, "Video vượt 100 MiB.")
    if not INSPECTION.acquire(blocking=False):
        raise HTTPException(409, "Đang có clip khác được xử lý.")
    root = None
    download = False
    try:
        root = Path(tempfile.mkdtemp(prefix="visign-admin-"))
        clip = root / "input"
        size = 0
        with clip.open("wb") as target:
            while chunk := video.file.read(1024 * 1024):
                size += len(chunk)
                if size > LIMIT:
                    raise HTTPException(413, "Video vượt 100 MiB.")
                target.write(chunk)
        try:
            job = subprocess.run(
                [sys.executable, str(WORKER), str(clip), str(root / "result")],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(504, "Kiểm tra clip quá 5 phút.") from exc
        if job.returncode == 2 and job.stdout:
            raise HTTPException(422, json.loads(job.stdout)["detail"])
        if job.returncode:
            raise HTTPException(503, "Kiểm tra môi trường AI và bộ detector trên backend.")
        clip.unlink()
        # Stored ZIP entries can be opened in the browser without a dependency.
        from zipfile import ZipFile

        archive = root / "result.zip"
        with ZipFile(archive, "w") as bundle:
            for path in sorted((root / "result").rglob("*")):
                if path.is_file():
                    bundle.write(path, path.relative_to(root / "result").as_posix())
        response = FileResponse(
            archive,
            media_type="application/zip",
            filename="visign-demo2-result.zip",
            background=BackgroundTask(shutil.rmtree, root, ignore_errors=True),
        )
        download = True
        return response
    finally:
        if root is not None and not download:
            shutil.rmtree(root, ignore_errors=True)
        INSPECTION.release()
