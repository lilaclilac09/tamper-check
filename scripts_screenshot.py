from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome"); pg=b.new_page(viewport={"width":1300,"height":900})
    pg.goto("http://127.0.0.1:8765/"); pg.wait_for_function("document.querySelectorAll(\"#model option\").length>0"); pg.wait_for_timeout(500)
    for k,lbl in [("genuine","Genuine"),("glue","Glue one side"),("implant","LTE implant")]:
        pg.click(f"button:has-text(\"{lbl}\")"); pg.wait_for_timeout(700); pg.screenshot(path=f"screenshots/{k}.png",full_page=True)
    b.close()
