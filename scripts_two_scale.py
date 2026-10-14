"""Record the two-scale demo segment (demo/two_scale_raw.mp4) + screenshots. Server must run on :8765."""
import shutil, subprocess, glob, sys, time, json
from playwright.sync_api import sync_playwright
A=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"]
rec="--video" in sys.argv
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=A)
    kw=dict(record_video_dir="demo/raw2",record_video_size={"width":1280,"height":1000}) if rec else {}
    ctx=b.new_context(viewport={"width":1280,"height":1000},**kw)
    T={}; t0=time.time(); mark=lambda k: T.__setitem__(k,round(time.time()-t0,2))
    pg=ctx.new_page(); pg.goto("http://127.0.0.1:8765/"); pg.wait_for_function("document.querySelectorAll('#model option').length>0"); pg.wait_for_timeout(2500)
    pg.locator("#two").scroll_into_view_if_needed(); pg.evaluate("document.querySelector('#two').style.outline='2px solid #3fb950'"); pg.wait_for_timeout(5000)
    pg.click('button:has-text("Genuine (2 scales)")'); pg.wait_for_function("document.querySelector('#res .v')&&document.querySelector('#res .v').textContent=='LIKELY GENUINE'"); mark('genuine'); pg.wait_for_timeout(1500)
    pg.screenshot(path="screenshots/two_scale/genuine.png"); pg.wait_for_timeout(9000 if rec else 0)
    pg.click('button:has-text("LTE implant (2 scales)")'); pg.wait_for_function("document.querySelector('#res .v').textContent=='TAMPERED - DO NOT USE'"); mark('implant'); pg.wait_for_timeout(1500)
    pg.screenshot(path="screenshots/two_scale/implant.png"); pg.wait_for_timeout(11000 if rec else 0)
    pg.locator('#v3d').scroll_into_view_if_needed(); mark('3d'); pg.wait_for_timeout(2000)
    pg.screenshot(path="screenshots/two_scale/implant_3d.png"); pg.wait_for_timeout(10000 if rec else 0); mark('end')
    json.dump(T,open('demo/two_scale_times.json','w')); print(T)
    ctx.close(); b.close()
if rec:
    src=glob.glob("demo/raw2/*.webm")[0]
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",src,"-c:v","libx264","-pix_fmt","yuv420p","-r","25","demo/two_scale_raw.mp4"],check=True)
    shutil.rmtree("demo/raw2")
