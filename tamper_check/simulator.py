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

def scenario(model="ledger-flex",kind="genuine",seed=0,res=0.001):
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
    return {"model":model,"scale_readings_g":reads,"scale_resolution_g":res,"imu_samples":imu_samples(com,rng),"rf_csv":rf_log(rng,rf),"attestation":att,"source":src,"label":kind}
