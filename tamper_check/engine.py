import csv, io, math
from .reference import REFERENCE, CELL_BANDS_MHZ

def estimate_com(samples, base_mm):
    """Two-support balance method: device laid across a pivot/phone; each sample = (support_offset_mm, tilt_deg).
    Tilt ~ k*(com - support). Least-squares fit tilt = k*x_com - k*s  -> com = intercept/k. Done per axis.
    samples: {"x":[[s,tilt],...],"y":[...]}. Returns (cx,cy) in mm relative to geometric center."""
    out=[]
    for ax in ("x","y"):
        pts=samples.get(ax) or []
        if len(pts)<2: out.append(0.0); continue
        n=len(pts); sx=sum(p[0] for p in pts); sy=sum(p[1] for p in pts)
        sxx=sum(p[0]**2 for p in pts); sxy=sum(p[0]*p[1] for p in pts)
        den=n*sxx-sx*sx
        if den==0: out.append(0.0); continue
        slope=(n*sxy-sx*sy)/den; icpt=(sy-slope*sx)/n  # tilt = slope*s + icpt, slope=-k, icpt=k*com
        out.append(0.0 if slope==0 else -icpt/slope)
    return tuple(round(v,3) for v in out)

def parse_rf_csv(text):
    """CSV columns: timestamp_s,freq_mhz,rssi_dbm (Flipper/SDR-style export)."""
    rows=[]
    for r in csv.DictReader(io.StringIO(text)):
        rows.append((float(r["timestamp_s"]),float(r["freq_mhz"]),float(r["rssi_dbm"])))
    return rows

def in_cell(f): return any(a<=f<=b for a,b in CELL_BANDS_MHZ)

def score(m):
    model=m["model"]; ref=REFERENCE[model]; warnings=[]; risk=0
    def add(check,sev,pts,msg):
        nonlocal risk; risk+=pts; warnings.append({"check":check,"severity":sev,"points":pts,"message":msg})
    w=m.get("weight_g")
    if w is not None:
        d=w-ref["weight_g"]
        if abs(d)>2*ref["weight_tol_g"]: add("weight","high",35,f"Weight {w:.2f} g is {d:+.2f} g off reference (tol ±{ref['weight_tol_g']} g)")
        elif abs(d)>ref["weight_tol_g"]: add("weight","medium",15,f"Weight {d:+.2f} g outside tolerance")
        else: add("weight","ok",0,f"Weight within ±{ref['weight_tol_g']} g")
    com=m.get("com_mm")
    if com is None and m.get("imu_samples"): com=estimate_com(m["imu_samples"],ref["com_mm"])
    if com is not None:
        sh=math.dist(com,ref["com_mm"])
        if sh>2*ref["com_tol_mm"]: add("center_of_mass","high",30,f"Center of mass shifted {sh:.2f} mm toward ({com[0]:+.1f},{com[1]:+.1f})")
        elif sh>ref["com_tol_mm"]: add("center_of_mass","medium",12,f"CoM shift {sh:.2f} mm (tol {ref['com_tol_mm']})")
        else: add("center_of_mass","ok",0,f"CoM shift {sh:.2f} mm, normal")
    rf=m.get("rf_rows")
    if rf is None and m.get("rf_csv"): rf=parse_rf_csv(m["rf_csv"])
    if rf is not None:
        floor=m.get("rf_noise_floor_dbm",-95); hits=[r for r in rf if r[2]>floor+15]
        cell=[r for r in hits if in_cell(r[1])]
        if cell:
            ts=sorted(r[0] for r in cell); per=None
            if len(ts)>2: gaps=[b-a for a,b in zip(ts,ts[1:]) if b-a>1]; per=round(sum(gaps)/len(gaps),1) if gaps else None
            add("rf_emission","critical",45,f"{len(cell)} cellular-band bursts while device OFF in Faraday bag"+(f", periodic ~{per}s" if per else "")+" — consistent with LTE/eSIM implant")
        elif hits: add("rf_emission","medium",10,f"{len(hits)} non-cellular emissions above floor")
        else: add("rf_emission","ok",0,"RF silent while powered off (expected)")
    att=m.get("attestation")
    if att is not None:
        if att=="pass": add("attestation","ok",0,"Ledger Genuine Check passed (note: does NOT detect added implants)")
        elif att=="fail": add("attestation","critical",50,"Genuine Check / attestation FAILED")
        else: add("attestation","medium",10,"Attestation not performed")
    if m.get("seal_broken"): add("packaging","medium",10,"Packaging/seal anomaly reported")
    if m.get("source") and m["source"]!="direct": add("provenance","low",5,f"Bought via {m['source']} (not ledger.com direct)")
    risk=min(risk,100)
    verdict="TAMPERED - DO NOT USE" if risk>=60 else "SUSPICIOUS" if risk>=25 else "LIKELY GENUINE"
    return {"model":model,"model_name":ref["name"],"risk":risk,"verdict":verdict,"warnings":warnings,"com_mm":com}
