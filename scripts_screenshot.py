from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"]); pg=b.new_page(viewport={"width":1300,"height":900})
    pg.goto("http://127.0.0.1:8765/"); pg.wait_for_function("document.querySelectorAll('#model option').length>0"); pg.wait_for_timeout(300)
    for k,lbl in [("genuine","Genuine"),("glue","Glue one side"),("implant","LTE implant")]:
        pg.click(f'button:has-text("{lbl}")'); pg.wait_for_timeout(700); pg.screenshot(path=f"screenshots/{k}.png",full_page=True)
    pg.fill("#w","57, 57, 57"); pg.select_option("#resol","1"); pg.click('button:has-text("Check")'); pg.wait_for_timeout(700)
    pg.screenshot(path="screenshots/kitchen_scale_demo_only.png",full_page=True)
    pg.fill("#w","57.312, 57.310, 57.313"); pg.select_option("#resol","0.001"); pg.click('button:has-text("Check")'); pg.wait_for_timeout(700)
    pg.screenshot(path="screenshots/manual_diamond_scale_flagged.png",full_page=True)
    pg.locator("#comm").screenshot(path="screenshots/community_reports.png")
    b.close()
