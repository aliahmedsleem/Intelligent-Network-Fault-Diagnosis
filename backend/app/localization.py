"""Topology-aware link localization from independent end-to-end probe evidence.

The model assumes undirected links and known probe paths. It never reads
injected fault labels when ranking candidates. Scores are transparent heuristic
evidence, not calibrated probabilities.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, model_validator
from .models import Network
from .engine import route


class Probe(BaseModel):
    source: str
    target: str
    baseline_loss_percent: float = Field(ge=0, le=100)
    observed_loss_percent: float = Field(ge=0, le=100)
    baseline_rtt_ms: float | None = Field(default=None, ge=0)
    observed_rtt_ms: float | None = Field(default=None, ge=0)


class LocalizationRequest(BaseModel):
    network: Network
    probes: list[Probe] = Field(min_length=2, max_length=200)
    loss_threshold_pp: float = Field(default=5, ge=0.1, le=100)

    @model_validator(mode="after")
    def validate_probes(self):
        for probe in self.probes:
            if probe.source not in self.network.nodes or probe.target not in self.network.nodes:
                raise ValueError("Probe endpoint not in network")
            if probe.source == probe.target:
                raise ValueError("Probe endpoints must differ")
        return self


def localize(request: LocalizationRequest) -> dict:
    paths = []
    for probe in request.probes:
        nodes, link_ids, _ = route(request.network, probe.source, probe.target)
        if not link_ids:
            raise ValueError(f"No baseline path for probe {probe.source} -> {probe.target}")
        delta = probe.observed_loss_percent - probe.baseline_loss_percent
        paths.append({
            "source": probe.source, "target": probe.target, "path": nodes,
            "link_ids": link_ids, "loss_delta_pp": round(delta, 4),
            "degraded": delta >= request.loss_threshold_pp,
        })
    degraded = [p for p in paths if p["degraded"]]
    healthy = [p for p in paths if not p["degraded"]]
    rankings = []
    for link in request.network.links:
        impacted = sum(link.id in p["link_ids"] for p in degraded)
        contradicted = sum(link.id in p["link_ids"] for p in healthy)
        # Fraction of degraded paths explained, minus healthy path contradictions.
        # No fault ground-truth labels are accessed here.
        score = (impacted / len(degraded) if degraded else 0) - (
            contradicted / len(healthy) if healthy else 0
        )
        rankings.append({
            "link_id": link.id, "source": link.source, "target": link.target,
            "score": round(score, 4), "degraded_paths_covered": impacted,
            "healthy_paths_contradicted": contradicted,
        })
    rankings.sort(key=lambda x: (-x["score"], -x["degraded_paths_covered"], x["link_id"]))
    positive = [r for r in rankings if r["score"] > 0 and r["degraded_paths_covered"] > 0]
    top = positive[0] if positive else None
    tied = [r["link_id"] for r in positive if r["score"] == top["score"]] if top else []
    return {
        "mode": "path_evidence_localization",
        "status": "ambiguous" if len(tied) > 1 else ("candidate_found" if top else "insufficient_evidence"),
        "suspected_link_id": top["link_id"] if len(tied) == 1 else None,
        "tied_candidates": tied,
        "rankings": rankings,
        "probes": paths,
        "method": "unweighted path coverage minus healthy-path contradiction",
        "limitations": [
            "Heuristic scores are not probabilities.",
            "Assumes static shortest-delay paths and undirected links.",
            "Multiple simultaneous faults, ECMP and routing changes are not modeled.",
            "At least two independent probe paths are recommended; ambiguous ties are reported.",
        ],
    }
