from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
payload = {
    "mode": "mininet_measured",
    "timestamp_utc": "2026-11-09T10:00:00+00:00",
    "topology": "h1-s1-s2-h2",
    "fault": {"type": "netem_packet_loss", "target_link": "s1-s2", "configured_loss_percent_each_direction": 20},
    "before": {"ping": {"packets_sent": 20, "packets_received": 20, "loss_percent": 0, "rtt_avg_ms": 3, "parse_ok": True}, "tcp": {"throughput_mbps": 90}},
    "after": {"ping": {"packets_sent": 20, "packets_received": 14, "loss_percent": 30, "rtt_avg_ms": 5, "parse_ok": True}, "tcp": {"throughput_mbps": 45}},
}


def test_import_measured_run():
    r = client.post("/api/measurements/analyze", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["measurements"]["throughput_change_mbps"] == -45
    assert "icmp_packet_loss_increased" in body["evidence"]
    assert body["localization"]["status"] == "not_performed"


def test_reject_analytical_as_measured():
    r = client.post("/api/measurements/analyze", json={**payload, "mode": "analytical_estimate"})
    assert r.status_code == 422


def test_missing_values_are_not_fabricated():
    p = {**payload, "after": {"ping": {"parse_ok": False}, "tcp": {"error": "iperf failed"}}}
    r = client.post("/api/measurements/analyze", json=p)
    assert r.status_code == 200
    assert r.json()["measurements"]["throughput_change_mbps"] is None
    assert "missing_measurements" in r.json()["quality_flags"]


def test_invalid_counts():
    p = {**payload, "after": {"ping": {"packets_sent": 10, "packets_received": 12}, "tcp": {}}}
    assert client.post("/api/measurements/analyze", json=p).status_code == 422
