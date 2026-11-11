# Integrated measured diagnosis → gated repair → verification

This is a **dedicated Linux Mininet lab**, not a production network automation agent.

```bash
sudo apt install -y mininet openvswitch-switch iputils-ping iproute2
sudo python3 simulator/mininet_closed_loop.py --loss 40 --ping-count 50 --output /tmp/closed-loop.json
```

The experiment creates a fixed seven-node topology, measures four end-to-end paths, injects impairment into the known lab link, measures again, and calls the same backend localization algorithm as the API. The algorithm does **not** receive the injected fault label.

The action is allowed only if the algorithm uniquely identifies the exact known lab link and that link is allowlisted. This second equality check is a safety interlock and must not be interpreted as improved diagnostic accuracy. If the check fails, the script **does not attempt repair**; it still removes the injected impairment during mandatory lab cleanup.

After a permitted action, new ICMP probes verify that the observed fault had sufficient impact and the recovered loss is within a specified tolerance of baseline. On failed verification, the script restores the safe zero-impairment setting and records failure; it does not reintroduce the injected fault.

Limitations: fixed single-link scenario, sequential probes, no Wi-Fi PHY or fiber optics physics, no autonomous unknown-fault remediation, no proof of diagnosis accuracy. Mininet's root qdisc replacement changes original TCLink shaping; this script restores safe zero-loss netem, not exact original qdisc state. The VM teardown occurs even after exceptions.

Use `pytest simulator/tests` for policy unit tests (no Mininet required). Real Mininet runs require root in an isolated VM and are not exercised by those unit tests.
