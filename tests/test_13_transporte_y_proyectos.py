"""Acto II: petróleo transportado por los principales ductos (recálculo independiente desde raw/), afirmaciones sobre capacidades y
fuentes externas de la caja de proyectos anunciados."""
import re
import urllib.request

import pandas as pd
import pytest

import helpers as H

PERMITIDOS = {"energia-argentina.ypf.com", "www.argentina.gob.ar", "mase.lmneuquen.com", "www.oldelval.com", "econojournal.com.ar"}


def _volumen_independiente(idducto):
    t = H.p20_dedup()
    t = t[(t.idducto == idducto) & (t.tipo_producto == "Petroleo")]
    seg = t.groupby(["anio", "mes", "nodo_origen", "nodo_destino"], dropna=False).volumen.sum().reset_index()
    return seg.groupby(["anio", "mes"]).volumen.max().groupby("anio").sum()


def test_allen_puerto_rosales_y_duplicar_igual_recalculo(raw):
    r = H.web_json("registro_cifras.json")
    a, d = _volumen_independiente(216), _volumen_independiente(511)
    for y in range(2020, 2026):
        assert abs(a.get(y, 0) - r[f"vol_allen_{y}_m3"]["valor"]) < 0.5, y
    assert abs(d[2025] - r["vol_duplicar_2025_m3"]["valor"]) < 0.5 and list(d.index) == [2025, 2026]
    assert abs(r["allen_total_2025_m3"]["valor"] - (a[2025] + d[2025])) < 1


def test_duplicar_aparece_en_marzo_de_2025(raw):
    t = H.p20_dedup()
    t = t[(t.idducto == 511) & (t.tipo_producto == "Petroleo") & (t.volumen > 0)]
    assert (t.anio * 100 + t.mes).min() == 202503


def test_el_flujo_de_2024_supera_la_capacidad_que_informa_el_anexo():
    r = H.web_json("registro_cifras.json")
    assert r["allen_flujo_2024_m3_dia"]["valor"] > r["allen_cap_anexo_2024"]["valor"] == r["ext_oldelval_cap_2022_m3"]["valor"]
    f = r["allen_flujo_2024_m3_dia"]["valor"]
    assert abs(100 * f / 42000 - r["allen_util_con_cap_prensa_pct"]["valor"]) < 5          # el tramo mas cargado es algo mayor que el promedio anual
    assert r["allen_util_con_cap_prensa_pct"]["valor"] > 100 > r["allen_util_con_cap_2023_pct"]["valor"]


def test_los_enlaces_externos_son_de_fuentes_permitidas():
    h = H.html_text()
    enlaces = set(re.findall(r'href="(https?://[^"]+)"', h))
    hosts = {re.match(r"https?://([^/]+)", u).group(1) for u in enlaces}
    assert hosts - {"github.com", "fonts.googleapis.com", "fonts.gstatic.com", "cdnjs.cloudflare.com"} <= PERMITIDOS, hosts
    assert len(enlaces) >= 8


def test_la_caja_de_proyectos_declara_que_es_informacion_externa():
    t = H.html_visible_text()
    assert re.search(r"Información externa, no verificada con los datos de este proyecto", t)
    assert not re.search(r"\b(récord|cuello de botella)\b", t, re.I)


@pytest.mark.parametrize("url", ["https://energia-argentina.ypf.com/vmos.html", "https://www.oldelval.com/proyecto-duplicar/", "https://www.oldelval.com/2026/09/08/",
                                 "https://mase.lmneuquen.com/petroleo/vmos-cumple-un-ano-y-acelera-el-salto-exportador-del-petroleo-vaca-muerta-n1226139",
                                 "https://www.argentina.gob.ar/noticias/energia-firmo-la-prorroga-que-hara-duplicar-la-capacidad-de-transporte-para-vaca-muerta"])
def test_los_enlaces_responden(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            assert r.status == 200
    except OSError as e:                                  # sin red, o bloqueo del sitio: no es un fallo del informe
        pytest.skip(f"no se pudo comprobar: {e}")
