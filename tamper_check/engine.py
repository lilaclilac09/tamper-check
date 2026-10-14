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

BOARD_G=0.3  # extra mass this large is consistent with an added PCB/eSIM board -> TAMPERED

def com_from_two_scales(left_g,right_g,span_mm=100.0,left2_g=None,right2_g=None):
    """Two-scale balance: rigid ruler across two tared mg scales, supports span_mm apart, wallet laid centred.
    Moment balance about the midpoint: x = (R-L)/(R+L) * span/2 (mm, + = toward the right scale).
    x1 = d + p (device CoM offset d plus placement error p). After rotating the wallet 180 deg in place,
    x2 = -d + p, so d = (x1 - x2)/2 cancels placement error."""
    def x(L,R):
        if L is None or R is None or L+R<=0: raise ValueError("left/right readings must be positive")
        return (R-L)/(R+L)*span_mm/2
    x1=x(left_g,right_g); out={"method":"two_scale","span_mm":span_mm,"left_g":left_g,"right_g":right_g,"left2_g":left2_g,"right2_g":right2_g,"x1_mm":round(x1,3),"total_g":round(left_g+right_g,4)}
    if left2_g is not None and right2_g is not None:
        x2=x(left2_g,right2_g); out.update(x2_mm=round(x2,3),offset_mm=round((x1-x2)/2,3),placement_mm=round((x1+x2)/2,3),flipped=True)
    else: out.update(offset_mm=round(x1,3),flipped=False)
    return out

def parse_rf_csv(text):
    """CSV columns: timestamp_s,freq_mhz,rssi_dbm (Flipper/SDR-style export)."""
    rows=[]
    for r in csv.DictReader(io.StringIO(text)):
        rows.append((float(r["timestamp_s"]),float(r["freq_mhz"]),float(r["rssi_dbm"])))
    return rows

def in_cell(f): return any(a<=f<=b for a,b in CELL_BANDS_MHZ)

REMEDIATION=[
 "STOP: do NOT enter or import any seed phrase on this device; do not set it up.",
 "Run Ledger Genuine Check in Ledger Live (note: passes even with an added implant).",
 "Verify firmware version in Ledger Live matches the latest official release.",
 "If funds are already on a seed generated/entered on this device: move them to a fresh device bought DIRECT from ledger.com, with a NEW seed.",
 "Report to Ledger Support with purchase source; if funds were stolen, contact police before opening the device.",
 "Optional: photograph, then open up / visually inspect for extra PCB, eSIM, antenna or glue (voids evidence chain - only after reporting).",
]

def score(m):
    model=m["model"]; ref=REFERENCE[model]; warnings=[]; risk=0
    def add(check,sev,pts,msg):
        nonlocal risk; risk+=pts; warnings.append({"check":check,"severity":sev,"points":pts,"message":msg})
    readings=m.get("scale_readings_g") or ([m["weight_g"]] if m.get("weight_g") is not None else [])
    res=m.get("scale_resolution_g") or 0.001
    weight=None
    if readings:
        weight=sum(readings)/len(readings)
        spread=max(readings)-min(readings)
        tol=max(ref["weight_tol_g"],2*res,2*spread)
        d=weight-ref["weight_g"]
        info=f"avg of {len(readings)} reading(s) {weight:.3f} g, {d:+.3f} g vs reference (tol ±{tol:.3f} g @ {res} g resolution)"
        if d>=BOARD_G-1e-6 and abs(d)>2*tol: add("scale_weight","critical",60,"PRIMARY: "+info+f" — board-sized extra mass (>= {BOARD_G:.3f} g)")
        elif abs(d)>2*tol: add("scale_weight","high",50,"PRIMARY: "+info)
        elif abs(d)>tol: add("scale_weight","medium",25,"PRIMARY: "+info)
        else: add("scale_weight","ok",0,"PRIMARY: "+info)
        if res>=0.1: add("scale_resolution","medium",0,f"{res} g scale is DEMO-ONLY: cannot catch mg-level implants. Use a ~0.001 g diamond scale (2 mg repeatability).")
        if len(readings)<3: add("scale_repeat","low",0,"Take >=3 readings (re-zero between) for a reliable average")
        if spread>5*res and spread>0.005: add("scale_repeat","low",0,f"Readings spread {spread:.3f} g: check draft/level/zero")
    else: add("scale_weight","medium",10,"No scale reading: precision weight is the primary check")
    com=m.get("com_mm"); tsc=None
    t2=m.get("two_scale")
    if com is None and t2 and t2.get("left_g") is not None and t2.get("right_g") is not None:
        tsc=com_from_two_scales(t2["left_g"],t2["right_g"],t2.get("span_mm") or 100.0,t2.get("left2_g"),t2.get("right2_g"))
        com=[tsc["offset_mm"],0.0]
    if com is None and m.get("imu_samples"): com=estimate_com(m["imu_samples"],ref["com_mm"])
    if com is not None:
        sh=math.dist(com,ref["com_mm"])
        how=(f" [two scales: x={tsc['offset_mm']:+.2f} mm"+(f", flip-corrected, placement {tsc['placement_mm']:+.2f} mm cancelled" if tsc['flipped'] else ", single placement: rotate 180 deg and re-weigh to cancel placement error")+"]") if tsc else ""
        if sh>2*ref["com_tol_mm"]: add("center_of_mass","high",30,f"Center of mass shifted {sh:.2f} mm toward ({com[0]:+.1f},{com[1]:+.1f})"+how)
        elif sh>ref["com_tol_mm"]: add("center_of_mass","medium",12,f"CoM shift {sh:.2f} mm (tol {ref['com_tol_mm']})"+how)
        else: add("center_of_mass","ok",0,f"CoM shift {sh:.2f} mm, normal"+how)
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
    flagged=risk>=25
    verdict="TAMPERED - DO NOT USE" if risk>=60 else "SUSPICIOUS" if risk>=25 else "LIKELY GENUINE"
    return {"model":model,"model_name":ref["name"],"risk":risk,"verdict":verdict,"warnings":warnings,"com_mm":com,"weight_g":weight,"remediation":REMEDIATION if flagged else [],"two_scale":tsc}
