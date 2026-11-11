"""Validate measured remediation reports without executing privileged actions."""
from __future__ import annotations
from pydantic import BaseModel, Field, model_validator


class Ping(BaseModel):
    sent: int = Field(ge=1, le=100000)
    received: int = Field(ge=0, le=100000)
    loss_percent: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def counts(self):
        if self.received > self.sent:
            raise ValueError("received > sent")
        calculated = 100 * (self.sent - self.received) / self.sent
        if abs(calculated - self.loss_percent) > 0.11:
            raise ValueError("loss percent inconsistent with counts")
        return self


class Verification(BaseModel):
    passed: bool
    loss_tolerance_pp: float = Field(ge=0, le=100)
    criterion: str


class RemediationReport(BaseModel):
    mode: str
    topology: str
    baseline: Ping
    faulted: Ping
    recovered: Ping
    verification: Verification
    remediation_type: str

    @model_validator(mode="after")
    def contract(self):
        if self.mode != "mininet_remediation_measured":
            raise ValueError("Wrong experiment mode")
        if self.remediation_type != "remove_known_injected_impairment":
            raise ValueError("Unsupported remediation type")
        expected = self.recovered.loss_percent <= (
            self.baseline.loss_percent + self.verification.loss_tolerance_pp
        )
        if expected != self.verification.passed:
            raise ValueError("Verification result does not match measured losses")
        return self


def analyze_remediation(report: RemediationReport) -> dict:
    fault_increase = report.faulted.loss_percent - report.baseline.loss_percent
    recovery_gain = report.faulted.loss_percent - report.recovered.loss_percent
    return {
        "mode": report.mode,
        "status": "verified_recovery" if report.verification.passed else "verification_failed",
        "measurements": {
            "baseline_loss_percent": report.baseline.loss_percent,
            "faulted_loss_percent": report.faulted.loss_percent,
            "recovered_loss_percent": report.recovered.loss_percent,
            "fault_loss_increase_pp": round(fault_increase, 4),
            "recovery_gain_pp": round(recovery_gain, 4),
        },
        "verification_passed": report.verification.passed,
        "evidence": "Measured ICMP probes; a passing threshold does not prove permanent recovery.",
        "scope": "Controlled reversal of an injected Mininet impairment; not autonomous remediation.",
    }
