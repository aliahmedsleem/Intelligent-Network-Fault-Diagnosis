from enum import Enum
from pydantic import BaseModel, Field, model_validator


class Medium(str, Enum):
    ethernet = "ethernet"
    fiber = "fiber"
    wifi_24 = "wifi_2_4"
    wifi_5 = "wifi_5"
    microwave = "microwave"


class Link(BaseModel):
    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    medium: Medium
    capacity_mbps: float = Field(gt=0, le=1_000_000)
    delay_ms: float = Field(ge=0, le=100_000)
    loss_percent: float = Field(default=0, ge=0, le=100)


class Network(BaseModel):
    nodes: list[str] = Field(min_length=2, max_length=200)
    links: list[Link] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_graph(self):
        if len(set(self.nodes)) != len(self.nodes):
            raise ValueError("Duplicate node IDs")
        ids = [link.id for link in self.links]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate link IDs")
        for link in self.links:
            if link.source not in self.nodes or link.target not in self.nodes:
                raise ValueError(f"Unknown endpoint in link {link.id}")
            if link.source == link.target:
                raise ValueError(f"Self-loop not supported: {link.id}")
        return self


class TrafficExperiment(BaseModel):
    network: Network
    source: str
    target: str
    offered_load_mbps: float = Field(gt=0, le=1_000_000)
    packet_size_bytes: int = Field(default=1200, ge=64, le=9000)


class FaultExperiment(TrafficExperiment):
    failed_link_id: str


class ExperimentResult(BaseModel):
    mode: str
    path: list[str]
    link_ids: list[str]
    connected: bool
    bottleneck_mbps: float
    offered_load_mbps: float
    estimated_throughput_mbps: float
    baseline_delay_ms: float
    estimated_loss_percent: float
    diagnosis: str
    note: str
