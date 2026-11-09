from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
NETWORK = {"nodes": ["h1", "h2", "h3", "h4", "s1", "s2", "s3"], "links": [
    {"id": "h1-s1", "source": "h1", "target": "s1", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 1},
    {"id": "h2-s1", "source": "h2", "target": "s1", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 1},
    {"id": "s1-s2", "source": "s1", "target": "s2", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 2},
    {"id": "s2-s3", "source": "s2", "target": "s3", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 2},
    {"id": "h3-s3", "source": "h3", "target": "s3", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 1},
    {"id": "h4-s2", "source": "h4", "target": "s2", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 1},
]}
PROBES = [
    {"source": "h1", "target": "h4", "baseline_loss_percent": 0, "observed_loss_percent": 24},
    {"source": "h2", "target": "h3", "baseline_loss_percent": 0, "observed_loss_percent": 22},
    {"source": "h1", "target": "h2", "baseline_loss_percent": 0, "observed_loss_percent": 0},
    {"source": "h3", "target": "h4", "baseline_loss_percent": 0, "observed_loss_percent": 0},
]


def test_batch_infers_fault_without_ground_truth_input():
    response = client.post("/api/localization/probe-batch", json={
        "mode": "mininet_multi_probe_measured", "network": NETWORK,
        "probes": PROBES, "ground_truth_link_id": "s1-s2",
    })
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["localization"]["suspected_link_id"] == "s1-s2"
    assert result["evaluation"]["top1_correct"] is True


def test_wrong_ground_truth_does_not_change_inference():
    base = {"mode": "mininet_multi_probe_measured", "network": NETWORK, "probes": PROBES}
    first = client.post("/api/localization/probe-batch", json={**base, "ground_truth_link_id": "s1-s2"}).json()
    second = client.post("/api/localization/probe-batch", json={**base, "ground_truth_link_id": "s2-s3"}).json()
    assert first["localization"] == second["localization"]
    assert second["evaluation"]["top1_correct"] is False


def test_reject_fake_mode():
    response = client.post("/api/localization/probe-batch", json={
        "mode": "analytical_estimate", "network": NETWORK, "probes": PROBES,
    })
    assert response.status_code == 422
