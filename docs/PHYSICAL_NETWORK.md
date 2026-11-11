# Physical network diagnosis — local computer

The primary physical-network target is the **network used by the computer running FastAPI**, not a remote site or an agent.

## Supported now (Windows backend host)

- `GET /api/physical/active`: detect the default IPv4 route and associated network adapter; read local IP, gateway, DNS, link speed and interface state.
- If the active interface appears wireless, read available OS-reported SSID, BSSID, channel, signal quality percentage and link rates using `netsh wlan show interfaces`.
- `GET /api/physical/diagnose`: run three ICMP probes to the active gateway and a DNS lookup of `example.com`; return conservative, evidence-based findings.
- Existing `/api/physical/interfaces`, `/routes`, and `/ping` remain available for manual inspection.

Use the **Physical LAN / Wi-Fi** screen and choose **Detect active connection** or **Diagnose this computer's network**. Backend must run **directly on Windows** to inspect the Windows Wi-Fi adapter; a backend running in WSL, Docker or a remote server inspects *its own* network instead.

## Important limitations

- The selected route is the Windows default IPv4 route; a VPN or unusual routing policy can change what is considered active.
- The Wi-Fi signal value is a Windows-reported percentage, **not RSSI in dBm**. Localized output from `netsh` can prevent optional Wi-Fi fields from being parsed.
- Gateway ICMP can be filtered. DNS resolution does not prove end-to-end connectivity. These checks are preliminary diagnosis, not verified fault localization.
- No active subnet scan, automated device configuration changes, or remediation.
- GNS3 remains a separate experimental environment, and ns-3/Mininet remain research tools.

## Planned

Improve Windows Wi-Fi telemetry via native APIs; interface-aware probing, packet loss and latency statistics, evidence confidence, safe recommendations, and explicit approval for any later remediation.
