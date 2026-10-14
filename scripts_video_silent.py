"""Record the silent captioned demo walkthrough: demo/walk_raw.mp4 + demo/walk_marks.json (times + element boxes).
Server must run on :8765. Numbers are simulated EXAMPLES."""
import shutil, subprocess, glob, time, json
from playwright.sync_api import sync_playwright
A=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"]
M={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=A)
    ctx=b.new_context(viewport={"width":1280,"height":1000},record_video_dir="demo/raw3",record_video_size={"width":1280,"height":1000})
    t0=time.time(); pg=ctx.new_page()
    def box(sel):
        return pg.evaluate("""s=>{let r=null;for(const e of document.querySelectorAll(s)){const b=e.getBoundingClientRect();if(!b.width)continue;r=r?{x0:Math.min(r.x0,b.left),y0:Math.min(r.y0,b.top),x1:Math.max(r.x1,b.right),y1:Math.max(r.y1,b.bottom)}:{x0:b.left,y0:b.top,x1:b.right,y1:b.bottom}}return r}""",sel)
    def mark(k,sel=None): M[k]={"t":round(time.time()-t0,2),"box":box(sel) if sel else None}
    def typ(sel,txt): pg.fill(sel,""); pg.locator(sel).press_sequentially(txt,delay=110)
    def check(v): pg.click('button:has-text("Check")'); pg.wait_for_function(f"document.querySelector('#res .v')&&document.querySelector('#res .v').textContent=={v!r}"); pg.wait_for_timeout(600)
    RES="#res .v, #res table"
    pg.goto("http://127.0.0.1:8765/"); pg.wait_for_function("document.querySelectorAll('#model option').length>0"); pg.wait_for_timeout(1500); mark("overview")
    pg.wait_for_timeout(3000)
    for name,txt,res,v in [("genuine","57.007, 57.006, 57.008","0.001","LIKELY GENUINE"),("glue","57.359, 57.358, 57.360","0.001","SUSPICIOUS"),
                           ("kitchen","57, 57, 57","1","LIKELY GENUINE"),("mg","57.312, 57.310, 57.313","0.001","SUSPICIOUS")]:
        pg.select_option("#resol",res); mark(name+"_type","#w, #resol"); typ("#w",txt); pg.wait_for_timeout(700); mark(name+"_typed")
        check(v); mark(name+"_res",RES); pg.wait_for_timeout(3000)
        if name=="glue":
            pg.locator("#v3d").scroll_into_view_if_needed(); pg.wait_for_timeout(500); mark("glue_3d","#v3d"); pg.wait_for_timeout(4000)
            pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(800)
        if name=="genuine":
            pg.click('button:has-text("LTE implant")'); pg.wait_for_function("document.querySelector('#res .v').textContent=='TAMPERED - DO NOT USE'"); pg.wait_for_timeout(600)
            mark("implant_res",RES); pg.wait_for_timeout(3500)
            pg.locator("#v3d").scroll_into_view_if_needed(); pg.wait_for_timeout(500); mark("implant_3d","#v3d"); pg.wait_for_timeout(4000)
            pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(800)
    mark("mg_check","#res ol"); pg.wait_for_timeout(1500)
    for i in range(6): pg.locator("#res input[type=checkbox]").nth(i).check(); pg.wait_for_timeout(500)
    pg.wait_for_timeout(1500)
    pg.locator("#two").scroll_into_view_if_needed(); pg.wait_for_timeout(600)
    for name,w,L,R,L2,R2,v in [("ts_gen","57.008, 57.007, 57.009","29.261","27.747","28.938","28.070","LIKELY GENUINE"),
                               ("ts_imp","58.209, 58.208, 58.210","28.517","29.693","29.505","28.705","TAMPERED - DO NOT USE")]:
        typ("#w",w)
        for i in ("#ls","#rs","#ls2","#rs2"): pg.fill(i,"")
        pg.evaluate("twoCalc()"); pg.wait_for_timeout(300)
        mark(name+"_lr","#ls, #rs, #ls2, #rs2, #span"); typ("#ls",L); typ("#rs",R); pg.wait_for_timeout(600); mark(name+"_flip")
        typ("#ls2",L2); typ("#rs2",R2); pg.wait_for_timeout(900); mark(name+"_off","#twox"); pg.wait_for_timeout(3000)
        check(v); mark(name+"_res",RES); pg.wait_for_timeout(3500)
    pg.locator("#v3d").scroll_into_view_if_needed(); pg.wait_for_timeout(500); mark("ts_3d","#v3d"); pg.wait_for_timeout(4500); mark("end")
    ctx.close(); b.close()
json.dump(M,open("demo/walk_marks.json","w"),indent=1)
src=glob.glob("demo/raw3/*.webm")[0]
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",src,"-c:v","libx264","-pix_fmt","yuv420p","-r","25","demo/walk_raw.mp4"],check=True)
shutil.rmtree("demo/raw3")
