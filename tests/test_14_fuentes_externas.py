"""Cada cifra externa que figura en el registro (ext_*, allen_cap_prensa_2022) se busca en el texto crudo de la página de la fuente citada.
Sin red, o si el sitio bloquea la consulta, la prueba se omite (no es un fallo del informe)."""
import html
import re
import urllib.request

import pytest

import helpers as H

FUENTES = {
    "https://energia-argentina.ypf.com/vmos.html": [r"550 mil barriles", r"700 mil barriles", r"437 km"],
    "https://www.oldelval.com/proyecto-duplicar/": [r"55\.000 m ?3", r"86\.000 m ?3"],
    "https://www.oldelval.com/2026/09/08/": [r"207 kil[oó]metros", r"24 pulgadas", r"220\.000 barriles", r"50% de avance global", r"primer trimestre de 2027"],
    "https://mase.lmneuquen.com/petroleo/vmos-cumple-un-ano-y-acelera-el-salto-exportador-del-petroleo-vaca-muerta-n1226139": [r"180\.000 barriles", r"550\.000 barriles", r"enero de 2027", r"m[aá]s del 50%"],
    "https://www.argentina.gob.ar/noticias/energia-firmo-la-prorroga-que-hara-duplicar-la-capacidad-de-transporte-para-vaca-muerta": [r"36\.000 m3"],
    "https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-302-2025-410830": [r"377\.400 BARRILES"],
    "https://econojournal.com.ar/oilgas/oldelval-amplio-su-capacidad-de-transporte-a-42-000-m3-de-petroleo-por-dia/": [r"42\.000 m3"],
}
VALORES = {"ext_vmos_cap_max_bbl": 550000, "ext_vmos_cap_amp_bbl": 700000, "ext_vmos_km": 437, "ext_vmos_cap_rigi_bbl": 377400, "ext_vmos_cap_inicial_prensa_bbl": 180000,
           "ext_dnorte_km": 207, "ext_dnorte_pulgadas": 24, "ext_dnorte_bbl": 220000, "ext_dnorte_avance_pct": 50, "ext_duplicar_f1_m3": 55000, "ext_duplicar_f2_m3": 86000,
           "ext_oldelval_cap_2022_m3": 36000, "allen_cap_prensa_2022": 42000}


def test_el_registro_tiene_los_valores_externos_citados():
    r = H.web_json("registro_cifras.json")
    for k, v in VALORES.items():
        assert r[k]["valor"] == v, k


@pytest.mark.parametrize("url", list(FUENTES))
def test_las_cifras_estan_en_el_texto_de_la_fuente(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
    except OSError as e:
        pytest.skip(f"no se pudo consultar: {e}")
    t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", raw)
    t = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).split())
    faltan = [p for p in FUENTES[url] if not re.search(p, t)]
    assert not faltan, f"no aparecen en {url}: {faltan}"
