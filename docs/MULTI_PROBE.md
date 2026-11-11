# Multi-probe measured localization pipeline

This pipeline separates **measured traffic**, **link inference**, and **ground-truth evaluation**.

- Ubuntu Mininet experiment `simulator/mininet_multi_probe.py` creates a seven-node virtual topology, sends ICMP probes over four source/destination pairs before and after fault injection, and exports a JSON batch.
- FastAPI endpoint `POST /api/localization/probe-batch` validates the batch, runs the explainable path-evidence localization engine, then compares its unique Top-1 candidate with the withheld injected link ID.
- The fault ID is not passed to `localize()`. Scores are heuristics, not confidence probabilities.

Run inside an isolated Ubuntu VM with Mininet, OVS, ping, tc:

```bash
sudo python3 simulator/mininet_multi_probe.py --output /tmp/probe-batch.json
```

Send the JSON body to `/api/localization/probe-batch` from a local client. Never run this privileged script through a public HTTP endpoint.

**Scientific limitations:** Single fault, known static topology, static shortest-delay routes, sequential ICMP measurements, no radio PHY model. This is a first measured end-to-end experiment, not a validated AI diagnosis system. Run repeated experiments, randomize the fault and probe order, report ambiguity, false-positive rates, Top-1 accuracy and confidence intervals before claiming performance.
