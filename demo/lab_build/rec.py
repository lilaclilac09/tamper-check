import time, json, glob, subprocess, shutil, sys
from playwright.sync_api import sync_playwright
URL=sys.argv[1] if len(sys.argv)>1 else "http://localhost:3311/tools/tamper-check"
M={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome")
    ctx=b.new_context(viewport={"width":1280,"height":1000},record_video_dir="raw",record_video_size={"width":1280,"height":1000})
    t0=time.time(); pg=ctx.new_page()
    def box(sel):
        r=pg.locator(sel).first.bounding_box(); return [round(r["x"]),round(r["y"]),round(r["width"]),round(r["height"])] if r else None
    def mark(k,*sels): M[k]={"t":round(time.time()-t0,2),"box":[box(s) for s in sels]}
    pg.goto(URL); pg.wait_for_selector("[data-testid=tc-step1]"); pg.wait_for_timeout(1500)
    pg.screenshot(path="top.png")
    pg.locator("[data-testid=tc-step1]").scroll_into_view_if_needed(); pg.evaluate("document.querySelector('[data-testid=tc-step1]').scrollIntoView({block:'start'})"); pg.wait_for_timeout(600)
    for case,vals in (("gen",["57.007","57.006","57.008"]),("tam",["58.209","58.208","58.210"])):
        if case=="tam": pg.click("[data-testid=tc-step1] button:has-text('Reset')"); pg.wait_for_timeout(400)
        mark(case+"1_start","[data-testid=tc-step1] svg")
        for i,v in enumerate(vals):
            pg.click("[data-testid=tc-tare1]"); pg.wait_for_timeout(500)
            mark(f"{case}1_type{i}","[data-testid=tc-in1]","[data-testid=tc-lcd1]")
            pg.locator("[data-testid=tc-in1]").press_sequentially(v,delay=120); pg.wait_for_timeout(300)
            pg.click("[data-testid=tc-weigh]"); pg.wait_for_timeout(700); mark(f"{case}1_lcd{i}","[data-testid=tc-lcd1]")
            pg.wait_for_selector(f"[data-testid=tc-note-{i}]"); pg.wait_for_timeout(900)
        pg.wait_for_selector("[data-testid=tc-v1]"); pg.wait_for_timeout(500); mark(case+"1_res","[data-testid=tc-step1] svg","[data-testid=tc-v1]")
        pg.screenshot(path=f"{case}1.png"); pg.wait_for_timeout(3000)
    pg.evaluate("document.querySelector('[data-testid=tc-step2]').scrollIntoView({block:'start'})"); pg.wait_for_timeout(700)
    for case,(L,R,L2,R2) in (("gen",("28.504","28.504","28.504","28.504")),("tam",("28.517","29.693","29.505","28.705"))):
        if case=="tam": pg.click("[data-testid=tc-step2] button:has-text('Reset')"); pg.wait_for_timeout(400)
        mark(case+"2_start","[data-testid=tc-step2] svg")
        pg.click("[data-testid=tc-tare2]"); pg.wait_for_timeout(1200); pg.click("[data-testid=tc-place2]"); pg.wait_for_timeout(1000)
        mark(case+"2_lr","[data-testid=tc-step2] svg")
        pg.locator("[data-testid=tc-L]").press_sequentially(L,delay=110); pg.locator("[data-testid=tc-R]").press_sequentially(R,delay=110); pg.wait_for_timeout(1500)
        pg.click("[data-testid=tc-rot]"); mark(case+"2_rot","[data-testid=tc-step2] svg"); pg.wait_for_timeout(1700)
        pg.locator("[data-testid=tc-L2]").press_sequentially(L2,delay=110); pg.locator("[data-testid=tc-R2]").press_sequentially(R2,delay=110); pg.wait_for_timeout(800)
        pg.wait_for_selector("[data-testid=tc-v2]"); mark(case+"2_res","[data-testid=tc-step2] svg","[data-testid=tc-offset]","[data-testid=tc-v2]")
        pg.screenshot(path=f"{case}2.png"); pg.wait_for_timeout(3500)
    mark("end"); ctx.close(); b.close()
json.dump(M,open("marks.json","w"),indent=1)
src=glob.glob("raw/*.webm")[0]; subprocess.run(["ffmpeg","-y","-v","error","-i",src,"-c:v","libx264","-pix_fmt","yuv420p","-r","25","lab_raw.mp4"],check=True); shutil.rmtree("raw")
