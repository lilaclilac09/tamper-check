import shutil, subprocess, glob, os
from playwright.sync_api import sync_playwright
A=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=A)
    ctx=b.new_context(viewport={"width":1280,"height":1000},record_video_dir="demo/raw",record_video_size={"width":1280,"height":1000})
    pg=ctx.new_page(); pg.goto("http://127.0.0.1:8765/"); pg.wait_for_function("document.querySelectorAll('#model option').length>0"); pg.wait_for_timeout(4000)
    for lbl in ["Genuine","Glue one side","LTE implant"]:
        pg.click(f'button:has-text("{lbl}")'); pg.wait_for_timeout(9000); pg.mouse.wheel(0,500); pg.wait_for_timeout(5000); pg.mouse.wheel(0,-500); pg.wait_for_timeout(1500)
    pg.fill("#w","57, 57, 57"); pg.select_option("#resol","1"); pg.wait_for_timeout(1500); pg.click('button:has-text("Check")'); pg.wait_for_timeout(8000)
    pg.fill("#w","57.312, 57.310, 57.313"); pg.select_option("#resol","0.001"); pg.wait_for_timeout(1500); pg.click('button:has-text("Check")'); pg.wait_for_timeout(5000)
    for i in range(6): pg.locator("#res input[type=checkbox]").nth(i).check(); pg.wait_for_timeout(1200)
    pg.mouse.wheel(0,600); pg.wait_for_timeout(5000)
    ctx.close(); b.close()
src=glob.glob("demo/raw/*.webm")[0]
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",src,"-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart","demo/demo.mp4"],check=True)
shutil.rmtree("demo/raw")
