"""Pure, testable fail-closed policy for a dedicated Mininet laboratory.

The known injected fault ID is used as an *execution safety interlock* only,
not by the inference algorithm. No arbitrary shell commands or interfaces.
"""
from __future__ import annotations


def decide_remediation(localization: dict, *, injected_link: str, allowed_links: set[str]) -> dict:
    candidate = localization.get("suspected_link_id")
    status = localization.get("status")
    if status != "candidate_found" or not isinstance(candidate, str):
        return {"authorized": False, "reason": "localization_not_unique", "candidate": None}
    if candidate not in allowed_links:
        return {"authorized": False, "reason": "candidate_not_allowlisted", "candidate": candidate}
    if candidate != injected_link:
        return {"authorized": False, "reason": "candidate_disagrees_with_lab_interlock", "candidate": candidate}
    return {"authorized": True, "reason": "unique_candidate_matches_lab_interlock", "candidate": candidate}


def verify_recovery(baseline_loss: float, faulted_loss: float, recovered_loss: float, tolerance_pp: float) -> dict:
    if not all(0 <= x <= 100 for x in (baseline_loss, faulted_loss, recovered_loss, tolerance_pp)):
        raise ValueError("Loss percentages and tolerance must be within 0-100")
    fault_observed = faulted_loss - baseline_loss >= tolerance_pp
    recovered = recovered_loss <= baseline_loss + tolerance_pp
    return {
        "fault_observed": fault_observed,
        "recovery_within_tolerance": recovered,
        "passed": fault_observed and recovered,
        "note": "Threshold verification on measured ICMP loss; not statistical proof.",
    }
