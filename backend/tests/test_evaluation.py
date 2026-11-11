from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
network={"nodes":["a","b","c","d"],"links":[
    {"id":"ab","source":"a","target":"b","medium":"ethernet","capacity_mbps":100,"delay_ms":1},
    {"id":"bc","source":"b","target":"c","medium":"ethernet","capacity_mbps":100,"delay_ms":1},
    {"id":"cd","source":"c","target":"d","medium":"ethernet","capacity_mbps":100,"delay_ms":1}]}
probes=[{"source":"a","target":"c","baseline_loss_percent":0,"observed_loss_percent":20},
        {"source":"b","target":"d","baseline_loss_percent":0,"observed_loss_percent":20},
        {"source":"a","target":"b","baseline_loss_percent":0,"observed_loss_percent":0},
        {"source":"c","target":"d","baseline_loss_percent":0,"observed_loss_percent":0}]
def trial(truth):
    return {"mode":"mininet_multi_probe_measured","network":network,"probes":probes,"ground_truth_link_id":truth}

def test_dataset_metrics():
    r=client.post("/api/evaluation/localization",json={"trials":[trial("bc"),trial("ab")]})
    assert r.status_code==200,r.text
    data=r.json()
    assert data["top1_accuracy_over_all_labeled"]["rate"]==0.5
    assert data["labeled_trial_count"]==2
    assert data["top1_accuracy_over_all_labeled"]["lower_95"] < 0.5
    assert data["top1_accuracy_over_all_labeled"]["upper_95"] > 0.5

def test_empty_dataset_rejected():
    assert client.post("/api/evaluation/localization",json={"trials":[]}).status_code==422

def test_unlabeled_excluded_from_accuracy():
    r=client.post("/api/evaluation/localization",json={"trials":[trial(None)]})
    assert r.status_code==200
    assert r.json()["top1_accuracy_over_all_labeled"] is None
