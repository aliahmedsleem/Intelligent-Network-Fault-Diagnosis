"""Read-only GNS3 controller integration (local controller only by default).

The adapter reads topology metadata; it does not change network configuration,
start/stop nodes, or claim device reachability from GNS3 state alone.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/gns3", tags=["GNS3"])
DEFAULT_URL = "http://127.0.0.1:3080"


def controller_url() -> str:
    raw = os.getenv("GNS3_CONTROLLER_URL", DEFAULT_URL).rstrip("/")
    parsed = urlparse(raw)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise HTTPException(status_code=503, detail="GNS3 controller must use a local HTTP endpoint; use a local SSH tunnel for remote controllers")
    return raw


def get_json(path: str):
    request = Request(controller_url() + path, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=4) as response:
            return json.load(response)
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"GNS3 controller returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Cannot reach the local GNS3 controller") from exc


@router.get("/status")
def status():
    version = get_json("/v2/version")
    return {"connected": True, "controller": "local", "version": version}


@router.get("/projects")
def projects():
    result = get_json("/v2/projects")
    return [{"project_id": p.get("project_id"), "name": p.get("name"), "status": p.get("status")} for p in result]


@router.get("/projects/{project_id}/topology")
def topology(project_id: str):
    import uuid
    try:
        uuid.UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid project UUID") from exc
    nodes = get_json(f"/v2/projects/{project_id}/nodes")
    links = get_json(f"/v2/projects/{project_id}/links")
    return {
        "source": "gns3_controller",
        "project_id": project_id,
        "nodes": [{"id": n.get("node_id"), "name": n.get("name"), "type": n.get("node_type"), "status": n.get("status"), "x": n.get("x"), "y": n.get("y")} for n in nodes],
        "links": [{"id": l.get("link_id"), "nodes": [{"node_id": end.get("node_id"), "adapter_number": end.get("adapter_number"), "port_number": end.get("port_number")} for end in l.get("nodes", [])]} for l in links],
        "note": "Controller metadata only; link health requires active probes or telemetry.",
    }
