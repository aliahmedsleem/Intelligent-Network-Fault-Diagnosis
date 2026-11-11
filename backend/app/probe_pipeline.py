"""Independent end-to-end probe batch -> topology localization.

The fault label in the imported data is used only for *evaluation* after
inference, never supplied to the localization algorithm.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator
from .models import Network
from .localization import Probe, LocalizationRequest, localize


class ProbeObservation(BaseModel):
    source: str
    target: str
    baseline_loss_percent: float = Field(ge=0, le=100)
    observed_loss_percent: float = Field(ge=0, le=100)


class ProbeBatch(BaseModel):
    mode: str
    network: Network
    probes: list[ProbeObservation] = Field(min_length=2, max_length=200)
    ground_truth_link_id: str | None = None
    threshold_pp: float = Field(default=5, gt=0, le=100)

    @model_validator(mode="after")
    def validate_mode(self):
        if self.mode != "mininet_multi_probe_measured":
            raise ValueError("Only mininet_multi_probe_measured is supported")
        return self


def analyze_batch(batch: ProbeBatch) -> dict:
    inference = localize(LocalizationRequest(
        network=batch.network,
        probes=[Probe(**p.model_dump()) for p in batch.probes],
        loss_threshold_pp=batch.threshold_pp,
    ))
    ground_truth = batch.ground_truth_link_id
    evaluation = {
        "ground_truth_link_id": ground_truth,
        "top1_correct": (inference["suspected_link_id"] == ground_truth)
        if ground_truth is not None and inference["status"] == "candidate_found" else None,
        "note": "Ground truth evaluated only after inference; never used to rank links.",
    }
    return {"mode": batch.mode, "localization": inference, "evaluation": evaluation}
