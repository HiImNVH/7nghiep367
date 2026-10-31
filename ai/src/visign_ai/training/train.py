"""Train a reproducible GRU only from approved schema and reviewed manifest splits."""

import argparse
import csv
import os
import random
from pathlib import Path

import numpy as np
import torch
import yaml
from torch.utils.data import DataLoader

from visign_ai.dataset.manifest import (
    audit_splits,
    dataset_version,
    read_class_map,
    read_manifest,
)
from visign_ai.io import new_output, write_json
from visign_ai.landmarks.sequence_transform import load_schema, schema_digest

from .gru_classifier import GRUClassifier
from .sequence_dataset import SequenceDataset, collate_sequences


def probabilities(model, loader, device):
    scores, labels = [], []
    model.eval()
    with torch.inference_mode():
        for sequences, lengths, target in loader:
            scores.append(
                model(sequences.to(device), lengths).softmax(-1).cpu().numpy()
            )
            labels.extend(target.tolist())
    return np.concatenate(scores), np.array(labels)


def prepare(args):
    schema = load_schema(args.schema)
    if schema.get("status") != "APPROVED":
        raise ValueError("Schema approval is required before real training")
    rows = read_manifest(args.manifest)
    mapping = read_class_map(args.class_map)
    config = yaml.safe_load(Path(args.config).read_text("utf-8-sig"))
    labels = args.classes or sorted({row["classLabel"] for row in rows})
    if len(labels) != len(set(labels)) or set(labels) - set(mapping):
        raise ValueError("Invalid class subset")
    if set(labels) - {row["classLabel"] for row in rows}:
        raise ValueError("Requested class has no manifest samples")
    rows = [row for row in rows if row["classLabel"] in labels]
    meanings = list(dict.fromkeys(mapping[label]["meaningId"] for label in labels))
    p0 = []
    if args.kind == "pilot" and not 1 <= len(meanings) <= 3:
        raise ValueError("Pilot must support between one and three meanings")
    if args.kind == "full":
        if not args.p0_meanings:
            raise ValueError("Full training requires the frozen P0 meaning catalog")
        with Path(args.p0_meanings).open(encoding="utf-8-sig", newline="") as source:
            p0 = [row["meaningId"] for row in csv.DictReader(source)]
        if len(p0) != len(set(p0)) or len(p0) != 10 or set(p0) != set(meanings):
            raise ValueError(
                "Full class subset must match exactly ten approved P0 meanings"
            )
    audit = audit_splits(rows, args.kind)
    for split in ("train", "validation", "test"):
        present = {row["classLabel"] for row in rows if row["split"] == split}
        if present != set(labels):
            raise ValueError(f"{split} must cover every selected class")
    return schema, rows, mapping, config, labels, meanings, p0, audit


def train(args):
    schema, rows, mapping, config, labels, meanings, p0, audit = prepare(args)
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    seed = int(config["seed"])
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    device = torch.device(args.device)
    datasets = {
        split: SequenceDataset(
            [row for row in rows if row["split"] == split],
            args.feature_root,
            labels,
            schema,
        )
        for split in ("train", "validation")
    }
    generator = torch.Generator().manual_seed(seed)
    loaders = {
        split: DataLoader(
            dataset,
            batch_size=int(config["batch_size"]),
            shuffle=split == "train",
            generator=generator,
            collate_fn=collate_sequences,
            num_workers=0,
        )
        for split, dataset in datasets.items()
    }
    model_config = {
        "input_size": len(schema["landmarkOrder"]) * 3,
        "hidden_size": int(config["hidden_size"]),
        "num_classes": len(labels),
        "num_layers": int(config["num_layers"]),
    }
    model = GRUClassifier(**model_config).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config["learning_rate"]))
    best_loss, best_state, history = float("inf"), None, []
    if int(config["epochs"]) < 1:
        raise ValueError("epochs must be positive")
    for epoch in range(int(config["epochs"])):
        model.train()
        train_loss = 0.0
        for sequences, lengths, target in loaders["train"]:
            optimizer.zero_grad()
            loss = torch.nn.functional.cross_entropy(
                model(sequences.to(device), lengths), target.to(device)
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item() * len(target)
        scores, truth = probabilities(model, loaders["validation"], device)
        validation_loss = float(
            -np.log(np.maximum(scores[np.arange(len(truth)), truth], 1e-12)).mean()
        )
        history.append(
            {
                "epoch": epoch + 1,
                "trainLoss": train_loss / len(datasets["train"]),
                "validationLoss": validation_loss,
            }
        )
        if validation_loss < best_loss:
            best_loss = validation_loss
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }
    if best_state is None:
        raise ValueError("Training produced no finite validation checkpoint")
    model.load_state_dict(best_state)
    scores, truth = probabilities(model, loaders["validation"], device)
    # Threshold uses validation only. Report the rejection/coverage tradeoff explicitly.
    confidence, predicted = scores.max(axis=1), scores.argmax(axis=1)
    candidates = []
    for threshold in config["threshold_candidates"]:
        threshold = float(threshold)
        if not 0 <= threshold <= 1:
            raise ValueError("Invalid threshold candidate")
        accepted = confidence >= threshold
        precision = (
            float((predicted[accepted] == truth[accepted]).mean())
            if accepted.any()
            else 0.0
        )
        candidates.append(
            {
                "threshold": threshold,
                "coverage": float(accepted.mean()),
                "acceptedClassAccuracy": precision,
                "score": float(
                    ((predicted == truth) & accepted).mean()
                    - ((predicted != truth) & accepted).mean()
                ),
            }
        )
    selected = max(candidates, key=lambda item: (item["score"], item["coverage"]))
    metadata = {
        "modelVersion": args.model_version,
        "artifactKind": args.kind,
        "datasetVersion": dataset_version(args.manifest),
        "featureSchemaVersion": schema["featureSchemaVersion"],
        "extractorVersion": schema["extractorVersion"],
        "meanings": meanings,
        "classLabels": labels,
        "meaningMap": {label: mapping[label]["meaningId"] for label in labels},
        "displayTextMap": {
            mapping[label]["meaningId"]: mapping[label]["displayText"]
            for label in labels
        },
        "acceptanceThreshold": selected["threshold"],
        "accuracy": None,
        "macroF1": None,
        "perMeaningPrecision": None,
        "perMeaningRecall": None,
        "evaluatedAt": None,
        "demoReady": False,
    }
    with new_output(args.output) as output:
        torch.save(
            {
                "modelConfig": model_config,
                "stateDict": best_state,
                "schemaSha256": schema_digest(schema),
            },
            output / "model.pt",
        )
        write_json(output / "feature_schema.json", schema)
        write_json(output / "model_info.json", metadata)
        write_json(
            output / "training-report.json",
            {
                "seed": seed,
                "config": config,
                "device": str(device),
                "torchVersion": torch.__version__,
                "splitAudit": audit,
                "history": history,
                "p0Meanings": p0,
                "validationThresholdSweep": candidates,
                "thresholdRule": "validation max(correct accepted - incorrect accepted), then coverage",
            },
        )
    print("Training complete. Test evaluation and lead approval remain pending.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "manifest",
        "feature-root",
        "class-map",
        "schema",
        "config",
        "output",
        "model-version",
    ):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--kind", choices=["pilot", "full"], required=True)
    parser.add_argument("--classes", nargs="+")
    parser.add_argument("--p0-meanings")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    train(parser.parse_args())


if __name__ == "__main__":
    main()
