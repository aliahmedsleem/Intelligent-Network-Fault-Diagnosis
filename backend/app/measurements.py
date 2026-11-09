"""Validation and analysis of *imported* Mininet measurements.

Never execute arbitrary uploaded commands or treat experiment ground truth as
predicted localization. This module accepts a bounded JSON result and reports
measured changes with explicit evidence/quality flags.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PingSample(BaseModel):
    model_config = ConfigDict(extra="ignore")
    packets_sent: int | None = Field(default=None, ge=0, le=100000)
    packets_received: int | None = Field(default=None, ge=0, le=100000)
    loss_percent: float | None = Field(default=None, ge=0, le=100)
    rtt_avg_ms: float | None = Field(default=None, ge=0, le=1e6)
    parse_ok: bool = False

    @model_validator(mode="after")
    def counts_consistent(self):
        if self.packets_sent is not None and self.packets_received is not None:
            if self.packets_received > self.packets_sent:
                raise ValueError("Received packets cannot exceed sent packets")
        return self


class TcpSample(BaseModel):
    model_config = ConfigDict(extra="ignore")
    throughput_mbps: float | None = Field(default=None, ge=0, le=1e8)
    error: str | None = Field(default=None, max_length=500)


class Phase(BaseModel):
    ping: PingSample
    tcp: TcpSample


class Fault(BaseModel):
    type: str = Field(min_length=1, max_length=100)
    target_link: str = Field(min_length=1, max_length=100)
    configured_loss_percent_each_direction: float = Field(ge=0, le=100)


class MeasuredRun(BaseModel):
    mode: str
    timestamp_utc: str = Field(max_length=100)
    topology: str = Field(max_length=300)
    fault: Fault
    before: Phase
    after: Phase

    @model_validator(mode="after")
    def measured_only(self):
        if self.mode != "mininet_measured":
            raise ValueError("Only mininet_measured experiments may be imported")
        return self


def analyze(run: MeasuredRun) -> dict:
    b, a = run.before, run.after
    flags: list[str] = []
    if not b.ping.parse_ok or not a.ping.parse_ok:
        flags.append("ping_parse_incomplete")
    if b.tcp.error or a.tcp.error:
        flags.append("iperf_error")
    if any(x is None for x in (b.ping.loss_percent, a.ping.loss_percent, b.tcp.throughput_mbps, a.tcp.throughput_mbps)):
        flags.append("missing_measurements")
    before_tp, after_tp = b.tcp.throughput_mbps, a.tcp.throughput_mbps
    before_loss, after_loss = b.ping.loss_percent, a.ping.loss_percent
    throughput_delta = round(after_tp - before_tp, 4) if before_tp is not None and after_tp is not None else None
    loss_delta = round(after_loss - before_loss, 4) if before_loss is not None and after_loss is not None else None
    evidence = []
    if throughput_delta is not None and throughput_delta < -max(1, before_tp * .15):
        evidence.append("tcp_throughput_degraded")
    if loss_delta is not None and loss_delta >= 5:
        evidence.append("icmp_packet_loss_increased")
    if not flags and not evidence:
        evidence.append("no_significant_degradation_by_simple_thresholds")
    return {
        "mode": "mininet_measured",
        "timestamp_utc": run.timestamp_utc,
        "topology": run.topology,
        "ground_truth": {"fault_link": run.fault.target_link, "configured_loss_percent": run.fault.configured_loss_percent_each_direction},
        "measurements": {
            "before": {"throughput_mbps": before_tp, "loss_percent": before_loss, "rtt_avg_ms": b.ping.rtt_avg_ms},
            "after": {"throughput_mbps": after_tp, "loss_percent": after_loss, "rtt_avg_ms": a.ping.rtt_avg_ms},
            "throughput_change_mbps": throughput_delta,
            "loss_change_percentage_points": loss_delta,
        },
        "evidence": evidence,
        "quality_flags": flags,
        "localization": {"status": "not_performed", "note": "Known injected fault is ground truth only, not an inferred root cause."},
        "method": "deterministic threshold screening of real Mininet measurements; not machine learning",
    }
