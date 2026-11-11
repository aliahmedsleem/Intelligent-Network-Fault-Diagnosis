#!/usr/bin/env python3
"""Measured packet-level impairment experiment in a dedicated Linux lab.

Mininet hosts generate actual ICMP and TCP traffic. No fabricated metrics.
Requires root, Mininet, OVS, iperf3, ping, and tc.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def dependencies():
    missing = [name for name in ("mn", "ovs-vsctl", "iperf3", "ping", "tc") if shutil.which(name) is None]
    if missing:
        raise RuntimeError("Missing commands: " + ", ".join(missing))
    if os.geteuid() != 0:
        raise PermissionError("Run inside an isolated Linux lab with sudo/root.")


def ping_measure(source, target: str, count: int):
    command = f"ping -n -c {count} -W 2 {target}"
    output = source.cmd(command)
    packet = re.search(r"(\d+) packets transmitted, (\d+)(?: packets)? received, ([\d.]+)% packet loss", output)
    rtt = re.search(r"(?:rtt|round-trip) min/avg/max/(?:mdev|stddev) = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", output)
    return {
        "command": command,
        "packets_sent": int(packet.group(1)) if packet else None,
        "packets_received": int(packet.group(2)) if packet else None,
        "loss_percent": float(packet.group(3)) if packet else None,
        "rtt_avg_ms": float(rtt.group(2)) if rtt else None,
        "raw": output.strip(),
        "parse_ok": packet is not None,
    }


def iperf_measure(server, client, seconds: int, port: int):
    server.cmd(f"iperf3 -s -1 -p {port} -D --logfile /tmp/nflab-iperf-server-{port}.log")
    time.sleep(1)
    output = client.cmd(f"iperf3 -c {server.IP()} -p {port} -t {seconds} -J")
    try:
        parsed = json.loads(output)
        summary = parsed.get("end", {}).get("sum_received", {})
        bits = summary.get("bits_per_second")
        return {
            "throughput_mbps": round(bits / 1e6, 4) if isinstance(bits, (int, float)) else None,
            "error": parsed.get("error"),
            "raw": parsed,
        }
    except json.JSONDecodeError:
        return {"throughput_mbps": None, "error": "Could not parse iperf3 JSON", "raw": output}


def run(loss: float, count: int, seconds: int):
    from mininet.net import Mininet
    from mininet.node import OVSSwitch, Controller
    from mininet.link import TCLink
    from mininet.log import setLogLevel

    setLogLevel("warning")
    net = Mininet(controller=Controller, switch=OVSSwitch, link=TCLink, build=False, autoSetMacs=True)
    try:
        net.addController("c0")
        h1 = net.addHost("h1", ip="10.20.0.1/24")
        h2 = net.addHost("h2", ip="10.20.0.2/24")
        s1 = net.addSwitch("s1")
        s2 = net.addSwitch("s2")
        net.addLink(h1, s1, bw=100, delay="1ms")
        middle = net.addLink(s1, s2, bw=100, delay="2ms")
        net.addLink(s2, h2, bw=100, delay="1ms")
        net.build()
        net.start()
        time.sleep(2)
        before = {
            "ping": ping_measure(h1, h2.IP(), count),
            "tcp": iperf_measure(h2, h1, seconds, 5201),
        }
        interfaces = [middle.intf1.name, middle.intf2.name]
        for intf in (middle.intf1, middle.intf2):
            # Replace the link's root qdisc to inject controlled loss.
            # The prior TCLink bandwidth/delay qdisc may be replaced by this command.
            subprocess.run(["tc", "qdisc", "replace", "dev", intf.name, "root", "netem", "delay", "2ms", "loss", f"{loss}%"], check=True)
        time.sleep(1)
        after = {
            "ping": ping_measure(h1, h2.IP(), count),
            "tcp": iperf_measure(h2, h1, seconds, 5202),
        }
        return {
            "mode": "mininet_measured",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "kernel": platform.release(),
            "topology": "h1-s1-s2-h2",
            "fault": {"type": "netem_packet_loss", "target_link": "s1-s2", "interfaces": interfaces, "configured_loss_percent_each_direction": loss},
            "experiment": {"ping_count": count, "iperf_seconds": seconds},
            "before": before,
            "after": after,
            "limitations": [
                "Virtual Linux packet measurements, not physical radio or fiber measurements.",
                "TCP throughput is environment dependent.",
                "The fault link is known ground truth; no localization algorithm is claimed.",
                "The qdisc replacement changes the original TCLink bandwidth/delay configuration.",
            ],
        }
    finally:
        net.stop()


def main():
    parser = argparse.ArgumentParser(description="Measured Mininet link impairment experiment")
    parser.add_argument("--loss", type=float, default=20.0)
    parser.add_argument("--ping-count", type=int, default=20)
    parser.add_argument("--iperf-seconds", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("/tmp/network-fault-run.json"))
    args = parser.parse_args()
    if not 0 <= args.loss <= 100 or not 1 <= args.ping_count <= 1000 or not 1 <= args.iperf_seconds <= 120:
        parser.error("loss must be 0-100, ping-count 1-1000, iperf-seconds 1-120")
    dependencies()
    result = run(args.loss, args.ping_count, args.iperf_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved measured experiment to {args.output}")


if __name__ == "__main__":
    main()
