# Closed-loop experiment inspection

1. Run `sudo python3 simulator/mininet_closed_loop.py --output /tmp/closed-loop.json` in a dedicated Ubuntu Mininet VM with the backend dependencies installed.
2. Transfer the resulting JSON file to your browser machine.
3. In the dashboard, select the **Closed Loop** section and import the JSON file.
4. The frontend posts it to `POST /api/lifecycle/inspect`, which recomputes localization independently and audits reported authorization and recovery measurements.

This endpoint **does not run** Mininet or execute repairs. A consistent result only means the uploaded data agrees with the model's contract; it does **not** authenticate the file, prove that commands ran, or statistically validate the remediation.

The laboratory uses a fixed tree topology and requires both crossing probe paths to exhibit increased packet loss followed by recovery within five percentage points of baseline. If the script's own verification tolerance is changed from the default, this audit's fixed 5 pp policy must be updated before treating the artifact as consistent.
