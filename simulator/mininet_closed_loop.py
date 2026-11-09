#!/usr/bin/env python3
"""Measured Mininet closed-loop lab, with inference separate from safety interlock."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "simulator"))
from app.models import Network
from app.localization import LocalizationRequest, Probe, localize
from lab_policy import decide_remediation, verify_recovery
from mininet_multi_probe import EDGES, NODES, PAIRS, measure


def set_loss(interfaces: list[str], loss: float):
    import re
    for interface in interfaces:
        if not re.fullmatch(r"s[123]-eth[0-9]+", interface):
            raise ValueError("Unsafe interface name")
        subprocess.run(["tc", "qdisc", "replace", "dev", interface, "root",
                        "netem", "delay", "2ms", "loss", f"{loss}%"], check=True)


def run(loss: float, count: int, tolerance: float):
    from mininet.net import Mininet
    from mininet.node import OVSSwitch, Controller
    from mininet.link import TCLink
    from mininet.log import setLogLevel

    setLogLevel("warning")
    net = Mininet(controller=Controller, switch=OVSSwitch, link=TCLink,
                  build=False, autoSetMacs=True)
    injected = False
    interfaces: list[str] = []
    actions = []
    try:
        net.addController("c0")
        hosts = {name: net.addHost(name) for name in ("h1", "h2", "h3", "h4")}
        switches = {name: net.addSwitch(name) for name in ("s1", "s2", "s3")}
        nodes = {**hosts, **switches}
        links = {}
        for link_id, a, b, delay in EDGES:
            links[link_id] = net.addLink(nodes[a], nodes[b], bw=100, delay=f"{delay}ms")
        net.build()
        net.start()
        time.sleep(2)
        baseline = measure(hosts, count)
        fault_link = "s1-s2"
        middle = links[fault_link]
        interfaces = [middle.intf1.name, middle.intf2.name]
        injected = True  # ensure cleanup even if injection fails halfway
        set_loss(interfaces, loss)
        actions.append({"type": "inject_fault", "target": fault_link, "loss_percent": loss})
        time.sleep(1)
        observed = measure(hosts, count)
        network = Network.model_validate({
            "nodes": NODES,
            "links": [
                {"id": link_id, "source": a, "target": b, "medium": "ethernet",
                 "capacity_mbps": 100, "delay_ms": delay}
                for link_id, a, b, delay in EDGES
            ],
        })
        probes = [
            Probe(source=a, target=b, baseline_loss_percent=baseline[a, b],
                  observed_loss_percent=observed[a, b])
            for a, b in PAIRS
        ]
        inference = localize(LocalizationRequest(network=network, probes=probes))
        decision = decide_remediation(
            inference, injected_link=fault_link, allowed_links={fault_link}
        )
        recovered = None
        verification = {"status": "not_run"}
        if decision["authorized"]:
            set_loss(interfaces, 0)
            actions.append({"type": "remove_injected_loss", "target": fault_link})
            time.sleep(1)
            recovered = measure(hosts, count)
            checks = [
                verify_recovery(baseline[p], observed[p], recovered[p], tolerance)
                for p in PAIRS if fault_link in (
                    # Unique paths on the fixed tree: h1->h4 and h2->h3 cross s1-s2.
                    ["s1-s2"] if p in (("h1", "h4"), ("h2", "h3")) else []
                )
            ]
            verification = {
                "status": "passed" if checks and all(c["passed"] for c in checks) else "failed",
                "path_checks": checks,
            }
            if verification["status"] == "failed":
                set_loss(interfaces, 0)
                actions.append({"type": "restore_safe_baseline", "target": fault_link})
        else:
            verification = {"status": "blocked", "reason": decision["reason"]}
        return {
            "mode": "mininet_closed_loop_measured",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "network": network.model_dump(mode="json"),
            "probes": [
                {"source": a, "target": b, "baseline_loss_percent": baseline[a, b],
                 "observed_loss_percent": observed[a, b],
                 "recovered_loss_percent": recovered[a, b] if recovered is not None else None}
                for a, b in PAIRS
            ],
            "inference": inference,
            "execution_policy": decision,
            "actions": actions,
            "verification": verification,
            "ground_truth_for_evaluation_only": {
                "fault_link": fault_link,
                "top1_correct": inference["suspected_link_id"] == fault_link
                if inference["status"] == "candidate_found" else False,
            },
            "limitations": [
                "Known-fault safety interlock, not general autonomous remediation.",
                "Fixed topology and one injected impairment; results not yet statistically validated.",
                "Safe zero-loss qdisc does not restore original TCLink bandwidth shaping.",
            ],
        }
    finally:
        if injected and interfaces:
            try:
                set_loss(interfaces, 0)
            except Exception as exc:
                print(f"WARNING: safe-state cleanup failed: {exc}", file=sys.stderr)
        net.stop()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--loss", type=float, default=40)
    p.add_argument("--ping-count", type=int, default=50)
    p.add_argument("--tolerance", type=float, default=5)
    p.add_argument("--output", type=Path, default=Path("/tmp/closed-loop.json"))
    args = p.parse_args()
    if not 0 <= args.loss <= 100 or not 10 <= args.ping_count <= 1000 or not 0 <= args.tolerance <= 100:
        p.error("Invalid experiment bounds")
    if os.geteuid() != 0:
        p.error("Run with sudo inside a dedicated Ubuntu Mininet VM")
    missing = [cmd for cmd in ("ovs-vsctl", "ping", "tc") if shutil.which(cmd) is None]
    if missing:
        p.error("Missing commands: " + ", ".join(missing))
    result = run(args.loss, args.ping_count, args.tolerance)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
