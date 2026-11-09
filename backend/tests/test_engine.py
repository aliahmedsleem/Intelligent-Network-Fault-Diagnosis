import pytest
from fastapi.testclient import TestClient
from app.engine import evaluate, diagnose_fault
from app.main import app
from app.models import FaultExperiment, TrafficExperiment

NETWORK = {
    "nodes": ["A", "B", "C"],
    "links": [
        {"id": "ab", "source": "A", "target": "B", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 1},
        {"id": "bc", "source": "B", "target": "C", "medium": "fiber", "capacity_mbps": 80, "delay_ms": 2},
        {"id": "ac", "source": "A", "target": "C", "medium": "microwave", "capacity_mbps": 20, "delay_ms": 10},
    ],
}


def test_shortest_delay_route():
    result = evaluate(TrafficExperiment(network=NETWORK, source="A", target="C", offered_load_mbps=50))
    assert result.path == ["A", "B", "C"]
    assert result.bottleneck_mbps == 80
    assert result.estimated_throughput_mbps == 50


def test_link_fault_reroutes():
    result = diagnose_fault(FaultExperiment(network=NETWORK, source="A", target="C", offered_load_mbps=50, failed_link_id="bc"))
    assert result["after"]["path"] == ["A", "C"]
    assert result["after"]["estimated_throughput_mbps"] == 20
    assert result["route_changed"] is True


def test_no_route():
    network = {"nodes": ["A", "B"], "links": [NETWORK["links"][0]]}
    result = diagnose_fault(FaultExperiment(network=network, source="A", target="B", offered_load_mbps=10, failed_link_id="ab"))
    assert result["after"]["diagnosis"] == "no_route"


def test_invalid_link():
    with pytest.raises(ValueError):
        diagnose_fault(FaultExperiment(network=NETWORK, source="A", target="C", offered_load_mbps=10, failed_link_id="xyz"))


def test_api():
    client = TestClient(app)
    assert client.get("/api/health").json()["status"] == "ok"
    result = client.post("/api/experiments/analytical", json={"network": NETWORK, "source": "A", "target": "C", "offered_load_mbps": 50})
    assert result.status_code == 200
    assert result.json()["mode"] == "analytical_estimate"
