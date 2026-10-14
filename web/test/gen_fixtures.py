"""Generate cross-engine parity vectors: inputs from the Python simulator + manual cases, with Python score() outputs.
Run from repo root: python web/test/gen_fixtures.py"""
import json, random
from tamper_check.engine import score
from tamper_check.simulator import scenario, rf_log
from tamper_check.reference import REFERENCE
cases=[]
for m in REFERENCE:
    for k in ("genuine","glue","implant","counterfeit"):
        for s in range(3):
            cases.append(scenario(m,k,s))
            if k!="counterfeit": cases.append(scenario(m,k,s,method="two_scale"))
w=57.0; R=w*(0.5+2.0/100)
cases+=[
 {"model":"ledger-nano-x","scale_readings_g":[34.0,34.001,33.999]},
 {"model":"ledger-nano-x","scale_readings_g":[34.07]*3},
 {"model":"ledger-nano-x","scale_readings_g":[34.3]*3},
 {"model":"ledger-flex","scale_readings_g":[57.3]*3,"scale_resolution_g":0.001},
 {"model":"ledger-flex","scale_readings_g":[57.0]*3,"scale_resolution_g":1},
 {"model":"ledger-stax","weight_g":45.0},
 {"model":"ledger-stax","attestation":"fail"},
 {"model":"ledger-stax","attestation":"not_run","seal_broken":True,"source":"marketplace"},
 {"model":"ledger-flex","scale_readings_g":[w]*3,"two_scale":{"left_g":w-R,"right_g":R,"left2_g":R,"right2_g":w-R,"span_mm":100}},
 {"model":"ledger-flex","scale_readings_g":[w]*3,"two_scale":{"left_g":28.5,"right_g":28.5}},
 {"model":"ledger-flex","scale_readings_g":[w]*3,"two_scale":{"left_g":28.0,"right_g":29.0}},
 {"model":"ledger-flex","rf_csv":rf_log(random.Random(0),True)},
 {"model":"ledger-flex","rf_csv":open("samples/rf_implant.csv").read()},
 {"model":"ledger-flex","rf_csv":open("samples/rf_genuine.csv").read()},
 {"model":"ledger-flex","com_mm":[1.0,0.5]},
]
out=[{"input":c,"expected":score(c)} for c in cases]
json.dump(out,open("web/test/fixtures.json","w"),indent=0)
print(len(out))
