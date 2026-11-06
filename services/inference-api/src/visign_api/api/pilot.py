"""Manage the local pilot worker and its persistent status."""

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from .admin import REPO, authorize

router = APIRouter(prefix="/api/admin/pilot", dependencies=[Depends(authorize)])
ROOT = REPO / ".local" / "pilot-runs"
WORKER = REPO / "admin" / "train model" / "pilot_worker.py"
ACTIVE = {"preparing", "training", "evaluating"}
lock = Lock()
process: subprocess.Popen | None = None


def save(folder: Path, state: dict) -> None:
    target = folder / "status.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    temporary.replace(target)


def current() -> tuple[Path | None, dict]:
    latest = ROOT / "latest.txt"
    if not latest.is_file():
        return None, {"phase": "idle"}
    job_id = latest.read_text("ascii").strip()
    if not re.fullmatch("[0-9a-f]{12}", job_id):
        raise HTTPException(500, "Mã job đã lưu không hợp lệ.")
    folder = ROOT / job_id
    state = json.loads((folder / "status.json").read_text("utf-8"))
    if state["phase"] in ACTIVE and process is not None and process.poll() is not None:
        state.update(phase="failed", error="Worker đã dừng. Xem worker.log trên backend.")
        save(folder, state)
    return folder, state


def start(folder: Path, state: dict, command: str, *options: str) -> dict:
    global process
    save(folder, state)
    try:
        with (folder / "worker.log").open("ab") as log:
            process = subprocess.Popen(
                [sys.executable, str(WORKER), command, str(folder), *options],
                cwd=REPO, stdout=log, stderr=subprocess.STDOUT,
            )
    except OSError as error:
        state.update(phase="failed", error="Không khởi động được worker.")
        save(folder, state)
        raise HTTPException(503, state["error"]) from error
    return state


@router.get("")
def status():
    with lock:
        return current()[1]


@router.get("/history")
def history():
    with lock:
        _, latest = current()
        jobs = []
        for folder in ROOT.iterdir() if ROOT.is_dir() else ():
            if not folder.is_dir() or not re.fullmatch("[0-9a-f]{12}", folder.name):
                continue
            status_file = folder / "status.json"
            try:
                updated = status_file.stat().st_mtime
                state = latest if latest.get("id") == folder.name else json.loads(
                    status_file.read_text("utf-8")
                )
                if state.get("id") != folder.name or "phase" not in state:
                    continue
            except (OSError, ValueError, AttributeError):
                continue
            jobs.append({**state, "updatedAt": updated, "group": "sot-cho"})
        local = ROOT.parent
        for path in local.glob("pilot-verification-*/*/status.json"):
            try:
                state = json.loads(path.read_text("utf-8"))
                if state["id"] != path.parent.name or "phase" not in state:
                    continue
                jobs.append({**state, "updatedAt": path.stat().st_mtime,
                             "title": "Lần kiểm thử", "group": "sot-cho",
                             "wandbDirectory": (path.parent / "wandb").relative_to(REPO).as_posix()})
            except (OSError, ValueError, KeyError, TypeError):
                continue
        for path in local.glob("quang-dev-*/exploratory*/report.json"):
            try:
                report = json.loads(path.read_text("utf-8"))
                counts = report["splitAudit"]["sampleCounts"]
                run_id = report["wandbRunId"]
                jobs.append({
                    "id": run_id, "phase": "complete", "updatedAt": path.stat().st_mtime,
                    "title": f"Chạy phát triển · {len(report['labelOrder'])} nhãn",
                    "accepted": sum(counts.values()), "sampleTotal": sum(counts.values()),
                    "epoch": len(report["history"]), "epochs": len(report["history"]),
                    "testCount": counts["test"], "metrics": {"accuracy": report["testTop1Accuracy"]},
                    "wandbMode": report["wandbMode"], "wandbRunId": run_id, "wandbUrl": report.get("wandbUrl"),
                    "wandbProject": "visign-dev",
                    "wandbDirectory": (path.parent / "wandb").relative_to(REPO).as_posix(),
                })
            except (OSError, ValueError, KeyError, TypeError):
                continue
        try:
            links = json.loads((local / "wandb-run-links.json").read_text("utf-8"))
        except (OSError, ValueError):
            links = {}
        for job in jobs:
            run_id = job.get("wandbRunId")
            url = links.get(run_id) if isinstance(links, dict) and isinstance(run_id, str) else None
            if isinstance(url, str) and re.fullmatch(
                r"https://(?:wandb\.ai/|forge\.coreweave\.com/wandb/)[\w.-]+/[\w.-]+/runs/"
                + re.escape(run_id), url
            ):
                job["wandbUrl"] = url
        try:
            hidden = json.loads((local / "hidden-train-runs.json").read_text("utf-8"))
        except (OSError, ValueError):
            hidden = []
        if not isinstance(hidden, list):
            hidden = []
        unique = {job["id"]: job for job in reversed(jobs) if job["id"] not in hidden}
        return sorted(unique.values(), key=lambda job: job["updatedAt"], reverse=True)


@router.post("/prepare", status_code=202)
def prepare():
    with lock:
        if current()[1]["phase"] in ACTIVE:
            raise HTTPException(409, "Đang có job pilot.")
        archive_value = os.environ.get("VISIGN_PILOT_DATA") or os.environ.get("VISIGN_PILOT_ZIP")
        if not archive_value or not (Path(archive_value).is_file() or (Path(archive_value) / "data/manifests/reviewed-dev.csv").is_file()):
            raise HTTPException(503, "Backend cần VISIGN_PILOT_DATA trỏ tới thư mục bàn giao hoặc ZIP của Quang.")
        folder = ROOT / uuid4().hex[:12]
        folder.mkdir(parents=True)
        state = {"id": folder.name, "phase": "preparing"}
        save(folder, state)
        latest = ROOT / "latest.txt"
        temporary = latest.with_suffix(".tmp")
        temporary.write_text(folder.name, "ascii")
        temporary.replace(latest)
        return start(folder, state, "prepare", "--archive", str(Path(archive_value).resolve()))


@router.post("/train", status_code=202)
def train():
    with lock:
        folder, state = current()
        if folder is None or state["phase"] != "ready":
            raise HTTPException(409, "Cần kiểm tra đủ 6 clip trước khi train.")
        if importlib.util.find_spec("wandb") is None:
            raise HTTPException(503, "Chưa cài wandb trong môi trường backend.")
        return start(folder, {**state, "phase": "training", "epoch": 0}, "train")
