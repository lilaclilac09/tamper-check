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
    assert f([r+0.2]*3)["warnings"][0]["severity"]=="high"
    b=f([r+0.3]*3); assert b["warnings"][0]["severity"]=="critical" and b["verdict"]=="TAMPERED - DO NOT USE"
def test_mg_implant_caught_by_diamond_scale_not_kitchen():
    r=REFERENCE["ledger-flex"]["weight_g"]
    assert score({"model":"ledger-flex","scale_readings_g":[r+0.3]*3,"scale_resolution_g":0.001})["warnings"][0]["severity"]=="critical"
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

from tamper_check.engine import com_from_two_scales
from tamper_check.simulator import two_scale_readings
def test_two_scale_math():
    t=com_from_two_scales(25.0,25.0,100); assert t["offset_mm"]==0 and not t["flipped"]
    t=com_from_two_scales(24.0,26.0,100); assert abs(t["x1_mm"]-2.0)<1e-9  # (26-24)/50*50
    assert com_from_two_scales(26.0,24.0,200)["offset_mm"]==-4.0
def test_two_scale_flip_cancels_placement():
    w,d,p,S=57.0,1.5,3.0,100.0
    R1=w*(0.5+(d+p)/S); R2=w*(0.5+(-d+p)/S)
    t=com_from_two_scales(w-R1,R1,S,w-R2,R2)
    assert abs(t["offset_mm"]-d)<1e-9 and abs(t["placement_mm"]-p)<1e-9 and t["flipped"]
    assert abs(com_from_two_scales(w-R1,R1,S)["offset_mm"]-(d+p))<1e-9  # unflipped is biased by placement
def test_two_scale_bad_input():
    import pytest
    with pytest.raises(ValueError): com_from_two_scales(0,0)
def test_two_scale_in_score():
    w=57.0; R=w*(0.5+2.0/100)
    r=score({"model":"ledger-flex","scale_readings_g":[w]*3,"two_scale":{"left_g":w-R,"right_g":R,"left2_g":R,"right2_g":w-R,"span_mm":100}})
    c=W(r,"center_of_mass"); assert c["severity"]=="high" and "two scales" in c["message"] and abs(r["com_mm"][0]-2.0)<1e-6
    g=score({"model":"ledger-flex","scale_readings_g":[w]*3,"two_scale":{"left_g":28.5,"right_g":28.5}})
    assert W(g,"center_of_mass")["severity"]=="ok" and g["risk"]==0
def test_two_scale_simulator_recovers_com():
    for s in range(20):
        t=two_scale_readings(57.0,1.0,random.Random(s))
        assert abs(com_from_two_scales(t["left_g"],t["right_g"],t["span_mm"],t["left2_g"],t["right2_g"])["offset_mm"]-1.0)<0.15
def test_two_scale_scenarios_and_api():
    for m in M:
        for s in range(5):
            assert score(scenario(m,"genuine",s,method="two_scale"))["verdict"]=="LIKELY GENUINE"
            assert score(scenario(m,"glue",s,method="two_scale"))["verdict"]!="LIKELY GENUINE"
            assert score(scenario(m,"implant",s,method="two_scale"))["verdict"]=="TAMPERED - DO NOT USE"
    c=TestClient(app); r=c.post("/api/simulate/ledger-flex/genuine?method=two_scale").json()
    assert r["two_scale"]["flipped"] and "two-scale" in r["label"]
    assert c.post("/api/simulate/ledger-flex/genuine?method=xx").status_code==400
    r=c.post("/api/check",json={"model":"ledger-flex","scale_readings_g":[57.0]*3,"two_scale":{"left_g":28.5,"right_g":28.5,"span_mm":100}}).json()
    assert r["two_scale"]["offset_mm"]==0 and r["verdict"]=="LIKELY GENUINE"
