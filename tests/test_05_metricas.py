"""2.2 a 2.5 de la auditoría: bbl/día, índices, volatilidad y KPIs, recalculados desde raw/."""
import numpy as np
import pandas as pd
import pytest

import helpers as H


def test_bbl_dia_dic_2025_y_variacion(vm):
    s = H.monthly_bbl_dia(vm)
    assert round(s["2025-12-01"], 1) == 590_754.6
    assert round(s["2024-12-01"], 1) == 447_804.6
    assert round(100 * (s["2025-12-01"] / s["2024-12-01"] - 1), 2) == 31.92
    k = H.web_json("kpis_resumen.json")
    assert k["produccion_vm_dic_2025_bbl_dia"] == round(s["2025-12-01"], 1)
    assert k["variacion_interanual_vm_dic_2025_pct"] == 31.92


def test_dias_se_cuentan_una_vez_por_mes(vm):
    assert (vm.groupby("fecha").dias.nunique() == 1).all()
    s = H.monthly_bbl_dia(vm)
    assert round(vm[vm.anio == 2022].bbl.sum() / 365) == 243_237      # cifras citadas en dax_measures.md
    assert round(vm[vm.anio == 2025].bbl.sum() / 365) == 501_956
    assert (pd.Timestamp("2026-01-01") - pd.Timestamp("2006-01-01")).days == 7305
    assert len(s) == 240


def test_top_yacimientos_igual_recalculo(vm):
    y = vm.groupby(["areayacimiento", "fecha"]).agg(bbl=("bbl", "sum"), dias=("dias", "first")).reset_index()
    yy = y.groupby("areayacimiento").agg(bbl=("bbl", "sum"), dias=("dias", "sum"))
    yy["v"] = yy.bbl / yy.dias
    yy = yy.sort_values("v", ascending=False)
    w = H.web("top_yacimientos.csv")
    assert len(yy) == len(w) == 146
    assert list(yy.index) == list(w.areayacimiento)
    assert np.allclose(yy.v.round(1).values, w.produccion_bbl_dia.values, atol=0.051)
    assert w.iloc[0].areayacimiento == "BAJADA DEL PALO OESTE" and w.iloc[0].produccion_bbl_dia == 31386.5
    assert w.iloc[9].areayacimiento == "CRUZ DE LORENA" and w.iloc[9].produccion_bbl_dia == 6135.0


def test_indices_base_2019_solo_referencia(vm, export_raw):
    sp = H.monthly_bbl_dia(vm)
    se = export_raw.groupby("fecha").volumen.sum()
    bp, be = sp[sp.index.year == 2019].mean(), se[se.index.year == 2019].mean()
    assert round(bp, 1) == 90_014.4 and round(be, 1) == 316_714.1
    assert round(sp["2025-12-01"] / bp * 100, 2) == 656.29      # solo referencia: la base 2019 ya no se publica (F1)


def test_volatilidad_mensual_2020_2025(vm, export_raw):
    se = export_raw.groupby("fecha").volumen.sum().reindex(pd.date_range("2020-01-01", "2025-12-01", freq="MS"))
    sp = H.monthly_bbl_dia(vm).loc["2020-01-01":"2025-12-01"]
    e, p = se.pct_change().dropna().std() * 100, sp.pct_change().dropna().std() * 100
    assert round(e, 2) == 76.85 and round(p, 2) == 5.18 and round(e / p, 1) == 14.8


def test_pct_no_convencional(vm):
    assert round(100 * vm[vm.tipo_de_recurso == "NO CONVENCIONAL"].bbl.sum() / vm.bbl.sum(), 2) == 99.91
    v22 = vm[vm.anio >= 2022]
    assert round(100 * v22[v22.tipo_de_recurso == "NO CONVENCIONAL"].bbl.sum() / v22.bbl.sum(), 2) == 99.88


def test_convencional_solo_observable_desde_2022(vm):
    conv = vm[vm.tipo_de_recurso == "CONVENCIONAL"]
    assert conv.anio.min() == 2022
    pct = (vm[vm.anio >= 2022].groupby(["anio"]).apply(lambda d: 100 * d[d.tipo_de_recurso == "CONVENCIONAL"].bbl.sum() / d.bbl.sum()))
    assert pct.max() < 0.2 and round(pct.loc[2022], 3) == 0.196
    assert round(vm[(vm.anio == 2022) & (vm.tipo_de_recurso == "CONVENCIONAL")].bbl.sum(), 1) == 173_589.8
    assert round(vm[(vm.anio == 2025) & (vm.tipo_de_recurso == "NO CONVENCIONAL")].bbl.sum(), 1) == 183_076_385.1


def test_produccion_nc_junio_2026_es_dato_disponible(vm_raw_data):
    """D3: la tarjeta de jun-2026 se calcula con el archivo NC (solo no convencional)."""
    nc = vm_raw_data["nc"]
    j = nc[(nc.anio == 2026) & (nc.mes == 6)]
    assert round(j.prod_pet.sum() * H.BBL_PER_M3 / 30, 1) == 633_371.1
    j25 = nc[(nc.anio == 2025) & (nc.mes == 6)]
    assert round(100 * ((j.prod_pet.sum() / 30) / (j25.prod_pet.sum() / 30) - 1), 1) == 33.0


def test_coordenadas_pozos(vm_raw_data, clean_ok):
    c = H.clean("dim_pozo_coordenadas_no_convencional.csv")
    cl = H.clean("fact_produccion_pozo_mes_vaca_muerta.csv")
    nc_pozos = set(cl[cl.tipo_de_recurso == "NO CONVENCIONAL"].idpozo)
    assert len(c) == 3335 and len(nc_pozos) == 3062 and nc_pozos <= set(c.idpozo)
    assert cl.idpozo.nunique() == 3300 and cl.idpozo.nunique() - len(nc_pozos) == 238
    assert len(H.web("produccion_mapa.csv")) == 3062
