"""Evaluate a frozen checkpoint on the exact handed-off test split."""

import argparse
import json
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from visign_ai.dataset.manifest import audit_splits, dataset_version, read_manifest
from visign_ai.inference import GRUPredictor
from visign_ai.io import new_output, write_json
from visign_ai.landmarks.sequence_transform import load_schema
from visign_ai.training.sequence_dataset import SequenceDataset

from .metrics import meaning_metrics
from .release_gate import passes_release_gate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("artifact", "manifest", "feature-root", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    predictor = GRUPredictor(args.artifact)
    metadata = predictor.metadata.copy()
    if metadata["datasetVersion"] != dataset_version(args.manifest):
        raise ValueError("Evaluation manifest differs from the training handoff")
    labels, meanings = metadata["classLabels"], metadata["meanings"]
    rows = [row for row in read_manifest(args.manifest) if row["classLabel"] in labels]
    audit = audit_splits(rows, metadata["artifactKind"])
    test_rows = [row for row in rows if row["split"] == "test"]
    if {row["classLabel"] for row in test_rows} != set(labels):
        raise ValueError("Test split must cover every class")
    dataset = SequenceDataset(
        test_rows, args.feature_root, labels, load_schema(predictor.schema_path)
    )
    truth, predicted, durations, accepted = [], [], [], []
    predictor.model.eval()
    with torch.inference_mode():
        for sequence, target in dataset:
            start = time.perf_counter()
            probabilities = predictor.model(
                sequence.unsqueeze(0), torch.tensor([len(sequence)])
            ).softmax(-1)[0]
            score, index = probabilities.max(0)
            durations.append((time.perf_counter() - start) * 1000)
            truth.append(metadata["meaningMap"][labels[target]])
            predicted.append(metadata["meaningMap"][labels[int(index)]])
            accepted.append(float(score) >= metadata["acceptanceThreshold"])
    report = meaning_metrics(truth, predicted, meanings)
    accepted = np.array(accepted, dtype=bool)
    report.update(
        {
            "datasetVersion": metadata["datasetVersion"],
            "splitAudit": audit,
            "evaluatedAt": datetime.now(UTC).isoformat(),
            "meaningOrder": meanings,
            "acceptanceThreshold": metadata["acceptanceThreshold"],
            "acceptedCoverage": float(accepted.mean()),
            "acceptedMeaningAccuracy": float(
                (np.array(truth)[accepted] == np.array(predicted)[accepted]).mean()
            )
            if accepted.any()
            else None,
            "inferOnlyLatencyMs": {
                "p50": float(np.percentile(durations, 50)),
                "p95": float(np.percentile(durations, 95)),
            },
            "latencyScope": "Pre-extracted tensor, CPU inference only. End-to-end benchmark pending.",
            "negativeOodEvaluation": "pending reviewed negative/OOD clips",
        }
    )
    training = json.loads(
        (Path(args.artifact) / "training-report.json").read_text("utf-8")
    )
    report["modelQualityGatePassed"] = passes_release_gate(
        metadata["artifactKind"], meanings, report, training["p0Meanings"]
    )
    for key in (
        "accuracy",
        "macroF1",
        "perMeaningPrecision",
        "perMeaningRecall",
        "evaluatedAt",
    ):
        metadata[key] = report[key]
    metadata["demoReady"] = False
    report["releaseStatus"] = "pending end-to-end checks and Huy approval"
    with new_output(args.output) as output:
        for name in ("model.pt", "feature_schema.json", "training-report.json"):
            shutil.copyfile(Path(args.artifact) / name, output / name)
        write_json(output / "model_info.json", metadata)
        write_json(output / "evaluation-report.json", report)
        fig, axis = plt.subplots(figsize=(max(6, len(meanings)), max(5, len(meanings))))
        axis.imshow(report["confusionMatrix"], cmap="Blues")
        axis.set(
            xticks=range(len(meanings)),
            yticks=range(len(meanings)),
            xticklabels=meanings,
            yticklabels=meanings,
            xlabel="Predicted",
            ylabel="True",
        )
        plt.setp(axis.get_xticklabels(), rotation=45, ha="right")
        for i, row in enumerate(report["confusionMatrix"]):
            for j, value in enumerate(row):
                axis.text(j, i, str(value), ha="center", va="center")
        fig.tight_layout()
        fig.savefig(output / "confusion-matrix.png", dpi=150)
        plt.close(fig)
    print(
        "Evaluation saved. Review model card and end-to-end benchmark before release."
    )


if __name__ == "__main__":
    main()
