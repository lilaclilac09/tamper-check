"""End-to-end: launches the server, drives the dashboard in Chromium, checks verdicts + 3D render."""
import os, shutil, socket, subprocess, sys, time, pytest
pw = pytest.importorskip("playwright.sync_api")

def _port():
    s=socket.socket(); s.bind(("127.0.0.1",0)); p=s.getsockname()[1]; s.close(); return p

@pytest.fixture(scope="module")
def url():
    port=_port(); proc=subprocess.Popen([sys.executable,"-m","uvicorn","tamper_check.app:app","--port",str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    import urllib.request
    for _ in range(50):
        try: urllib.request.urlopen(f"http://127.0.0.1:{port}/api/models"); break
        except Exception: time.sleep(0.2)
    yield f"http://127.0.0.1:{port}/"
    proc.terminate()

def test_dashboard_e2e(url):
    exe=os.environ.get("CHROME_PATH") or shutil.which("google-chrome")
    with pw.sync_playwright() as p:
        b=p.chromium.launch(executable_path=exe,args=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"]) if exe else p.chromium.launch(args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"])
        pg=b.new_page(); errors=[]
        pg.on("console",lambda m: m.type=="error" and errors.append(m.text)); pg.on("pageerror",lambda e: errors.append(str(e)))
        pg.goto(url); pg.wait_for_function("document.querySelectorAll('#model option').length>0")
        pg.wait_for_selector("#v3d canvas")
        expect={"Genuine":"LIKELY GENUINE","Glue one side":"SUSPICIOUS","LTE implant":"TAMPERED - DO NOT USE"}
        for btn,v in expect.items():
            pg.click(f'button:has-text("{btn}")'); pg.wait_for_function(f"document.querySelector('#res .v')&&document.querySelector('#res .v').textContent=={v!r}")
            n=pg.locator("#res ol li").count(); assert (n==0) if v=="LIKELY GENUINE" else (n==6)
        pg.fill("#w","57, 57, 57"); pg.select_option("#resol","1"); pg.click('button:has-text("Check")')
        pg.wait_for_function("document.querySelector('#res').textContent.includes('DEMO-ONLY')")
        pg.fill("#w","57.312, 57.310, 57.313"); pg.select_option("#resol","0.001"); pg.click('button:has-text("Check")')
        pg.wait_for_function("document.querySelector('#res').textContent.includes('0.312')")
        assert pg.locator("#res ol li").count()==6
        # 3D canvas actually drew something (non-background pixels)
        nonbg=pg.evaluate("""()=>{const c=document.querySelector('#v3d canvas');const t=document.createElement('canvas');t.width=c.width;t.height=c.height;const x=t.getContext('2d');x.drawImage(c,0,0);const d=x.getImageData(0,0,t.width,t.height).data;let n=0;for(let i=0;i<d.length;i+=4)if(Math.abs(d[i]-13)+Math.abs(d[i+1]-17)+Math.abs(d[i+2]-23)>30)n++;return n}""")
        assert nonbg>500, nonbg
        assert pg.locator("#hist tr").count()==6
        b.close()
    assert not errors, errors
