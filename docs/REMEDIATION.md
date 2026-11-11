# Controlled fault reversal and measured verification

Run in a **dedicated Ubuntu Mininet VM**, not on a production host:

```bash
sudo python3 simulator/mininet_remediation.py --loss 40 --ping-count 50 --output /tmp/remediation-run.json
```

This runs real ICMP probes in three phases: baseline, fault-injected, and after removal of the known injected impairment. A bounded, allowlisted `tc netem` action changes only the script's fixed Mininet switch interfaces. If recovery does not meet the baseline loss + tolerance criterion, the script reapplies the safe zero-loss impairment setting. The topology is torn down in `finally`.

`POST /api/remediation/analyze` validates imported results and independently checks whether the reported pass/fail agrees with measured packet loss. The API **does not** run `sudo`, `tc`, Mininet, or any system command.

Important: This is **controlled remediation of a known injected fault**, not automatic repair of arbitrary unknown faults. Restoring zero impairment after failed verification is a safe-state action, not a rollback to the injected fault. The root qdisc replacement also changes the original TCLink shaping configuration; exact qdisc restoration is a future improvement. For scientific conclusions, repeat experiments with randomized ordering and report uncertainty.
