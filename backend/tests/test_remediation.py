from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
REPORT = {
    "mode": "mininet_remediation_measured", "topology": "h1-s1-s2-h2",
    "baseline": {"sent": 50, "received": 50, "loss_percent": 0},
    "faulted": {"sent": 50, "received": 30, "loss_percent": 40},
    "recovered": {"sent": 50, "received": 49, "loss_percent": 2},
    "verification": {"passed": True, "loss_tolerance_pp": 5,
                     "criterion": "recovered loss <= baseline loss + tolerance"},
    "remediation_type": "remove_known_injected_impairment",
}


def test_verified_recovery():
    r = client.post("/api/remediation/analyze", json=REPORT)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "verified_recovery"
    assert r.json()["measurements"]["recovery_gain_pp"] == 38


def test_reject_forged_verification():
    p = {**REPORT, "verification": {**REPORT["verification"], "passed": False}}
    assert client.post("/api/remediation/analyze", json=p).status_code == 422


def test_reject_inconsistent_packet_counts():
    p = {**REPORT, "recovered": {"sent": 50, "received": 40, "loss_percent": 2}}
    assert client.post("/api/remediation/analyze", json=p).status_code == 422


def test_failed_verification_is_not_called_success():
    p = {**REPORT, "recovered": {"sent": 50, "received": 40, "loss_percent": 20},
         "verification": {**REPORT["verification"], "passed": False}}
    r = client.post("/api/remediation/analyze", json=p)
    assert r.status_code == 200
    assert r.json()["status"] == "verification_failed"
