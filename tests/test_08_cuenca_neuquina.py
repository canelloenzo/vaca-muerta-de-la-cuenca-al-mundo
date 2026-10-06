"""Fase 2 (D1, D3; F1, F6, F7, F8): producción total de la cuenca, exportación por terminal, índices, serie nacional y KPIs.
Todo se recalcula de forma independiente desde raw/ y se compara con lo que escribe scripts/11_series_cuenca_neuquina.py."""
import json

import numpy as np
import pandas as pd
import pytest

import helpers as H

KPIS = lambda: json.loads((H.WEB / "kpis_resumen.json").read_text(encoding="utf-8"))


def _prod_clean():
    d = H.clean("produccion_cuenca_neuquina_mensual.csv")
    d["fecha"] = pd.to_datetime(d.fecha)
    return d.set_index("fecha")


def _expo():
    w = H.web("exportacion_cuenca_neuquina_mensual.csv")
    w["fecha"] = pd.to_datetime(w.fecha)
    return w.set_index("fecha")


# ----------------------------------------------------------------------------- A. producción de la cuenca
def test_alcance_de_la_serie_vm(clean_ok):
    cl = H.clean("fact_produccion_pozo_mes_vaca_muerta.csv")
    assert set(cl.formacion) == {"vaca muerta"} and set(cl.cuenca) == {"NEUQUINA"}
    assert set(cl.provincia) == {"Neuquén", "Mendoza", "Rio Negro"}
    assert pd.to_datetime(cl.fecha).min() == pd.Timestamp("2006-01-01")


@pytest.mark.parametrize("anio,total,vm_pct", [(2022, 20_440_333.3, 69.1), (2023, 23_829_600.0, 74.5),
                                               (2024, 28_312_024.6, 79.6), (2025, 34_360_570.2, 84.8)])
def test_produccion_total_de_la_cuenca(raw, clean_ok, anio, total, vm_pct):
    c = H.cuenca_raw()
    t = c["anual"][c["anual"].index.year == anio].sum()
    v = c["anual_vm"][c["anual_vm"].index.year == anio].sum()
    assert abs(t - total) < 0.5
    assert round(100 * v / t, 1) == vm_pct
    pm = _prod_clean()
    assert abs(pm.loc[str(anio), "prod_cuenca_total_m3"].sum() - t) < 1e-3


def test_total_de_la_cuenca_solo_existe_desde_2022(raw, clean_ok):
    c = H.cuenca_raw()
    assert c["anual_conv"].index.min().year == 2022              # no hay convencional antes de 2022 en raw/
    pm = _prod_clean()
    assert pm.loc[:"2021-12-01", "prod_cuenca_total_m3"].isna().all()
    assert pm.loc["2022-01-01":"2025-12-01", "prod_cuenca_total_m3"].notna().all()
    assert pm.loc["2026-01-01":, "prod_cuenca_total_m3"].isna().all()


def test_no_convencional_de_la_cuenca_coincide_entre_archivos(raw):
    c = H.cuenca_raw()
    a = c["nc_anual"].loc["2022-01-01":"2025-12-01"]
    b = c["nc"].loc["2022-01-01":"2025-12-01"]
    assert np.allclose(a.values, b.values, atol=1e-6)


def test_produccion_vm_clean_igual_a_raw_hasta_2025(raw, clean_ok, vm):
    pm = _prod_clean()
    esp = vm.groupby("fecha").prod_pet.sum()
    assert np.allclose(pm.loc["2006-01-01":"2025-12-01", "prod_vm_m3"].values, esp.values, atol=1e-6)


# ----------------------------------------------------------------------------- D1. exportación por terminal
def test_exportacion_terminales_igual_recalculo(export_raw):
    w = _expo()
    ind = H.export_neuquina_mensual(export_raw)
    con = w[w.estado == "con_exportacion"]
    assert set(ind.index) == set(con.index)
    assert np.allclose(con.exportacion_m3.loc[ind.index], ind, atol=0.01)
    assert np.allclose(con.exportacion_terminales_bbl_dia.loc[ind.index], H.bbl_dia(ind, ind.index), atol=0.01)


def test_meses_sin_dato_son_vacios_y_los_ceros_son_ceros_reportados(export_raw):
    w = _expo()
    r = H.p21_raw().drop_duplicates()
    r = r[r.empresa.isin(H.OPERADORES_NEUQUINOS)].copy()
    r["fecha"] = pd.to_datetime(dict(year=r.anio, month=r.mes, day=1))
    for f, row in w.iterrows():
        hay_filas = (r.fecha == f).any()
        if row.estado == "sin_dato":
            assert not hay_filas and pd.isna(row.exportacion_terminales_bbl_dia)
        elif row.estado == "sin_exportacion_reportada":
            assert hay_filas and row.exportacion_m3 == 0 and not ((r.fecha == f) & (r.tipo_operacion == "Exportacion")).any()
        else:
            assert row.exportacion_m3 > 0


def test_oleoducto_a_chile_va_aparte_y_no_se_suma(raw, export_raw):
    w = _expo()
    t = H.p20_raw()
    o = t[(t.idducto == 379) & (t.tipo_operacion == "Exportacion") & (t.tipo_producto == "Petroleo")].copy()
    o["fecha"] = pd.to_datetime(dict(year=o.anio, month=o.mes, day=1))
    m = o.groupby("fecha").volumen.sum()
    col = w.exportacion_oleoducto_chile_m3.dropna()
    assert len(col) == len(m) == 38 and col.index.min() == pd.Timestamp("2023-05-01")
    assert np.allclose(col.loc[m.index], m, atol=0.01)
    assert round(m[m.index.year == 2025].sum() * H.BBL_PER_M3 / 365, 1) == 79_998.3
    # la serie principal NO incluye el oleoducto
    ind = H.export_neuquina_mensual(export_raw)
    assert np.allclose(w.exportacion_m3.loc[ind.index], ind, atol=0.01)


# ----------------------------------------------------------------------------- comparación, % exportado, MA12
@pytest.mark.parametrize("anio,esperado", [(2022, 20.8), (2023, 19.4), (2024, 18.2), (2025, 28.1)])
def test_pct_exportado_de_la_cuenca(raw, export_raw, anio, esperado):
    c = H.cuenca_raw()["anual"]
    e = H.export_neuquina_mensual(export_raw)
    pct = 100 * e[e.index.year == anio].sum() / c[c.index.year == anio].sum()
    assert round(pct, 1) == esperado
    an = H.web("comparacion_anual.csv").set_index("anio")
    assert abs(an.loc[anio, "pct_exportado_cuenca"] - pct) < 0.01


def test_la_razon_con_la_cuenca_no_se_publica_antes_de_2022():
    an = H.web("comparacion_anual.csv").set_index("anio")
    assert an.loc[2019:2021, "pct_exportado_cuenca"].isna().all() and an.loc[2019:2021, "prod_cuenca_bbl_dia"].isna().all()
    c = H.web("comparacion_produccion_exportacion.csv")
    assert c[c.fecha < "2022-01-01"].pct_exportado_cuenca.isna().all()


def test_comparacion_cierra_en_dic_2025_y_ma12_es_media_de_12_meses():
    c = H.web("comparacion_produccion_exportacion.csv")
    c["fecha"] = pd.to_datetime(c.fecha)
    assert c.fecha.max() == pd.Timestamp("2025-12-01")
    s = c.set_index("fecha")
    for col in ("prod_vm", "prod_cuenca", "exportacion_terminales"):
        esp = s[f"{col}_bbl_dia"].rolling(12, min_periods=12).mean()
        got = s[f"{col}_ma12_bbl_dia"]
        assert np.allclose(esp.dropna(), got.dropna(), atol=0.01) and esp.isna().equals(got.isna())
    assert s.prod_cuenca_ma12_bbl_dia.first_valid_index() == pd.Timestamp("2022-12-01")


def test_ma12_de_diciembre_2025_recalculado_desde_raw(raw, export_raw, vm):
    ind = H.export_neuquina_mensual(export_raw)
    e = H.bbl_dia(ind.loc["2025-01-01":"2025-12-01"], ind.loc["2025-01-01":"2025-12-01"].index).mean()
    s = H.web("comparacion_produccion_exportacion.csv").set_index("fecha")
    assert abs(s.loc["2025-12-01", "exportacion_terminales_ma12_bbl_dia"] - e) < 0.01
    c = H.cuenca_raw()["anual"].loc["2025-01-01":"2025-12-01"]
    pc = H.bbl_dia(c, c.index).mean()
    assert round(100 * e / pc, 1) == round(s.loc["2025-12-01", "pct_exportado_cuenca_ma12"], 1) == 28.0


# ----------------------------------------------------------------------------- índice: año base y sensibilidad
def test_anio_base_por_criterio_explicito(raw, vm, export_raw):
    ind = H.export_neuquina_mensual(export_raw)
    prod = vm.groupby("anio").prod_pet.sum()
    cumple = [y for y in range(2019, 2026)
              if int((ind[ind.index.year == y] > 0).sum()) == 12 and ind[ind.index.year == y].sum() / prod[y] >= 0.10]
    assert cumple[0] == 2022
    k = KPIS()
    assert k["indice_anio_base"] == 2022 and k["indice_sensibilidad_bases"] == [2021, 2022, 2023]
    assert "12 de 12" in k["indice_criterio_base"] and "10%" in k["indice_criterio_base"]
    assert k["indice_meses_con_exportacion_por_anio"]["2021"] == 11 and k["indice_meses_con_exportacion_por_anio"]["2022"] == 12


def test_indices_anuales_y_sensibilidad(raw, vm, export_raw):
    ind = H.export_neuquina_mensual(export_raw)
    c = H.cuenca_raw()["anual"]
    def prom(s, y):
        s = s[s.index.year == y]
        return s.sum() * H.BBL_PER_M3 / int(np.sum(s.index.days_in_month))
    an = H.web("comparacion_anual.csv").set_index("anio")
    for b in (2021, 2022, 2023):
        assert an.loc[b, f"idx_exportacion_terminales_base{b}"] == 100.0 and an.loc[b, f"idx_produccion_vm_base{b}"] == 100.0
    e = {y: prom(ind, y) for y in (2022, 2023, 2025)}   # 2021 tiene un mes en cero reportado (se verifica aparte)
    assert round(100 * e[2025] / e[2022], 1) == round(an.loc[2025, "idx_exportacion_terminales_base2022"], 1) == 227.0
    pv = vm.groupby("fecha").prod_pet.sum()
    assert round(100 * prom(pv, 2025) / prom(pv, 2022), 1) == round(an.loc[2025, "idx_produccion_vm_base2022"], 1) == 206.4
    assert round(100 * prom(c, 2025) / prom(c, 2022), 1) == round(an.loc[2025, "idx_produccion_cuenca_base2022"], 1) == 168.1
    assert np.isnan(an.loc[2025, "idx_produccion_cuenca_base2021"])
    largo = H.web("indices_sensibilidad.csv")
    assert len(largo) == 3 * 3 * 7 and set(largo.base) == {2021, 2022, 2023}
    x = largo[(largo.base == 2023) & (largo.serie == "exportacion_terminales") & (largo.anio == 2025)].indice.iloc[0]
    assert round(x, 1) == round(an.loc[2025, "idx_exportacion_terminales_base2023"], 1)


# ----------------------------------------------------------------------------- D3: tarjeta de producción jun-2026
def test_tarjeta_produccion_jun_2026_solo_no_convencional(vm_raw_data):
    nc = vm_raw_data["nc"]
    j = nc[(nc.anio == 2026) & (nc.mes == 6)].prod_pet.sum()
    j25 = nc[(nc.anio == 2025) & (nc.mes == 6)].prod_pet.sum()
    k = KPIS()
    assert k["fecha_ultimo_mes_produccion"] == "2026-06-01" and k["corte_comparaciones"] == "2025-12-01"
    assert k["produccion_ultimo_mes_bbl_dia"] == round(j * H.BBL_PER_M3 / 30, 1) == 633_371.1
    assert k["variacion_interanual_produccion_pct"] == round(100 * (j / j25 - 1), 1) == 33.0
    assert "no convencional" in k["produccion_alcance"].lower()
    assert k["produccion_vm_dic_2025_bbl_dia"] == 590_754.6 and k["variacion_interanual_vm_dic_2025_pct"] == 31.92


# ----------------------------------------------------------------------------- F7: serie nacional con NO IDENTIFICADO
def test_serie_nacional_por_terminal_con_no_identificado(export_raw):
    g = H.web("exportacion_nacional_por_terminal_anual.csv")
    tot = g[g.operador_terminal == "TOTAL"].set_index("anio")
    assert abs(tot.volumen_total_m3.sum() - 53_755_750.1) < 0.5          # el CSV redondea cada fila a 2 decimales
    assert round(tot.volumen_no_identificado_m3.sum()) == 15_044_986
    por_anio = export_raw[export_raw.pais == "NO IDENTIFICADO"].groupby("anio").volumen.sum()
    assert np.allclose(tot.volumen_no_identificado_m3.loc[por_anio.index], por_anio, atol=0.01)
    assert round(tot.loc[2019, "pct_no_identificado"]) == 79 and round(tot.loc[2026, "pct_no_identificado"]) == 4
    ops = g[g.operador_terminal != "TOTAL"].groupby("anio").volumen_total_m3.sum()
    assert np.allclose(ops.values, tot.volumen_total_m3.values, atol=0.1)
    term = g[(g.operador_terminal == "TERMAP S.A.")]
    assert (term.volumen_con_pais_m3 == 0).all()                  # TERMAP no identifica ningún destino
    assert KPIS()["pct_con_pais_identificado"] == 72.01 and KPIS()["pct_no_identificado"] == 27.99


def test_serie_nacional_por_pais_incluye_no_identificado(export_raw):
    p = H.web("exportacion_nacional_por_pais_anual.csv")
    assert round(p.volumen_m3.sum(), 0) == round(export_raw.volumen.sum(), 0)
    assert round(p[p.pais == "NO IDENTIFICADO"].volumen_m3.sum()) == 15_044_986


# ----------------------------------------------------------------------------- F8: concentración
def test_concentracion_por_operador_y_por_cargador(export_raw):
    per = export_raw[export_raw.anio.between(2020, 2025)]
    c = H.web("concentracion_exportacion_2020_2025.csv")
    op = c[c.nivel == "operador_terminal"].head(3).pct.sum()
    assert round(op, 2) == 94.25 == KPIS()["concentracion_top3_operadores_terminal_pct_2020_2025"]

    def grupo(x):
        n = H.norm(x)
        return "vista" if "vista" in n else ("pan american" if "pan american" in n else n)
    v = per.groupby(per.cargador.map(grupo)).volumen.sum().sort_values(ascending=False)
    top3 = 100 * v.head(3).sum() / v.sum()
    assert round(top3, 2) == KPIS()["concentracion_top3_cargadores_pct_2020_2025"] == 47.02
    car = c[c.nivel == "cargador"]
    assert round(car.pct.sum(), 1) == 100.0
    assert car.nombre.str.contains("VISTA").sum() == 1 and car.nombre.str.contains("PAN AMERICAN").sum() == 1


def test_volatilidad_publicada(raw, vm, export_raw):
    k = KPIS()
    ind = H.export_neuquina_mensual(export_raw)
    e = H.bbl_dia(ind.loc["2022-01-01":"2025-12-01"], ind.loc["2022-01-01":"2025-12-01"].index)
    p = H.monthly_bbl_dia(vm).loc["2022-01-01":"2025-12-01"]
    assert round(e.pct_change().dropna().std() * 100, 2) == k["volatilidad_mensual_2022_2025_exportacion_terminales_pct"] == 34.02
    assert round(p.pct_change().dropna().std() * 100, 2) == k["volatilidad_mensual_2022_2025_produccion_vm_pct"] == 2.55
    assert k["volatilidad_mensual_2020_2025_exportacion_nacional_terminales_pct"] == 76.85
    assert k["volatilidad_mensual_2020_2025_produccion_vm_pct"] == 5.18


# ----------------------------------------------------------------------------- F18: coordenadas dudosas
def test_pozos_con_coordenadas_dudosas(clean_ok):
    co = H.clean("dim_pozo_coordenadas_no_convencional.csv")
    pz = H.clean("fact_produccion_pozo_mes_vaca_muerta.csv")
    area = pz.sort_values("fecha").groupby("idpozo").areayacimiento.last()
    m = co.assign(area=co.idpozo.map(area)).dropna(subset=["area"])
    med = m.groupby("area")[["coordenadax", "coordenaday"]].median()
    mm = m.join(med, on="area", rsuffix="_med")
    p1, p2 = np.radians(mm.coordenaday), np.radians(mm.coordenaday_med)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(mm.coordenadax_med - mm.coordenadax) / 2) ** 2
    d = 2 * 6371.0 * np.arcsin(np.sqrt(a))
    esperado = set(mm[d > 30].idpozo)
    w = H.web("pozos_coordenadas_dudosas.csv")
    assert set(w.idpozo) == esperado == {153751, 159086}
    assert abs(w.set_index("idpozo").loc[153751, "distancia_a_mediana_del_yacimiento_km"] - 47.3) < 0.1
    assert abs(w.set_index("idpozo").loc[159086, "distancia_a_mediana_del_yacimiento_km"] - 41.5) < 0.1
    assert (d.quantile(0.999) < 30) and len(m) == 3062          # el umbral separa a los dos extremos del resto
