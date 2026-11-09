# ns-3 Wi-Fi packet-level experiment (experimental)

This is a **separate, initial** ns-3 simulation for an 802.11a 5 GHz link.
It does not yet simulate Wi-Fi 2.4 GHz, a realistic access-point population,
interference, fading, or mobility. It does not control real network hardware.

## Run in a supported Linux ns-3 installation

1. Install/build ns-3 with `wifi`, `internet`, `mobility`, `applications`,
   and `flow-monitor` modules enabled.
2. Copy `simulator/ns3_wifi_5ghz.cc` into `<ns-3-root>/scratch/netfault-wifi.cc`.
3. From the ns-3 root, run:

```bash
./ns3 run "scratch/netfault-wifi --distance=25 --duration=20 --offeredMbps=5 --seed=1 --run=1"
./ns3 run "scratch/netfault-wifi --distance=100 --duration=20 --offeredMbps=5 --seed=1 --run=2"
```

The program prints one JSON object with transmitted/received UDP flow packets,
simulated packet-loss percentage, simulated throughput, and average one-way delay.
It uses constant-rate 802.11a at 24 Mbps, fixed AP and station positions, a
fixed 1200-byte UDP payload, and a 2-second warm-up. FlowMonitor counters are
aggregated after simulation. For more precise experimental work, filter
FlowMonitor records to the application 5-tuple and record the exact ns-3 version.

The current implementation is **not yet built or executed in an ns-3 runtime**.
Do not cite any accuracy or numerical result until the program compiles and
repeatable simulations have been completed.

## Experimental protocol

Use 20+ independent run numbers for each distance and offered load, record the
ns-3 release, OS, random seed, propagation settings, and build hash. Compare
packet loss, throughput, and latency across distance and load. Report dispersion
and confidence intervals; repeated trials must use different random streams.
Validate model assumptions before extrapolating to actual wireless networks.

Do not treat the analytical `/api/models/link-budget` output as a packet
simulation; it is a separate power-budget calculation.
