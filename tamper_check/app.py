from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
from .reference import REFERENCE
from .engine import score
from .simulator import scenario
from .community import load_cases, notes_for
from fastapi.staticfiles import StaticFiles
app=FastAPI(title="tamper-check"); HISTORY=[]
_m=Path(__file__).parent.parent/'data'/'x_ohyishi'/'media'
if _m.exists(): app.mount('/media',StaticFiles(directory=_m),name='media')
class Measurement(BaseModel):
    model:str; weight_g:Optional[float]=None; scale_readings_g:Optional[list[float]]=None; scale_resolution_g:Optional[float]=None; com_mm:Optional[list[float]]=None
    imu_samples:Optional[dict]=None; rf_csv:Optional[str]=None; attestation:Optional[str]=None
    source:Optional[str]=None; seal_broken:bool=False; label:Optional[str]=None
def run(m):
    if m["model"] not in REFERENCE: raise HTTPException(404,"unknown model")
    r=score(m); r["community"]=notes_for(m["model"]); r["label"]=m.get("label") or "manual"; r["id"]=len(HISTORY)+1; HISTORY.append(r); return r
@app.get("/api/models")
def models(): return REFERENCE
@app.post("/api/check")
def check(m:Measurement): return run(m.model_dump())
@app.post("/api/simulate/{model}/{kind}")
def sim(model:str,kind:str,seed:int=0):
    if kind not in("genuine","glue","implant","counterfeit"): raise HTTPException(400,"bad kind")
    if model not in REFERENCE: raise HTTPException(404,"unknown model")
    return run(scenario(model,kind,seed))
@app.get("/api/history")
def hist(): return HISTORY[::-1]
@app.get("/")
def index(): return FileResponse(Path(__file__).parent.parent/"static"/"index.html")
@app.get("/api/community")
def community(model:Optional[str]=None, category:Optional[str]=None):
    cs=load_cases()
    if model: cs=[c for c in cs if model in str(c.get("device_model")) or c.get("device_model")=="any"]
    if category: cs=[c for c in cs if c.get("category")==category]
    return {"label":"COMMUNITY-REPORTED / UNVERIFIED (public X posts, @ohyishi threads, collected 2026-10-14)","count":len(cs),"cases":cs,
            "notes":notes_for(model) if model else None}
