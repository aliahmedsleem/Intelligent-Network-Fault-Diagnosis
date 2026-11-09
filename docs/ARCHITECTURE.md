# Architecture and scientific boundaries

## Development strategy
Windows 11 is the user's workstation. FastAPI and React run natively. Linux network namespaces, Mininet/OVS, and ns-3 should execute within a configured WSL2 Ubuntu distribution or an isolated Ubuntu VM. WSL2 is not guaranteed to support all ns-3 integration or realtime/TAP cases; validate each adapter independently.

## Components
1. **API**: FastAPI validates topology and exposes experiment endpoints.
2. **Analytical baseline (implemented)**: deterministic shortest-delay path; bottleneck throughput and independent link-loss composition. Explicitly labeled `analytical_estimate`.
3. **Packet-level wired adapter (planned)**: isolated Mininet + OVS environment with iperf3, ping, tc netem, tcpdump. Collect measured timestamps, packet loss, throughput and traces.
4. **Wireless adapter (planned)**: ns-3 Wi-Fi 2.4 / 5 GHz experiments with specified PHY/MAC/channel and reproducible seeds. ns-3 results are simulated, not hardware measurements.
5. **Fiber / microwave (planned)**: transparent ITU-T and ITU-R inspired link budgets and propagation equations; convert modeled impairments into reproducible virtual-network experiments. Validate each model in controlled unit tests.
6. **Fault analysis (planned)**: topology-aware localization; do not use the injected fault label as a predicted diagnosis. Ground truth remains isolated for scoring.
7. **Remediation (planned)**: supervised bounded actions in virtual networks only, before/after metrics and rollback on regression.
8. **Frontend (planned)**: React + TypeScript topology designer and disciplined instrumentation UI.

## Validation principles
Record simulator/version, OS/kernel, topology, traffic generator, RNG seed, baseline measurements, perturbation, ground-truth event, predictions, remediation, repeated trials and statistical summaries. Never mix analytical estimates, simulated metrics and measured container traffic as if equivalent.

## Current limitations
The first release implements ONLY an analytical baseline and API, not actual packet-level or wireless simulation. The baseline assumes undirected links, shortest delay, no queueing or routing protocols, independent link losses, and approximate goodput. It does not account for medium-specific attenuation. All values are estimates.
