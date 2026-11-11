# Mininet wired-network laboratory

Runs on **Ubuntu Linux with Mininet, Open vSwitch, iperf3, ping and tc**. Use an Ubuntu VM for the most predictable setup. WSL2 may require extra kernel/network capabilities and is not guaranteed.

## Ubuntu prerequisites

```bash
sudo apt update
sudo apt install -y mininet openvswitch-switch iperf3 iputils-ping iproute2
sudo systemctl start openvswitch-switch
sudo mn -c
sudo python3 simulator/mininet_experiment.py --output /tmp/network-fault-run.json
```

Run from repository root. The script creates isolated Mininet hosts and OVS switches, runs **real ICMP packets** and **real TCP iperf3 traffic** before and after injecting packet loss on one virtual link. It writes raw measurements and metadata to JSON. No hardware Wi-Fi/fiber/microwave physics is simulated here.

The script requires root, performs a Mininet cleanup of its own topology, and is intended for a dedicated lab VM only. Avoid using on a production server. Review the output before interpreting results; TCP throughput can be affected by host CPU and environment.

The baseline network is `h1 -- s1 -- s2 -- h2`. The impairment is applied to both ends of the `s1-s2` link using `tc netem loss`. This is an impairment experiment, not fault localization.
