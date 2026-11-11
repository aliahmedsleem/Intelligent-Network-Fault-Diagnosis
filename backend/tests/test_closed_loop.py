from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
network = {"nodes":["h1","h2","h3","h4","s1","s2","s3"],"links":[
 {"id":"h1-s1","source":"h1","target":"s1","medium":"ethernet","capacity_mbps":100,"delay_ms":1},
 {"id":"h2-s1","source":"h2","target":"s1","medium":"ethernet","capacity_mbps":100,"delay_ms":1},
 {"id":"s1-s2","source":"s1","target":"s2","medium":"ethernet","capacity_mbps":100,"delay_ms":2},
 {"id":"s2-s3","source":"s2","target":"s3","medium":"ethernet","capacity_mbps":100,"delay_ms":2},
 {"id":"h3-s3","source":"h3","target":"s3","medium":"ethernet","capacity_mbps":100,"delay_ms":1},
 {"id":"h4-s2","source":"h4","target":"s2","medium":"ethernet","capacity_mbps":100,"delay_ms":1}
]}
def probe(a,b,fault):
 return {"source":a,"target":b,"baseline_loss_percent":0,"observed_loss_percent":fault,"recovered_loss_percent":0}
artifact={"mode":"mininet_closed_loop_measured","network":network,
 "probes":[probe("h1","h4",30),probe("h2","h3",35),probe("h1","h2",0),probe("h3","h4",0)],
 "execution_policy":{"authorized":True,"reason":"unique_candidate_matches_lab_interlock","candidate":"s1-s2"},
 "verification":{"status":"passed"},
 "ground_truth_for_evaluation_only":{"fault_link":"s1-s2","top1_correct":True}}

def test_consistent_artifact():
 r=client.post("/api/lifecycle/inspect",json=artifact)
 assert r.status_code==200,r.text
 assert r.json()["audit_status"]=="consistent"
 assert r.json()["inference"]["suspected_link_id"]=="s1-s2"

def test_detects_false_success():
 p={**artifact,"probes":[{**artifact["probes"][0],"recovered_loss_percent":20},*artifact["probes"][1:]]}
 r=client.post("/api/lifecycle/inspect",json=p)
 assert r.status_code==200
 assert r.json()["audit_status"]=="inconsistent"
 assert "recovery_threshold_not_met" in r.json()["quality_flags"]

def test_detects_wrong_reported_candidate():
 p={**artifact,"execution_policy":{**artifact["execution_policy"],"candidate":"s2-s3"}}
 r=client.post("/api/lifecycle/inspect",json=p)
 assert "reported_candidate_disagrees_with_recomputed_inference" in r.json()["quality_flags"]

def test_rejects_wrong_mode():
 p={**artifact,"mode":"analytical_estimate"}
 assert client.post("/api/lifecycle/inspect",json=p).status_code==422
