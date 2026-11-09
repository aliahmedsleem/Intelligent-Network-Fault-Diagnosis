# GNS3 integration — phase 1

The dashboard now includes a **GNS3 Network** view that reads project,
node, and link metadata from a locally reachable GNS3 controller.

## Setup

1. Install and start GNS3, create or open a project, and start its local controller.
2. Start the existing FastAPI backend on the same host. The integration defaults to
   `http://127.0.0.1:3080` and uses the documented GNS3 v2 controller endpoints.
3. Open **GNS3 Network** and select the project.

The backend endpoints are:

- `GET /api/gns3/status`
- `GET /api/gns3/projects`
- `GET /api/gns3/projects/{project_id}/topology`

Optionally configure `GNS3_CONTROLLER_URL=http://localhost:3080` in the backend environment.
Only loopback HTTP addresses are permitted in phase 1 to avoid exposing an
unprotected controller over the network. For remote controllers, use an
authenticated SSH tunnel that terminates on localhost.

## Scope and next phases

This integration is **read-only**. GNS3's node state does not prove reachability.
The next phase will add authorized ICMP/TCP probes, per-device SNMP/SSH adapters,
fault correlation, and explicit human approval before any remediation.

LAN and Wi-Fi are *transport paths* to a reachable management address. Bridging
a GNS3 virtual Ethernet network to a physical wireless adapter is a separate
platform-specific problem and is not implemented by this adapter. A physical
network must be monitored only with the network owner's authorization.

Existing analytical, Mininet and ns-3 functionality remains separate while
the GNS3 adapter is validated.
