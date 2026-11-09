"""Transparent analytical baseline.

This is NOT a packet-level simulator. It evaluates a shortest-delay path and
simple capacity/loss assumptions. Mininet and ns-3 adapters are separate
future milestones. Outputs must never be presented as measured traffic.
"""
from __future__ import annotations

import heapq
from .models import Network, TrafficExperiment, FaultExperiment, ExperimentResult


def route(network: Network, source: str, target: str, excluded: set[str] | None = None):
    if source not in network.nodes or target not in network.nodes:
        raise ValueError("Source or target is not in the network")
    excluded = excluded or set()
    graph: dict[str, list[tuple[str, float, str]]] = {n: [] for n in network.nodes}
    for link in network.links:
        if link.id in excluded or link.loss_percent == 100:
            continue
        graph[link.source].append((link.target, link.delay_ms, link.id))
        graph[link.target].append((link.source, link.delay_ms, link.id))
    heap = [(0.0, source, (source,), ())]
    best: dict[str, float] = {}
    while heap:
        delay, node, path, link_ids = heapq.heappop(heap)
        if node in best:
            continue
        best[node] = delay
        if node == target:
            return list(path), list(link_ids), delay
        for neighbor, cost, link_id in graph[node]:
            if neighbor not in best:
                heapq.heappush(heap, (delay + cost, neighbor, path + (neighbor,), link_ids + (link_id,)))
    return [], [], 0.0


def evaluate(experiment: TrafficExperiment, excluded: set[str] | None = None) -> ExperimentResult:
    nodes, ids, delay = route(experiment.network, experiment.source, experiment.target, excluded)
    links = {link.id: link for link in experiment.network.links}
    if not nodes:
        return ExperimentResult(
            mode="analytical_estimate", path=[], link_ids=[], connected=False,
            bottleneck_mbps=0, offered_load_mbps=experiment.offered_load_mbps,
            estimated_throughput_mbps=0, baseline_delay_ms=0,
            estimated_loss_percent=100, diagnosis="no_route",
            note="Analytical graph estimate only; not a real packet measurement.",
        )
    bottleneck = min(links[i].capacity_mbps for i in ids)
    survival = 1.0
    for link_id in ids:
        survival *= 1 - links[link_id].loss_percent / 100
    loss = (1 - survival) * 100
    throughput = min(experiment.offered_load_mbps, bottleneck) * survival
    diagnosis = "capacity_limited" if experiment.offered_load_mbps > bottleneck else ("link_loss" if loss > 0 else "normal")
    return ExperimentResult(
        mode="analytical_estimate", path=nodes, link_ids=ids, connected=True,
        bottleneck_mbps=bottleneck, offered_load_mbps=experiment.offered_load_mbps,
        estimated_throughput_mbps=round(throughput, 5),
        baseline_delay_ms=round(delay, 5),
        estimated_loss_percent=round(loss, 5),
        diagnosis=diagnosis,
        note="Deterministic analytical estimate (no queueing, MAC, or packet emulation).",
    )


def diagnose_fault(experiment: FaultExperiment) -> dict:
    if experiment.failed_link_id not in {link.id for link in experiment.network.links}:
        raise ValueError("Failed link is not in the network")
    baseline = evaluate(experiment)
    after = evaluate(experiment, {experiment.failed_link_id})
    changed = baseline.path != after.path or baseline.connected != after.connected
    return {
        "mode": "analytical_estimate",
        "injected_fault": {"type": "link_down", "link_id": experiment.failed_link_id},
        "before": baseline.model_dump(),
        "after": after.model_dump(),
        "route_changed": changed,
        "localization": {
            "known_injected_link_id": experiment.failed_link_id,
            "warning": "This is fault injection ground truth, not AI localization.",
        },
    }
