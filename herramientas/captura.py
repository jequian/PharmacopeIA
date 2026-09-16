import sys, time
from playwright.sync_api import sync_playwright
vistas = sys.argv[1:] or ["matriz","grafo","contrastes","catalogo","pendientes"]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width':1440,'height':950}, device_scale_factor=1)
    pg.goto("file:///home/claude/visor.html")
    pg.wait_for_timeout(1200)
    for v in vistas:
        pg.evaluate(f"document.querySelector('nav button[data-v=\"{v}\"]').click()")
        pg.wait_for_timeout(350)
        pg.screenshot(path=f"/tmp/cap-{v}.png", full_page=False)
    b.close()
print("listo")
