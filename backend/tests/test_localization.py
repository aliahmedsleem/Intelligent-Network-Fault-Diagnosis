from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
NETWORK = {"nodes": ["A", "B", "C", "D"], "links": [
    {"id": "ab", "source": "A", "target": "B", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 1},
    {"id": "bc", "source": "B", "target": "C", "medium": "fiber", "capacity_mbps": 100, "delay_ms": 1},
    {"id": "cd", "source": "C", "target": "D", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 1},
]}
def probe(a, b, loss):
    return {"source": a, "target": b, "baseline_loss_percent": 0, "observed_loss_percent": loss}

def test_unique_localization_without_ground_truth():
    payload = {"network": NETWORK, "probes": [
        probe("A", "C", 25), probe("B", "D", 22), probe("A", "B", 0), probe("C", "D", 0),
    ]}
    result = client.post("/api/localization/analyze", json=payload)
    assert result.status_code == 200
    body = result.json()
    assert body["suspected_link_id"] == "bc"
    assert body["status"] == "candidate_found"

def test_ambiguity_is_explicit():
    payload = {"network": NETWORK, "probes": [probe("A", "D", 20), probe("A", "D", 20)]}
    body = client.post("/api/localization/analyze", json=payload).json()
    assert body["status"] == "ambiguous"
    assert body["suspected_link_id"] is None

def test_no_degradation_does_not_invent_fault():
    payload = {"network": NETWORK, "probes": [probe("A", "B", 0), probe("B", "C", 0)]}
    body = client.post("/api/localization/analyze", json=payload).json()
    assert body["status"] == "insufficient_evidence"
    assert body["suspected_link_id"] is None

def test_unknown_endpoint_rejected():
    payload = {"network": NETWORK, "probes": [probe("A", "X", 20), probe("A", "B", 0)]}
    assert client.post("/api/localization/analyze", json=payload).status_code == 422
