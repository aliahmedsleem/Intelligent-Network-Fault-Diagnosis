#!/usr/bin/env python3
"""Isolated Mininet fault -> remediation -> verification experiment.

Uses a fixed topology and allowlisted tc operations. Never execute through
an unauthenticated web endpoint or on a production host.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def loss_probe(source, destination, count):
    raw = source.cmd(f"ping -n -c {count} -W 2 {destination.IP()}")
    match = re.search(r"(\d+) packets transmitted, (\d+)(?: packets)? received, ([\d.]+)% packet loss", raw)
    if not match:
        raise RuntimeError("Cannot parse ICMP probe: " + raw[-300:])
    return {"sent": int(match.group(1)), "received": int(match.group(2)),
            "loss_percent": float(match.group(3))}


def qdisc(interface, loss):
    """Allowlisted netem settings on Mininet-owned interface names only."""
    if not re.fullmatch(r"s[12]-eth[0-9]+", interface):
        raise ValueError("Refusing unexpected interface: " + interface)
    if not 0 <= loss <= 100:
        raise ValueError("Invalid loss")
    subprocess.run(["tc", "qdisc", "replace", "dev", interface, "root",
                    "netem", "delay", "2ms", "loss", f"{loss}%"], check=True)


def run(loss, count, tolerance):
    from mininet.net import Mininet
    from mininet.node import OVSSwitch, Controller
    from mininet.link import TCLink
    from mininet.log import setLogLevel

    setLogLevel("warning")
    net = Mininet(controller=Controller, switch=OVSSwitch, link=TCLink,
                  build=False, autoSetMacs=True)
    actions = []
    try:
        net.addController("c0")
        h1 = net.addHost("h1", ip="10.21.0.1/24")
        h2 = net.addHost("h2", ip="10.21.0.2/24")
        s1 = net.addSwitch("s1")
        s2 = net.addSwitch("s2")
        net.addLink(h1, s1, bw=100, delay="1ms")
        middle = net.addLink(s1, s2, bw=100, delay="2ms")
        net.addLink(s2, h2, bw=100, delay="1ms")
        net.build()
        net.start()
        time.sleep(2)
        baseline = loss_probe(h1, h2, count)
        interfaces = [middle.intf1.name, middle.intf2.name]
        for name in interfaces:
            qdisc(name, loss)
        actions.append({"action": "inject_loss", "interfaces": interfaces,
                        "configured_loss_percent": loss})
        faulted = loss_probe(h1, h2, count)
        # Explicitly restore zero impairment on the controlled middle link.
        for name in interfaces:
            qdisc(name, 0)
        actions.append({"action": "remove_injected_loss", "interfaces": interfaces,
                        "configured_loss_percent": 0})
        recovered = loss_probe(h1, h2, count)
        verified = recovered["loss_percent"] <= baseline["loss_percent"] + tolerance
        # Rollback here means restoring the known baseline (zero injected loss)
        # if verification fails; it does NOT re-inject the fault.
        if not verified:
            for name in interfaces:
                qdisc(name, 0)
            actions.append({"action": "restore_safe_baseline_after_failed_verification",
                            "interfaces": interfaces})
        return {
            "mode": "mininet_remediation_measured",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "topology": "h1-s1-s2-h2",
            "ground_truth": {"injected_link": "s1-s2", "loss_percent": loss},
            "baseline": baseline,
            "faulted": faulted,
            "recovered": recovered,
            "verification": {"passed": verified, "loss_tolerance_pp": tolerance,
                             "criterion": "recovered loss <= baseline loss + tolerance"},
            "actions": actions,
            "remediation_type": "remove_known_injected_impairment",
            "limitations": [
                "Controlled impairment reversal, not autonomous diagnosis or generic repair.",
                "Small ICMP samples may be noisy; repeat trials before statistical claims.",
                "Root qdisc replacement does not restore original TCLink bandwidth settings.",
                "Failed verification restores the safe zero-loss configuration, not the fault.",
            ],
        }
    finally:
        net.stop()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--loss", type=float, default=40)
    p.add_argument("--ping-count", type=int, default=50)
    p.add_argument("--tolerance", type=float, default=5)
    p.add_argument("--output", type=Path, default=Path("/tmp/remediation-run.json"))
    a = p.parse_args()
    if not 0 <= a.loss <= 100 or not 10 <= a.ping_count <= 1000 or not 0 <= a.tolerance <= 100:
        p.error("Invalid bounds for loss, ping-count or tolerance")
    if os.geteuid() != 0:
        p.error("Use sudo in a dedicated Mininet VM")
    missing = [x for x in ("ovs-vsctl", "ping", "tc") if shutil.which(x) is None]
    if missing:
        p.error("Missing: " + ", ".join(missing))
    result = run(a.loss, a.ping_count, a.tolerance)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {a.output}")


if __name__ == "__main__":
    main()
