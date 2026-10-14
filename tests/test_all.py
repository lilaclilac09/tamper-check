import random
from fastapi.testclient import TestClient
from tamper_check.engine import score, estimate_com, parse_rf_csv
from tamper_check.simulator import scenario, imu_samples, rf_log
from tamper_check.reference import REFERENCE
from tamper_check.app import app
def W(r,c): return next(w for w in r["warnings"] if w["check"]==c)
M=list(REFERENCE)
def test_com_recovers_offset():
    cx,cy=estimate_com(imu_samples([5.0,-2.0],random.Random(1),noise=0.0),[0,0]); assert abs(cx-5)<1e-6 and abs(cy+2)<1e-6
def test_com_noisy():
    cx,_=estimate_com(imu_samples([3.0,0],random.Random(2)),[0,0]); assert abs(cx-3)<0.3
def test_weight_rules():
    r=REFERENCE["ledger-nano-x"]["weight_g"]; f=lambda x,**k: score({"model":"ledger-nano-x","scale_readings_g":x,**k})
    assert f([r,r+0.001,r-0.001])["risk"]==0
    assert f([r+0.07]*3)["warnings"][0]["severity"]=="medium"
    assert f([r+0.3]*3)["warnings"][0]["severity"]=="high"
def test_mg_implant_caught_by_diamond_scale_not_kitchen():
    r=REFERENCE["ledger-flex"]["weight_g"]
    assert score({"model":"ledger-flex","scale_readings_g":[r+0.3]*3,"scale_resolution_g":0.001})["warnings"][0]["severity"]=="high"
    k=score({"model":"ledger-flex","scale_readings_g":[round(r+0.3)]*3,"scale_resolution_g":1})
    assert k["warnings"][0]["severity"]=="ok" and any(w["check"]=="scale_resolution" for w in k["warnings"])
def test_readings_averaged():
    assert abs(score({"model":"ledger-stax","scale_readings_g":[45.0,45.002,45.004]})["weight_g"]-45.002)<1e-9
def test_legacy_weight_and_repeat_hint():
    r=score({"model":"ledger-stax","weight_g":45.0}); assert r["risk"]==0 and any(w["check"]=="scale_repeat" for w in r["warnings"])
def test_remediation_only_when_flagged():
    assert score(scenario("ledger-flex","genuine",1))["remediation"]==[]
    rem=score(scenario("ledger-flex","glue",1))["remediation"]; assert rem and "seed" in rem[0]
def test_attestation_fail_critical(): assert W(score({"model":"ledger-stax","attestation":"fail"}),"attestation")["severity"]=="critical"
def test_rf_cell_detected():
    rows=parse_rf_csv(rf_log(random.Random(0),True)); r=score({"model":"ledger-flex","rf_rows":rows})
    w=W(r,"rf_emission"); assert w["severity"]=="critical" and "periodic" in w["message"]
def test_rf_silent(): assert W(score({"model":"ledger-flex","rf_csv":rf_log(random.Random(0))}),"rf_emission")["severity"]=="ok"
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
    assert c.post("/api/check",json={"model":"ledger-nano-s-plus","scale_readings_g":[21.0,21.001,20.999],"scale_resolution_g":0.001,"attestation":"pass"}).json()["verdict"]=="LIKELY GENUINE"
    assert c.post("/api/check",json={"model":"nope"}).status_code==404
    assert c.post("/api/simulate/ledger-flex/xx").status_code==400
    assert len(c.get("/api/history").json())>=2 and c.get("/").status_code==200

from tamper_check.community import load_cases, notes_for
def test_cases_dataset_valid():
    cs=load_cases(); assert len(cs)>=5
    for c in cs:
        assert c["verified"] is False and "UNVERIFIED" in c["source"] and c["source_post"].startswith("https://x.com/")
        for m in c.get("media",[]): assert (__import__("pathlib").Path(m)).exists(), m
def test_community_notes_do_not_change_specs_or_score():
    before=dict(REFERENCE["ledger-nano-s-plus"]); n=notes_for("ledger-nano-s-plus")
    assert REFERENCE["ledger-nano-s-plus"]==before and "UNVERIFIED" in n["label"] and any("ST33K1M5" in x for x in n["notes"])
    assert any(w["observed_g"]==19.9 for w in n["observed_weights"])
    s=scenario("ledger-nano-s-plus","genuine",0); assert score(s)["risk"]==0
def test_api_community():
    c=TestClient(app); d=c.get("/api/community").json(); assert d["count"]>=5 and "UNVERIFIED" in d["label"]
    f=c.get("/api/community?model=ledger-flex").json(); assert all("ledger-flex" in x["device_model"] or x["device_model"]=="any" for x in f["cases"]) and f["notes"]["notes"]
    assert c.get("/api/community?category=spec_drift").json()["count"]==2
    r=c.post("/api/simulate/ledger-flex/genuine").json(); assert "UNVERIFIED" in r["community"]["label"]
