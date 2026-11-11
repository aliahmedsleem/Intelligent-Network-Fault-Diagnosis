"""Read-only validation of closed-loop Mininet experiment artifacts.

The API never executes host commands or trusts a reported pass flag without
checking underlying path observations. Ground truth is only for evaluation.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, model_validator
from .models import Network
from .localization import LocalizationRequest, Probe, localize


class PathObservation(BaseModel):
    source: str
    target: str
    baseline_loss_percent: float = Field(ge=0, le=100)
    observed_loss_percent: float = Field(ge=0, le=100)
    recovered_loss_percent: float | None = Field(default=None, ge=0, le=100)


class Decision(BaseModel):
    authorized: bool
    reason: str
    candidate: str | None = None


class Verification(BaseModel):
    status: str


class GroundTruth(BaseModel):
    fault_link: str
    top1_correct: bool | None = None


class ClosedLoopArtifact(BaseModel):
    mode: str
    network: Network
    probes: list[PathObservation] = Field(min_length=2, max_length=200)
    execution_policy: Decision
    verification: Verification
    ground_truth_for_evaluation_only: GroundTruth

    @model_validator(mode="after")
    def validate_contract(self):
        if self.mode != "mininet_closed_loop_measured":
            raise ValueError("Expected mininet_closed_loop_measured")
        if self.verification.status not in {"passed", "failed", "blocked"}:
            raise ValueError("Unknown verification state")
        return self


def inspect_closed_loop(artifact: ClosedLoopArtifact) -> dict:
    inferred = localize(LocalizationRequest(
        network=artifact.network,
        probes=[Probe(source=p.source, target=p.target,
                      baseline_loss_percent=p.baseline_loss_percent,
                      observed_loss_percent=p.observed_loss_percent)
                for p in artifact.probes],
    ))
    predicted = inferred["suspected_link_id"]
    expected_authorization = (
        inferred["status"] == "candidate_found"
        and predicted == artifact.ground_truth_for_evaluation_only.fault_link
    )
    flags: list[str] = []
    if artifact.execution_policy.authorized != expected_authorization:
        flags.append("authorization_disagrees_with_recomputed_policy")
    if artifact.execution_policy.candidate != predicted:
        flags.append("reported_candidate_disagrees_with_recomputed_inference")
    if artifact.ground_truth_for_evaluation_only.top1_correct is not None:
        actual_correct = inferred["status"] == "candidate_found" and predicted == artifact.ground_truth_for_evaluation_only.fault_link
        if artifact.ground_truth_for_evaluation_only.top1_correct != actual_correct:
            flags.append("reported_top1_disagrees_with_recomputed_inference")
    if artifact.verification.status == "passed" and not artifact.execution_policy.authorized:
        flags.append("passed_without_authorized_action")
    if artifact.verification.status == "blocked" and artifact.execution_policy.authorized:
        flags.append("blocked_despite_authorized_action")
    recovered = [p for p in artifact.probes if p.recovered_loss_percent is not None]
    if artifact.verification.status in {"passed", "failed"} and len(recovered) != len(artifact.probes):
        flags.append("incomplete_recovery_measurements")
    if artifact.verification.status == "passed" and not recovered:
        flags.append("passed_without_recovery_measurements")
    if artifact.verification.status == "blocked" and recovered:
        flags.append("blocked_but_recovery_measurements_present")
    # A passing result cannot be accepted without observed fault and recovery
    # on each of the two crossing paths of the fixed laboratory topology.
    crossing = {("h1", "h4"), ("h2", "h3")}
    if artifact.verification.status == "passed":
        for pair in crossing:
            matching = [p for p in artifact.probes if (p.source, p.target) == pair]
            if len(matching) != 1:
                flags.append("missing_or_duplicate_crossing_probe")
                continue
            p = matching[0]
            if (p.recovered_loss_percent is None or
                p.observed_loss_percent - p.baseline_loss_percent < 5 or
                p.recovered_loss_percent > p.baseline_loss_percent + 5):
                flags.append("recovery_threshold_not_met")
    return {
        "mode": artifact.mode,
        "reported_status": artifact.verification.status,
        "audit_status": "consistent" if not flags else "inconsistent",
        "quality_flags": sorted(set(flags)),
        "inference": inferred,
        "execution_policy_reported": artifact.execution_policy.model_dump(),
        "probes": [p.model_dump() for p in artifact.probes],
        "ground_truth_evaluation": {
            "link_id": artifact.ground_truth_for_evaluation_only.fault_link,
            "top1_correct_recomputed": inferred["status"] == "candidate_found" and predicted == artifact.ground_truth_for_evaluation_only.fault_link,
        },
        "note": "Read-only artifact audit; source authenticity and physical execution are not independently verified.",
    }
