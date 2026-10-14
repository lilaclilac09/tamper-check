import random
from .reference import REFERENCE

def imu_samples(com,rng,k=0.8,noise=0.05):
    pts={}
    for i,ax in enumerate("xy"):
        pts[ax]=[[s, k*(com[i]-s)+rng.gauss(0,noise)] for s in (-6,-3,0,3,6)]
    return pts

def rf_log(rng,implant=False,dur=120,period=30):
    lines=["timestamp_s,freq_mhz,rssi_dbm"]
    for t in range(0,dur,2):
        f=rng.choice([433.9,868.3,915.0,1800.0,2140.0]); lines.append(f"{t},{f},{-96+rng.gauss(0,1.5):.1f}")
    if implant:
        for t in range(5,dur,period):
            for j in range(3): lines.append(f"{t+j*0.2:.1f},{rng.choice([850.0,1842.5,2655.0])},{-52+rng.gauss(0,3):.1f}")
    return "\n".join(lines)

def two_scale_readings(w,com_x,rng,span=100.0,res=0.001,placement_sd=0.8):
    """Simulated two-scale balance (EXAMPLE data). Placement error p is shared by both placements;
    wallet rotated 180 deg in place for the second pair."""
    p=rng.gauss(0,placement_sd); r=lambda v: round(round(v/res)*res,4); out={"span_mm":span}
    for sfx,x in (("",com_x+p),("2",-com_x+p+rng.gauss(0,0.03))):
        R=w*(0.5+x/span); out["left"+sfx+"_g"]=r(w-R+rng.gauss(0,0.0007)); out["right"+sfx+"_g"]=r(R+rng.gauss(0,0.0007))
    return out

def scenario(model="ledger-flex",kind="genuine",seed=0,res=0.001,method="imu"):
    """kind: genuine | glue (mass added one side) | implant (mass + LTE bursts) | counterfeit (attestation fail)"""
    rng=random.Random(seed); ref=REFERENCE[model]
    w=ref["weight_g"]+rng.gauss(0,0.008); com=[rng.gauss(0,0.2),rng.gauss(0,0.2)]
    rf=False; att="pass"; src="direct"
    if kind in("glue","implant"):
        added=0.35 if kind=="glue" else 1.2; L=ref["dims_mm"][0]
        off=L*0.35; com[0]=(com[0]*w+off*added)/(w+added); w+=added; src="reseller"
        rf= kind=="implant"
    if kind=="counterfeit": att="fail"; src="marketplace"
    reads=[round(round((w+rng.gauss(0,0.001))/res)*res,4) for _ in range(5)]
    d={"model":model,"scale_readings_g":reads,"scale_resolution_g":res}
    if method=="two_scale": d["two_scale"]=two_scale_readings(w,com[0],rng,res=res); d["label"]=kind+" (two-scale)"
    else: d["imu_samples"]=imu_samples(com,rng)
    return {**d,"rf_csv":rf_log(rng,rf),"attestation":att,"source":src,"label":d.get("label",kind)}
