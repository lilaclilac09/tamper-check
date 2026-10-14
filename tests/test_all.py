import random
from fastapi.testclient import TestClient
from tamper_check.engine import score, estimate_com, parse_rf_csv
from tamper_check.simulator import scenario, imu_samples, rf_log
from tamper_check.reference import REFERENCE
from tamper_check.app import app
M=list(REFERENCE)
def test_com_recovers_offset():
    cx,cy=estimate_com(imu_samples([5.0,-2.0],random.Random(1),noise=0.0),[0,0]); assert abs(cx-5)<1e-6 and abs(cy+2)<1e-6
def test_com_noisy():
    cx,_=estimate_com(imu_samples([3.0,0],random.Random(2)),[0,0]); assert abs(cx-3)<0.3
def test_weight_rules():
    r=REFERENCE["ledger-nano-x"]["weight_g"]
    assert score({"model":"ledger-nano-x","weight_g":r})["risk"]==0
    assert score({"model":"ledger-nano-x","weight_g":r+1.0})["warnings"][0]["severity"]=="medium"
    assert score({"model":"ledger-nano-x","weight_g":r+3})["warnings"][0]["severity"]=="high"
def test_attestation_fail_critical(): assert score({"model":"ledger-stax","attestation":"fail"})["warnings"][0]["severity"]=="critical"
def test_rf_cell_detected():
    rows=parse_rf_csv(rf_log(random.Random(0),True)); r=score({"model":"ledger-flex","rf_rows":rows})
    assert r["warnings"][0]["check"]=="rf_emission" and r["warnings"][0]["severity"]=="critical" and "periodic" in r["warnings"][0]["message"]
def test_rf_silent(): assert score({"model":"ledger-flex","rf_csv":rf_log(random.Random(0))})["warnings"][0]["severity"]=="ok"
def test_scenarios_all_models():
    for m in M:
        for s in range(5):
            assert score(scenario(m,"genuine",s))["verdict"]=="LIKELY GENUINE"
            assert score(scenario(m,"glue",s))["verdict"]!="LIKELY GENUINE"
            assert score(scenario(m,"implant",s))["verdict"]=="TAMPERED - DO NOT USE"
            assert score(scenario(m,"counterfeit",s))["verdict"]!="LIKELY GENUINE"
def test_api():
    c=TestClient(app); assert set(c.get("/api/models").json())==set(M)
    assert c.post("/api/simulate/ledger-flex/implant").json()["risk"]>=60
    assert c.post("/api/check",json={"model":"ledger-nano-s-plus","weight_g":21.0,"attestation":"pass"}).json()["verdict"]=="LIKELY GENUINE"
    assert c.post("/api/check",json={"model":"nope"}).status_code==404
    assert c.post("/api/simulate/ledger-flex/xx").status_code==400
    assert len(c.get("/api/history").json())>=2 and c.get("/").status_code==200
