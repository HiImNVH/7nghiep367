"""Prepare and run the fixed SOT/CHO pilot on the backend machine."""

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from visign_ai.dataset.manifest import confined_path, dataset_version, read_class_map, read_manifest
from visign_ai.io import write_json
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest

REPO = Path(__file__).resolve().parents[2]
SCHEMA = REPO / "ai/configs/feature_schema.json"
CONFIG = REPO / "ai/configs/pilot-gru.yaml"
LABELS = ("CHO", "SOT")
SPLITS = ("train", "validation", "test")


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def cli(module, **options):
    args = [sys.executable, "-m", module]
    for name, value in options.items():
        args.extend(("--" + name.replace("_", "-"), str(value)))
    subprocess.run(args, cwd=REPO, check=True)


def train_arguments(folder, device):
    return SimpleNamespace(
        manifest=folder / "features/manifest.csv",
        feature_root=folder / "features",
        class_map=folder / "classes.json",
        schema=folder / "schema.json",
        config=folder / "config.yaml",
        output=folder / "trained",
        model_version="vsl-pilot-" + folder.name,
        kind="pilot",
        classes=list(LABELS),
        p0_meanings=None,
        device=device,
    )


@contextmanager
def read_handoff(source):
    if source.is_dir():
        yield lambda relative: confined_path(source, relative).read_bytes()
    else:
        with zipfile.ZipFile(source) as archive:
            yield archive.read


def prepare_data(folder, archive, update):
    from visign_ai.training.train import prepare

    shutil.copyfile(SCHEMA, folder / "schema.json")
    shutil.copyfile(CONFIG, folder / "config.yaml")
    schema = load_schema(folder / "schema.json")
    if schema["status"] != "APPROVED":
        raise ValueError("Schema pilot chưa được duyệt.")
    with read_handoff(archive) as read:
        for name in ("reviewed-dev.csv", "classes.json"):
            (folder / name).write_bytes(read("data/manifests/" + name))
        rows = [r for r in read_manifest(folder / "reviewed-dev.csv") if r["classLabel"] in LABELS]
        mapping = read_class_map(folder / "classes.json")
        if (
            len(rows) != 6
            or {(r["classLabel"], r["split"]) for r in rows}
            != {(label, split) for label in LABELS for split in SPLITS}
            or any(mapping[label]["meaningId"] != label for label in LABELS)
        ):
            raise ValueError("Pilot cần đúng 6 clip Sốt/Chờ, mỗi lớp đủ ba tập.")
        write_json(folder / "classes.json", {label: mapping[label] for label in LABELS})
        with (folder / "pilot.csv").open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        for row in rows:
            raw = confined_path(folder / "raw", row["rawPath"])
            content = read("data/" + row["rawPath"])
            if hashlib.sha256(content).hexdigest() != row["sha256"]:
                raise ValueError("SHA-256 video không khớp manifest: " + row["sampleId"])
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(content)
    cli(
        "visign_ai.landmarks.extract_manifest",
        manifest=folder / "pilot.csv", raw_root=folder / "raw",
        output=folder / "features", schema=folder / "schema.json",
    )
    report = json.loads((folder / "features/extraction-report.json").read_text("utf-8"))
    update(accepted=report["acceptedCount"], rejected=report["rejected"])
    if report["rejected"]:
        raise ValueError("Có clip thiếu landmark. Pilot không còn đủ cả ba tập.")
    from visign_ai.training.sequence_dataset import SequenceDataset

    args = train_arguments(folder, "cpu")
    _, processed, _, _, labels, _, _, _ = prepare(args)
    SequenceDataset(processed, args.feature_root, labels, schema)
    update(phase="ready", schemaSha256=schema_digest(schema), samples=6)


def run_training(folder, update):
    import wandb
    from visign_ai.training.train import prepare, train

    mode = os.environ.get("WANDB_MODE", "online")
    if mode not in {"online", "offline"}:
        raise ValueError("WANDB_MODE phải là online hoặc offline.")
    if mode == "online":
        try:
            logged_in = wandb.login(prompt=False, verify=True, timeout=15)
        except wandb.errors.Error as exc:
            raise ValueError("Không kết nối được W&B. Kiểm tra mạng và chạy wandb login trong VS Code.") from exc
        if not logged_in:
            raise ValueError("Chưa đăng nhập W&B. Chạy wandb login trong VS Code rồi thử lại.")
    device = os.environ.get("VISIGN_PILOT_DEVICE", "cpu")
    if device not in {"cpu", "cuda"}:
        raise ValueError("VISIGN_PILOT_DEVICE phải là cpu hoặc cuda.")
    args = train_arguments(folder, device)
    schema, _, _, config, _, _, _, audit = prepare(args)
    git = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip())
    provenance = {
        "gitCommit": git, "workingTreeDirty": dirty,
        "pilotManifest": dataset_version(folder / "pilot.csv"),
        "processedManifest": dataset_version(args.manifest),
        "schemaSha256": schema_digest(schema),
        "extractorVersion": schema["extractorVersion"],
        "splitCounts": audit["sampleCounts"], "device": device,
    }
    with wandb.init(
        project=os.environ.get("WANDB_PROJECT", "visign-pilot"),
        name="sot-cho-" + folder.name, mode=mode, dir=str(folder),
        config={**config, **provenance}, save_code=False, settings=wandb.Settings(disable_git=True, disable_code=True),
    ) as run:
        url = run.url if mode == "online" else None
        update(wandbUrl=url, wandbMode=mode, wandbRunId=run.id, epochs=config["epochs"])

        def log_epoch(values):
            run.log({
                "epoch": values["epoch"],
                "train_loss": values["trainLoss"],
                "validation_loss": values["validationLoss"],
            }, step=values["epoch"])
            update(epoch=values["epoch"])

        train(args, on_epoch=log_epoch)
        update(phase="evaluating")
        cli(
            "visign_ai.evaluation.evaluate",
            manifest=args.manifest, feature_root=args.feature_root,
            artifact=args.output, output=folder / "evaluated",
        )
        report = json.loads((folder / "evaluated/evaluation-report.json").read_text("utf-8"))
        metrics = {key: report[key] for key in ("accuracy", "macroF1", "perMeaningRecall", "confusionMatrix")}
        checkpoint = digest(folder / "evaluated/model.pt")
        run.summary.update({**metrics, "checkpointSha256": checkpoint})
        write_json(folder / "pilot-evidence.json", {
            **provenance, **metrics, "checkpointSha256": checkpoint,
            "wandbRunId": run.id, "wandbUrl": url, "wandbMode": mode,
        })
    update(phase="complete", metrics=metrics, checkpointSha256=checkpoint)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "train"))
    parser.add_argument("folder", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    state_path = args.folder / "status.json"
    state = json.loads(state_path.read_text("utf-8"))

    def update(**changes):
        state.update(changes)
        temporary = state_path.with_suffix(".tmp")
        write_json(temporary, state)
        temporary.replace(state_path)

    try:
        if args.phase == "prepare":
            prepare_data(args.folder, args.archive, update)
        else:
            run_training(args.folder, update)
    except Exception as error:
        message = str(error) if isinstance(error, (ValueError, ImportError)) else "Job lỗi. Xem worker.log trên máy backend."
        update(phase="failed", error=message)
        raise


if __name__ == "__main__":
    main()
