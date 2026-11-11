import math
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_fiber_budget_components():
    r = client.post("/api/models/link-budget", json={"link":{
        "medium":"fiber","length_km":10,"wavelength_nm":1550,
        "tx_power_dbm":0,"receiver_sensitivity_dbm":-15,
        "connector_count":2,"splice_count":2
    }})
    assert r.status_code == 200, r.text
    d = r.json()
    assert math.isclose(d["path_loss_db"],3.0,abs_tol=0.00001)
    assert d["received_power_dbm"] == -3
    assert d["link_margin_db"] == 9
    assert d["one_way_propagation_ms"] == 0.05

def test_radio_fspl_and_frequency():
    r = client.post("/api/models/link-budget", json={"link":{
        "medium":"wifi_2_4","distance_m":100,"frequency_ghz":2.45,
        "tx_power_dbm":20,"rx_sensitivity_dbm":-90
    }})
    assert r.status_code == 200, r.text
    d=r.json()
    assert 79 < d["path_loss_db"] < 82
    assert d["margin_sufficient"] is True

def test_invalid_band_rejected():
    r=client.post("/api/models/link-budget",json={"link":{
        "medium":"wifi_2_4","distance_m":100,"frequency_ghz":5.5,
        "tx_power_dbm":20,"rx_sensitivity_dbm":-90
    }})
    assert r.status_code == 422

def test_long_microwave_link_fails_margin():
    r=client.post("/api/models/link-budget",json={"link":{
        "medium":"microwave","distance_m":20000,"frequency_ghz":18,
        "tx_power_dbm":10,"rx_sensitivity_dbm":-80
    }})
    assert r.status_code == 200
    assert r.json()["margin_sufficient"] is False
