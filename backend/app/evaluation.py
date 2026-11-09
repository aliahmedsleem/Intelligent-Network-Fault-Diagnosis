"""Reproducible offline evaluation of recorded localization decisions.

Does not generate synthetic measurements or claim real-world accuracy.
"""
from __future__ import annotations

from math import sqrt
from pydantic import BaseModel, Field
from .probe_pipeline import ProbeBatch, analyze_batch


class EvaluationDataset(BaseModel):
    trials: list[ProbeBatch] = Field(min_length=1, max_length=500)


def wilson(successes: int, n: int) -> dict | None:
    if n == 0:
        return None
    z = 1.959963984540054
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return {"rate": round(p, 5), "lower_95": round(max(0, center - margin), 5),
            "upper_95": round(min(1, center + margin), 5)}


def evaluate_dataset(dataset: EvaluationDataset) -> dict:
    cases = []
    for index, batch in enumerate(dataset.trials):
        analysis = analyze_batch(batch)
        localization = analysis["localization"]
        truth = batch.ground_truth_link_id
        cases.append({
            "index": index,
            "ground_truth": truth,
            "prediction": localization["suspected_link_id"],
            "status": localization["status"],
            "correct": localization["suspected_link_id"] == truth
            if truth is not None and localization["status"] == "candidate_found" else None,
        })
    labeled = [x for x in cases if x["ground_truth"] is not None]
    correct = sum(x["correct"] is True for x in labeled)
    ambiguous = sum(x["status"] == "ambiguous" for x in cases)
    identified = sum(x["status"] == "candidate_found" for x in cases)
    return {
        "mode": "offline_measured_probe_evaluation",
        "trial_count": len(cases),
        "labeled_trial_count": len(labeled),
        "top1_accuracy_over_all_labeled": wilson(correct, len(labeled)),
        "ambiguity_rate": wilson(ambiguous, len(cases)),
        "unique_prediction_rate": wilson(identified, len(cases)),
        "cases": cases,
        "method": "Wilson score 95% intervals; ambiguous/insufficient predictions count as incorrect for Top-1 accuracy.",
        "limitations": ["Uploaded trials are not independently authenticated.",
                        "Intervals assume independent trials; correlated repeated runs violate that assumption.",
                        "No dataset quality or class balance guarantee."],
    }
