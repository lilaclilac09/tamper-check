import time, json, glob, subprocess, shutil, sys
from playwright.sync_api import sync_playwright
URL=sys.argv[1]; M={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/home/box/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome')
    ctx=b.new_context(viewport={"width":1280,"height":1000},record_video_dir="raw",record_video_size={"width":1280,"height":1000})
    t0=time.time(); pg=ctx.new_page()
    def box(sel):
        r=pg.locator(sel).first.bounding_box(); return [round(r["x"]),round(r["y"]),round(r["width"]),round(r["height"])] if r else None
    def mark(k,*sels): M[k]={"t":round(time.time()-t0,2),"box":[box(s) for s in sels]}
    pg.goto(URL,wait_until="networkidle"); pg.wait_for_selector("[data-testid=tc-step1]"); pg.wait_for_timeout(1200)
    pg.evaluate("document.querySelector('[data-testid=tc-step1]').scrollIntoView({block:'start'})"); pg.wait_for_timeout(600)
    for case,vals in (("gen",["57.007","57.006","57.008"]),("light",["57.082","57.081","57.083"]),("glue",["57.351","57.349","57.352"])):
        for i in range(3): pg.fill(f"[data-testid=tc-w{i}]","")
        pg.wait_for_timeout(300); mark(case+"1_start")
        for i,v in enumerate(vals):
            pg.locator(f"[data-testid=tc-w{i}]").press_sequentially(v,delay=90); pg.wait_for_timeout(250)
        pg.wait_for_timeout(500); mark(case+"1_res","[data-testid=tc-v1]")
        pg.wait_for_timeout(2500)
    for i in range(3): pg.fill(f"[data-testid=tc-w{i}]","")
    pg.evaluate("document.querySelector('[data-testid=tc-step2]').scrollIntoView({block:'start'})"); pg.wait_for_timeout(800)
    mark("cards",".tc-steps"); pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelector('[data-testid=tc-L]').scrollIntoView({block:'start'});document.querySelector('[data-testid=tc-scroll]').scrollBy(0,-60)"); pg.wait_for_timeout(700)
    for case,vals in (("gen",("28.504","28.504","28.504","28.504")),("tam",("28.517","29.693","29.505","28.705"))):
        for k in "L R L2 R2".split(): pg.fill(f"[data-testid=tc-{k}]","")
        pg.wait_for_timeout(300); mark(case+"2_start")
        for k,v in zip("L R L2 R2".split(),vals):
            pg.locator(f"[data-testid=tc-{k}]").press_sequentially(v,delay=90); pg.wait_for_timeout(250)
        pg.wait_for_timeout(500); mark(case+"2_res","[data-testid=tc-v2]"); pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelector('[data-testid=tc-criteria]').scrollIntoView({block:'start'})"); pg.wait_for_timeout(800)
    mark("crit","[data-testid=tc-criteria] table"); pg.wait_for_timeout(2500)
    mark("end"); ctx.close(); b.close()
json.dump(M,open("marks.json","w"),indent=1)
src=glob.glob("raw/*.webm")[0]; subprocess.run(["ffmpeg","-y","-v","error","-i",src,"-c:v","libx264","-pix_fmt","yuv420p","-r","25","lab_raw.mp4"],check=True); shutil.rmtree("raw")
