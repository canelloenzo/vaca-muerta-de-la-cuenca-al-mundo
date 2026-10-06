"""5.1 de la auditoría: lo que se publica (data/web y objeto DATA embebido en docs/index.html) coincide
con el recálculo independiente. Incluye cada cifra de la sección (4) de la auditoría."""
import numpy as np
import pandas as pd
import pytest

import helpers as H


def test_kpis_html_igual_web():
    assert H.html_data()["kpis"] == H.web_json("resumen_kpis.json")


def test_indices_html_igual_web():
    d = pd.DataFrame(H.html_data()["indices"])
    w = H.web("indices_mensuales.csv")
    assert len(d) == len(w) == 102
    assert np.allclose(d.p.fillna(-1), w.indice_produccion.fillna(-1)) and np.allclose(d.e.fillna(-1), w.indice_exportacion.fillna(-1))


def test_top_yacimientos_html_igual_web(DATA):
    w = H.web("top_yacimientos.csv")
    assert [r["n"] for r in DATA["top_yac"]] == list(w.areayacimiento)
    assert np.allclose([r["v"] for r in DATA["top_yac"]], w.produccion_bbl_dia)


def test_mapa_html_igual_web(DATA):
    w = H.web("produccion_mapa.csv")
    assert len(DATA["mapa"]) == len(w) == 3062
    assert abs(sum(r[4] for r in DATA["mapa"]) - w.produccion_total_historica_bbl.sum()) < 3062


def test_prod_anual_html_igual_recalculo(vm, DATA):
    pa = vm.groupby(["anio", "tipo_de_recurso"]).bbl.sum().unstack().fillna(0)
    h = pd.DataFrame(DATA["prod_anual"]).set_index("anio")
    assert (h.noconv - pa["NO CONVENCIONAL"]).abs().max() < 0.06
    assert (h.conv - pa["CONVENCIONAL"]).abs().max() < 0.06


def test_paises_html_igual_recalculo(export_raw, DATA):
    con = export_raw[export_raw.pais.notna() & ~export_raw.pais.isin({"NO IDENTIFICADO", "no aplica"})]
    tot = con.groupby("pais").volumen.sum().sort_values(ascending=False)
    pr = {r["pais"].upper(): r["vol"] for r in DATA["paises_rank"] if not r["pais"].startswith("Otros")}
    for p, v in pr.items():
        key = "PERU" if p == "PERU" else p
        assert abs(tot[key] - v) < 0.1, p
    otros = [r for r in DATA["paises_rank"] if r["pais"].startswith("Otros")][0]["vol"]
    assert abs(tot.iloc[10:].sum() - otros) < 0.1


def test_empresas_html_igual_recalculo(export_raw, DATA):
    e = export_raw[export_raw.anio.between(2020, 2025)].groupby("empresa").volumen.sum().sort_values(ascending=False)
    top = DATA["empresas"]
    assert [r["pct"] for r in top[:3]] == list((100 * e / e.sum()).round(2).head(3))


# ------------------------------------------------------------------------------------------
# Cifras de la sección (4) de la auditoría ("pasaron todo")
# ------------------------------------------------------------------------------------------
def test_s4_produccion(vm):
    assert round(vm.bbl.sum()) == 722_439_535
    assert len(vm) == 205_082
    s = H.monthly_bbl_dia(vm)
    assert round(s["2025-12-01"], 1) == 590_754.6
    assert round(100 * (s["2025-12-01"] / s["2024-12-01"] - 1), 2) == 31.92


def test_s4_pozos_y_coordenadas(vm):
    nc = vm[vm.tipo_de_recurso == "NO CONVENCIONAL"]
    assert nc.idpozo.nunique() == 3062
    assert vm.idpozo.nunique() - nc.idpozo.nunique() == 238
    otros = vm[vm.tipo_de_recurso != "NO CONVENCIONAL"].drop_duplicates("idpozo").tipo_de_recurso.value_counts().to_dict()
    assert otros == {"CONVENCIONAL": 234, "SIN RESERVORIO": 3, "NO DISCRIMINADO": 1}


def test_s4_exportacion(export_raw):
    t = export_raw.groupby("anio").volumen.sum()
    assert round(t.loc[2025]) == 11_826_286 and t.loc[:2025].idxmax() == 2025
    assert round(100 * (t.loc[2025] / t.loc[2024] - 1), 1) == 59.6
    neu = export_raw[export_raw.empresa.isin(H.OPERADORES_NEUQUINOS)].groupby("anio").volumen.sum()
    assert round(neu.loc[2025]) == 9_642_378 and round(100 * neu.loc[2025] / t.loc[2025], 1) == 81.5
    j = export_raw[export_raw.fecha == "2026-06-01"]
    assert round(j.volumen.sum(), 1) == 1_268_381.1
    assert round(100 * j[j.empresa == "Oiltanking EBYTEM S.A."].volumen.sum() / j.volumen.sum(), 1) == 97.3


def test_s4_exportacion_neuquina_sobre_produccion_vm(vm, export_raw):
    neu = export_raw[export_raw.empresa.isin(H.OPERADORES_NEUQUINOS)].groupby("anio").volumen.sum()
    prod = vm.groupby("anio").prod_pet.sum()
    assert round(100 * neu.loc[2025] / prod.loc[2025], 1) == 33.1


def test_s4_precios_2019_2021(clean_ok):
    p = H.clean("dim_precio_exportacion_crudo.csv")
    f = pd.to_datetime(p.fecha)
    assert f.min() == pd.Timestamp("2019-01-01") and f.max() == pd.Timestamp("2021-06-01") and f.nunique() == 30


def test_s4_cobertura_de_capacidad(raw, clean_ok):
    t = H.p20_raw()
    cap = H.clean("fact_capacidad_ductos.csv")
    mes = t.groupby(["idducto", "anio", "mes"]).size().reset_index()
    m = mes.merge(cap[["idducto", "anio", "mes"]], how="left", indicator=True)
    assert len(mes) == 7939 and int((m._merge == "both").sum()) == 3603
    v = cap[cap.capacidad_valida]
    assert round(v.utilizacion_pct.median(), 2) == 0.53 and int((v.utilizacion_pct > 1).sum()) == 291 and len(v) == 3483


def test_s4_locale_en_power_query():
    pq = (H.REPO / "powerbi" / "power_query_m.md").read_text(encoding="utf-8")
    bloques = pq.split("\n## ")
    datos = [b for b in bloques if "Csv.Document" in b]
    assert len(datos) == 10 and all('"en-US"' in b for b in datos)
