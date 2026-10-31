"""Metrics are aggregated by meaning, including different class variants."""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)


def meaning_metrics(truth, predictions, meanings):
    if not truth or len(truth) != len(predictions):
        raise ValueError(
            "Evaluation needs equally sized, nonempty truth and predictions"
        )
    if set(truth) - set(meanings) or set(predictions) - set(meanings):
        raise ValueError("Unknown meaning in evaluation")
    precision, recall, f1, _ = precision_recall_fscore_support(
        truth, predictions, labels=meanings, zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(truth, predictions)),
        "macroF1": float(np.mean(f1)),
        "perMeaningPrecision": dict(zip(meanings, precision.tolist())),
        "perMeaningRecall": dict(zip(meanings, recall.tolist())),
        "confusionMatrix": confusion_matrix(
            truth, predictions, labels=meanings
        ).tolist(),
        "testSampleCounts": {meaning: truth.count(meaning) for meaning in meanings},
    }
