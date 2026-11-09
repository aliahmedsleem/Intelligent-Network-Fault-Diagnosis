"""Read-only audit of ns-3 packet-level UDP experiment output.

This does not run ns-3, and does not imply measurements from physical hardware.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class Ns3WifiRun(BaseModel):
    mode: str
    standard: str
    seed: int = Field(ge=1)
    run: int = Field(ge=1)
    distance_m: float = Field(gt=0, le=1000)
    duration_s: float = Field(ge=2, le=300)
    offered_mbps: float = Field(gt=0, le=1000)
    tx_packets: int = Field(ge=0)
    rx_packets: int = Field(ge=0)
    packet_loss_percent: float = Field(ge=0, le=100)
    throughput_mbps: float = Field(ge=0)
    mean_delay_ms: float = Field(ge=0)

    @model_validator(mode="after")
    def check_identity(self):
        if self.mode != "ns3_wifi_packet_simulation":
            raise ValueError("Expected ns3_wifi_packet_simulation")
        if self.standard != "802.11a_5ghz":
            raise ValueError("Unsupported ns-3 experiment standard")
        return self


def inspect_ns3_run(data: Ns3WifiRun) -> dict:
    flags = []
    if data.rx_packets > data.tx_packets:
        flags.append("received_packets_exceed_transmitted")
    if data.tx_packets == 0:
        flags.append("no_transmitted_packets")
    else:
        expected_loss = 100 * (data.tx_packets - min(data.rx_packets, data.tx_packets)) / data.tx_packets
        if abs(expected_loss - data.packet_loss_percent) > 0.011:
            flags.append("reported_loss_disagrees_with_packet_counts")
    # 1200-byte application payload is used in the current ns-3 program;
    # FlowMonitor counts IP bytes including headers, so do not derive a
    # fake throughput estimate from packet counts.
    if data.throughput_mbps > data.offered_mbps * 1.2:
        flags.append("throughput_above_offered_rate_check_units")
    return {
        "mode": "ns3_wifi_result_audit",
        "audit_status": "consistent" if not flags else "inconsistent",
        "quality_flags": flags,
        "experiment": data.model_dump(),
        "caveats": [
            "Checks numerical consistency only; does not authenticate ns-3 execution.",
            "Packet-level virtual Wi-Fi simulation, not a physical radio measurement.",
            "This does not establish scientific validity of propagation or interference assumptions.",
        ],
    }
