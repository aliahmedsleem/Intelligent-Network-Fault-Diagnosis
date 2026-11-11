"""Read-only host-network diagnostics for authorized physical LAN/Wi-Fi.

No scanning, remote execution, configuration changes or subnet enumeration.
Uses the host's operating-system network interface and route information.
"""
from __future__ import annotations

import platform
import re
import subprocess

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/physical", tags=["Physical network"])


class ProbeRequest(BaseModel):
    target: str = Field(min_length=1, max_length=253)


def run_command(args: list[str], timeout: int = 8) -> dict:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, shell=False)
        return {"exit_code": proc.returncode, "output": (proc.stdout + "\n" + proc.stderr).strip()[:12000]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HTTPException(status_code=503, detail="Host diagnostic command unavailable or timed out") from exc


@router.get("/interfaces")
def interfaces():
    os_name = platform.system()
    if os_name == "Windows":
        result = run_command(["ipconfig", "/all"])
    elif os_name == "Linux":
        result = run_command(["ip", "-brief", "address"])
    else:
        raise HTTPException(status_code=501, detail="Unsupported host operating system")
    return {"source": "host_operating_system", "platform": os_name, "result": result, "note": "Interface listing does not establish link health or network ownership."}


@router.get("/routes")
def routes():
    os_name = platform.system()
    if os_name == "Windows":
        result = run_command(["route", "print", "-4"])
    elif os_name == "Linux":
        result = run_command(["ip", "-4", "route", "show"])
    else:
        raise HTTPException(status_code=501, detail="Unsupported host operating system")
    return {"source": "host_operating_system", "platform": os_name, "result": result}


@router.post("/ping")
def ping(request: ProbeRequest):
    # Single target only, never accept command options or shell syntax.
    target = request.target.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}", target) or ".." in target or target.endswith("."):
        raise HTTPException(status_code=422, detail="Provide a valid IP address or hostname")
    os_name = platform.system()
    if os_name == "Windows":
        args = ["ping", "-n", "3", "-w", "1500", target]
    elif os_name == "Linux":
        args = ["ping", "-c", "3", "-W", "2", target]
    else:
        raise HTTPException(status_code=501, detail="Unsupported host operating system")
    result = run_command(args, timeout=9)
    return {"source": "active_icmp_probe", "target": target, "result": result, "note": "ICMP failures alone do not prove that a host or link is down."}


def _powershell_json(script: str):
    result = run_command(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], timeout=12)
    if result["exit_code"] != 0:
        raise HTTPException(status_code=503, detail="Windows network information is unavailable")
    try:
        return __import__("json").loads(result["output"])
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Windows network information could not be parsed") from exc


@router.get("/active")
def active_network():
    """Detect the Windows interface used for the default IPv4 route."""
    if platform.system() != "Windows":
        raise HTTPException(status_code=501, detail="Automatic active-interface detection currently requires Windows")
    script = """
$ErrorActionPreference = 'Stop'
$r = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' |
 Where-Object { $_.NextHop -ne '0.0.0.0' } |
 Sort-Object RouteMetric,InterfaceMetric | Select-Object -First 1
if (-not $r) { throw 'No IPv4 default route' }
$a = Get-NetAdapter -InterfaceIndex $r.InterfaceIndex
$ip = Get-NetIPAddress -InterfaceIndex $r.InterfaceIndex -AddressFamily IPv4 |
 Where-Object { $_.IPAddress -notlike '169.254.*' } | Select-Object -First 1
$dns = @(Get-DnsClientServerAddress -InterfaceIndex $r.InterfaceIndex -AddressFamily IPv4 |
 Select-Object -ExpandProperty ServerAddresses)
[pscustomobject]@{
 interface_index=$r.InterfaceIndex; interface_name=$a.Name;
 interface_description=$a.InterfaceDescription; status=$a.Status;
 link_speed=$a.LinkSpeed; mac_address=$a.MacAddress;
 connection_type=$(if ($a.NdisPhysicalMedium -match 'Wireless|802.11' -or $a.InterfaceDescription -match 'Wi-Fi|Wireless|802.11') {'wifi'} else {'ethernet_or_other'});
 ipv4=$ip.IPAddress; prefix_length=$ip.PrefixLength;
 gateway=$r.NextHop; dns_servers=$dns
} | ConvertTo-Json -Compress -Depth 4
"""
    data = _powershell_json(script)
    wifi = None
    if data.get("connection_type") == "wifi":
        # netsh reports signal quality as a percentage, not calibrated RSSI.
        raw = run_command(["netsh", "wlan", "show", "interfaces"], timeout=8)
        lines = raw["output"].splitlines()
        for line in lines:
            if ":" not in line:
                continue
            key, value = (s.strip() for s in line.split(":", 1))
            if key.lower() in {"ssid", "bssid", "signal", "radio type", "channel", "receive rate (mbps)", "transmit rate (mbps)"}:
                if wifi is None:
                    wifi = {}
                wifi[key.lower().replace(" ", "_")] = value
    return {"source": "windows_active_route", "interface": data, "wifi": wifi,
            "note": "Detected from the Windows default IPv4 route; Wi-Fi signal is OS-reported quality, not RSSI."}


@router.get("/diagnose")
def diagnose_active_network():
    """Conservative, read-only diagnostics from the computer's active route."""
    import socket
    connection = active_network()
    interface = connection["interface"]
    gateway = interface.get("gateway")
    if not gateway:
        return {"connection": connection, "status": "no_gateway", "findings": ["No default gateway detected"], "checks": {}}
    gateway_ping = run_command(["ping", "-n", "3", "-w", "1500", gateway], timeout=9)
    dns_ok = False
    dns_error = None
    try:
        socket.getaddrinfo("example.com", 443, type=socket.SOCK_STREAM)
        dns_ok = True
    except OSError as exc:
        dns_error = type(exc).__name__
    findings = []
    if interface.get("status", "").lower() != "up":
        findings.append("The selected network adapter is not reported as Up")
    if gateway_ping["exit_code"] != 0:
        findings.append("Gateway did not answer ICMP; this can also be caused by ICMP filtering")
    if not dns_ok:
        findings.append("DNS resolution failed from this computer")
    if connection.get("wifi"):
        signal = connection["wifi"].get("signal", "")
        match = re.search(r"(\d+)\s*%", signal)
        if match and int(match.group(1)) < 40:
            findings.append("Wi-Fi signal quality is low according to Windows")
    return {
        "source": "windows_active_network_diagnostics",
        "connection": connection,
        "status": "potential_issues" if findings else "no_issues_detected_by_limited_checks",
        "findings": findings,
        "checks": {"gateway_icmp": {"target": gateway, **gateway_ping},
                   "dns_lookup": {"hostname": "example.com", "success": dns_ok, "error": dns_error}},
        "note": "Preliminary evidence only. A failed ICMP probe does not prove a gateway failure; DNS success does not prove internet connectivity."
    }
