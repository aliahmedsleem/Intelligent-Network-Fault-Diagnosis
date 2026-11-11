from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
network = {"nodes": ["a", "b", "c", "d"], "links": [
    {"id": "ab", "source": "a", "target": "b", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 1},
    {"id": "bc", "source": "b", "target": "c", "medium": "fiber", "capacity_mbps": 100, "delay_ms": 1},
    {"id": "cd", "source": "c", "target": "d", "medium": "ethernet", "capacity_mbps": 100, "delay_ms": 1},
]}
def probe(s,t,loss):
    return {"source":s,"target":t,"baseline_loss_percent":0,"observed_loss_percent":loss}
def payload(probes, approve=True):
    return {"batch":{"mode":"mininet_multi_probe_measured","network":network,"probes":probes},
            "require_manual_approval":approve}

def test_unique_candidate_still_requires_approval():
    p=payload([probe("a","c",20),probe("b","d",25),probe("a","b",0),probe("c","d",0)])
    r=client.post("/api/lifecycle/plan",json=p)
    assert r.status_code==200,r.text
    assert r.json()["remediation"]["target_link"]=="bc"
    assert r.json()["remediation"]["status"]=="awaiting_approval"
    assert r.json()["remediation"]["executed"] is False

def test_ambiguous_blocks_action():
    r=client.post("/api/lifecycle/plan",json=payload([probe("a","d",20),probe("a","d",20)]))
    assert r.status_code==200
    assert r.json()["remediation"]["status"]=="blocked"

def test_no_privileged_execution_even_if_approval_disabled():
    p=payload([probe("a","c",20),probe("b","d",25),probe("a","b",0),probe("c","d",0)],False)
    result=client.post("/api/lifecycle/plan",json=p).json()
    assert result["remediation"]["status"]=="plan_ready"
    assert result["remediation"]["executed"] is False
    assert result["verification"]["status"]=="not_run"

def test_reject_unapproved_action():
    p=payload([probe("a","c",20),probe("b","d",25)])
    p["requested_action"]="restart_network_service"
    assert client.post("/api/lifecycle/plan",json=p).status_code==422
