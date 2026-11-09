"""Conservative, auditable diagnosis-to-remediation decision pipeline.

Never issues privileged commands. A candidate is only approved for a lab
remediation plan if independent probes uniquely identify one link and
the proposed action is explicitly allowlisted.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator
from .probe_pipeline import ProbeBatch, analyze_batch


class LifecycleRequest(BaseModel):
    batch: ProbeBatch
    requested_action: str = "remove_injected_loss"
    require_manual_approval: bool = True

    @model_validator(mode="after")
    def safe_action(self):
        if self.requested_action != "remove_injected_loss":
            raise ValueError("Only removal of a controlled injected loss is supported")
        return self


def plan_lifecycle(request: LifecycleRequest) -> dict:
    result = analyze_batch(request.batch)
    diagnosis = result["localization"]
    unique = diagnosis["status"] == "candidate_found" and diagnosis["suspected_link_id"] is not None
    if not unique:
        reason = "No unique fault location; remediation blocked"
    elif request.require_manual_approval:
        reason = "Manual approval required before any lab action"
    else:
        reason = "Eligible for a separate, controlled lab execution; no action executed by API"
    return {
        "mode": "diagnosis_remediation_planning",
        "diagnosis": diagnosis,
        "evaluation": result["evaluation"],
        "remediation": {
            "action": request.requested_action if unique else None,
            "target_link": diagnosis["suspected_link_id"] if unique else None,
            "status": "blocked" if not unique else ("awaiting_approval" if request.require_manual_approval else "plan_ready"),
            "executed": False,
            "reason": reason,
        },
        "verification": {"status": "not_run", "note": "Measured post-action verification requires a separate Mininet run."},
        "safety": ["No shell execution in API", "Ambiguous inference blocks remediation", "Known lab action only"],
    }
