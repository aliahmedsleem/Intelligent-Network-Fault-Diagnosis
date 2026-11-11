#!/usr/bin/env python3
"""Four measured end-to-end ICMP paths in an isolated Mininet topology."""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

NODES = ["h1", "h2", "h3", "h4", "s1", "s2", "s3"]
EDGES = [
    ("h1-s1", "h1", "s1", 1),
    ("h2-s1", "h2", "s1", 1),
    ("s1-s2", "s1", "s2", 2),
    ("s2-s3", "s2", "s3", 2),
    ("h3-s3", "h3", "s3", 1),
    ("h4-s2", "h4", "s2", 1),
]
PAIRS = [("h1", "h4"), ("h2", "h3"), ("h1", "h2"), ("h3", "h4")]


def ping_loss(source, target, count):
    raw = source.cmd(f"ping -n -c {count} -W 2 {target.IP()}")
    match = re.search(r"(\d+) packets transmitted, (\d+)(?: packets)? received, ([\d.]+)% packet loss", raw)
    if match is None:
        raise RuntimeError(f"Cannot parse ping from {source.name} to {target.name}: {raw[-300:]}")
    return float(match.group(3))


def measure(hosts, count):
    return {(a, b): ping_loss(hosts[a], hosts[b], count) for a, b in PAIRS}


def run(loss, count):
    from mininet.net import Mininet
    from mininet.node import OVSSwitch, Controller
    from mininet.link import TCLink
    from mininet.log import setLogLevel

    setLogLevel("warning")
    net = Mininet(controller=Controller, switch=OVSSwitch, link=TCLink, build=False, autoSetMacs=True)
    try:
        net.addController("c0")
        hosts = {h: net.addHost(h) for h in ("h1", "h2", "h3", "h4")}
        switches = {s: net.addSwitch(s) for s in ("s1", "s2", "s3")}
        nodes = {**hosts, **switches}
        links = {}
        for link_id, a, b, delay in EDGES:
            links[link_id] = net.addLink(nodes[a], nodes[b], bw=100, delay=f"{delay}ms")
        net.build()
        net.start()
        time.sleep(2)
        baseline = measure(hosts, count)
        # Controlled fault on the inter-switch segment, with both directions impaired.
        faulty = links["s1-s2"]
        for interface in (faulty.intf1.name, faulty.intf2.name):
            subprocess.run(["tc", "qdisc", "replace", "dev", interface, "root",
                            "netem", "delay", "2ms", "loss", f"{loss}%"], check=True)
        time.sleep(1)
        observed = measure(hosts, count)
        return {
            "mode": "mininet_multi_probe_measured",
            "network": {
                "nodes": NODES,
                "links": [
                    {"id": lid, "source": a, "target": b, "medium": "ethernet",
                     "capacity_mbps": 100, "delay_ms": delay}
                    for lid, a, b, delay in EDGES
                ],
            },
            "probes": [
                {"source": a, "target": b, "baseline_loss_percent": baseline[a, b],
                 "observed_loss_percent": observed[a, b]}
                for a, b in PAIRS
            ],
            "ground_truth_link_id": "s1-s2",
            "threshold_pp": 5,
            "metadata": {"ping_count_per_path_per_phase": count,
                         "injected_loss_percent_per_direction": loss,
                         "note": "Real virtual-host ICMP measurements; not a radio/fiber physical model."},
        }
    finally:
        net.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loss", type=float, default=30)
    parser.add_argument("--ping-count", type=int, default=40)
    parser.add_argument("--output", type=Path, default=Path("/tmp/probe-batch.json"))
    args = parser.parse_args()
    if not 0 <= args.loss <= 100 or not 5 <= args.ping_count <= 1000:
        parser.error("loss must be 0-100 and ping-count must be 5-1000")
    if os.geteuid() != 0:
        parser.error("Run with sudo in a dedicated Linux VM")
    missing = [x for x in ("ovs-vsctl", "ping", "tc") if shutil.which(x) is None]
    if missing:
        parser.error("Missing dependencies: " + ", ".join(missing))
    result = run(args.loss, args.ping_count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
