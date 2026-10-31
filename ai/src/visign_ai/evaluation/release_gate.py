"""Evaluate model-quality eligibility. Final demo approval belongs to Huy."""

import math


def passes_release_gate(kind, meanings, report, p0_meanings):
    recall = report.get("perMeaningRecall", {})
    macro_f1 = report.get("macroF1")
    return bool(
        kind == "full"
        and len(meanings) == len(set(meanings)) == 10
        and set(meanings) == set(p0_meanings)
        and report.get("splitAudit", {}).get("passed") is True
        and report["splitAudit"].get("mode") == "signer-held-out"
        and isinstance(macro_f1, (int, float))
        and math.isfinite(macro_f1)
        and 0.80 <= macro_f1 <= 1
        and all(
            isinstance(recall.get(meaning), (int, float))
            and math.isfinite(recall[meaning])
            and 0.65 <= recall[meaning] <= 1
            and report.get("testSampleCounts", {}).get(meaning, 0) > 0
            for meaning in meanings
        )
    )
