# Measured Mininet data pipeline

The Mininet script runs **on an isolated Ubuntu VM** and exports JSON. The FastAPI backend runs on Windows or Linux and analyzes the saved JSON through `POST /api/measurements/analyze`. This architecture intentionally does not run root shell commands from an HTTP request.

1. Run `sudo python3 simulator/mininet_experiment.py --output /tmp/network-fault-run.json` in Ubuntu after installing prerequisites.
2. Transfer the generated JSON file to the machine running the frontend, or access it locally.
3. Open the dashboard's **Measurements** section, choose the JSON file and click **Analyze measurements**.
4. The dashboard displays actual imported ICMP/TCP measurements, computed deltas, quality flags and evidence.

**Boundaries:** The endpoint accepts JSON data supplied by the user, not authenticated provenance; measurements are genuine only if produced by the Mininet experiment. Fault identity is injection ground truth and is never passed off as an AI prediction. Evidence thresholds are a transparent baseline, not statistically validated fault classification. Missing data remains missing. No automatic remediation is attempted.

## Validation plan
Repeat each experiment at least 20 times with randomized order, compare baseline vs fault, report means and confidence intervals, and isolate test labels from any trained model. Record kernel, Mininet/OVS, iperf3 versions and test seeds where applicable.
