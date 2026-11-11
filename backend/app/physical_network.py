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
