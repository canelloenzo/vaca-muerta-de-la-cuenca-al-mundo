"""Abre docs/index.html en Chromium headless y falla si hay errores de consola o paneles rotos.
Requiere: pip install playwright && python -m playwright install chromium
Uso: python scripts/verificar_html_headless.py [ruta_captura_dir]"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]


def verificar(captura_dir=None, ancho=1280):
    errores, avisos = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": ancho, "height": 900})
        pg.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errores.append(str(e)))
        pg.on("requestfailed", lambda r: avisos.append(f"request fallido: {r.url}"))
        pg.goto((REPO / "docs" / "index.html").as_uri(), wait_until="networkidle")
        pg.wait_for_timeout(800)
        estado = pg.evaluate(r"""() => ({
            charts: Object.values(Chart.instances).length,
            yac: document.querySelectorAll('#yac-tbody tr').length,
            resp: document.querySelectorAll('#resp-tbody tr').length,
            excl: document.querySelectorAll('#excl-tbody tr').length,
            emp: document.querySelectorAll('#empresa-list .empresa-row').length,
            scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth,
            marcadores: (document.body.innerText.match(/\{\{|\[URL_/g) || []).length })""")
        if captura_dir:
            Path(captura_dir).mkdir(parents=True, exist_ok=True)
            pg.screenshot(path=str(Path(captura_dir) / f"index_{ancho}.png"), full_page=True)
        b.close()
    return errores, avisos, estado


if __name__ == "__main__":
    cap = sys.argv[1] if len(sys.argv) > 1 else None
    res = {}
    for w in (1280, 390):
        e, a, s = verificar(cap, w)
        print(w, "errores:", e, "| avisos:", a, "|", s)
        res[w] = (e, s)
    ok = all(not e and s["charts"] == 5 and s["yac"] == 10 and s["marcadores"] == 0 and s["scrollW"] <= s["innerW"] + 1 for e, s in res.values())
    print("RESULTADO:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
