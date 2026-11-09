from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
run={"mode":"ns3_wifi_packet_simulation","standard":"802.11a_5ghz",
     "seed":1,"run":1,"distance_m":25,"duration_s":20,"offered_mbps":5,
     "tx_packets":1000,"rx_packets":900,"packet_loss_percent":10,
     "throughput_mbps":4.3,"mean_delay_ms":2.5}

def test_consistent_ns3_result():
    response=client.post("/api/ns3/wifi/inspect",json=run)
    assert response.status_code==200,response.text
    assert response.json()["audit_status"]=="consistent"

def test_detects_forged_loss_rate():
    response=client.post("/api/ns3/wifi/inspect",json={**run,"packet_loss_percent":0})
    assert response.status_code==200
    assert "reported_loss_disagrees_with_packet_counts" in response.json()["quality_flags"]

def test_rejects_wrong_mode():
    assert client.post("/api/ns3/wifi/inspect",json={**run,"mode":"measured_hardware"}).status_code==422
