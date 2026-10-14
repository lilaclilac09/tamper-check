from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
from .reference import REFERENCE
from .engine import score
from .simulator import scenario
app=FastAPI(title="tamper-check"); HISTORY=[]
class Measurement(BaseModel):
    model:str; weight_g:Optional[float]=None; scale_readings_g:Optional[list[float]]=None; scale_resolution_g:Optional[float]=None; com_mm:Optional[list[float]]=None
    imu_samples:Optional[dict]=None; rf_csv:Optional[str]=None; attestation:Optional[str]=None
    source:Optional[str]=None; seal_broken:bool=False; label:Optional[str]=None
def run(m):
    if m["model"] not in REFERENCE: raise HTTPException(404,"unknown model")
    r=score(m); r["label"]=m.get("label") or "manual"; r["id"]=len(HISTORY)+1; HISTORY.append(r); return r
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
