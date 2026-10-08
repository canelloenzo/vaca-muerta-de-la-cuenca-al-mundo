"""Serie principal de exportación (comercio exterior) y producción oficial de la cuenca: recálculo independiente
(otro método de lectura de la caché de la tabla dinámica) y verificación de cada afirmación publicada sobre esas series."""
import html
import re
import zipfile

import numpy as np
import pandas as pd
import pytest

import helpers as H

XLSX = "TD_comercioexterior_actualizado_2026-09-24.xlsx"
SERIE = "serie-historica-produccion-petroleo-por-cuenca-subtipo-capitulo-iv.csv"
BBL = 6.2898


@pytest.fixture(scope="session")
def comex_indep(raw):
    """Lectura con expresiones regulares (el script 16 usa ElementTree): devuelve todas las filas de exportación de la cuenca Neuquina."""
    path = H.raw_dir() / XLSX
    if not path.exists():
        pytest.skip(f"falta {XLSX} en raw/")

    def build():
        z = zipfile.ZipFile(path)
        d = z.read("xl/pivotCache/pivotCacheDefinition1.xml").decode("utf-8")
        campos = []
        for m in re.finditer(r'<cacheField name="([^"]*)"[^>]*?(?:/>|>(.*?)</cacheField>)', d, re.S):
            items = re.findall(r'<(?:s|n)\s+v="([^"]*)"', m.group(2) or "")
            campos.append((m.group(1), [html.unescape(i) for i in items] or None))
        nombres = [n for n, _ in campos]
        xml = z.read("xl/pivotCache/pivotCacheRecords1.xml").decode("utf-8")
        filas = []
        for rec in re.finditer(r"<r>(.*?)</r>", xml, re.S):
            celdas = re.findall(r'<(x|n|s|m|d)(?: v="([^"]*)")?\s*/>', rec.group(1))
            fila = []
            for k, (t, v) in enumerate(celdas):
                if t == "x":
                    fila.append(campos[k][1][int(v)])
                elif t == "m":
                    fila.append(None)
                else:
                    fila.append(html.unescape(v))
            filas.append(fila)
        df = pd.DataFrame(filas, columns=nombres)
        for c in ("anio", "mes", "cantidad", "monto"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df

    return H._cached("comex_indep_v1", [path], build)


def _neu(df):
    return df[(df.tipodecomercializacion == "Exportación") & df["producto"].str.startswith("Cuenca Neuquina", na=False)]


def test_registros_totales_y_de_exportacion_de_crudo(comex_indep):
    r = H.web_json("registro_cifras.json")
    assert len(comex_indep) == 798_045
    cuenca = comex_indep[(comex_indep.tipodecomercializacion == "Exportación") & comex_indep["producto"].str.startswith("Cuenca", na=False)]
    assert len(cuenca) == r["comex_registros_n"]["valor"]
    assert set(comex_indep[comex_indep["producto"].str.startswith("Cuenca", na=False)].unidad) == {"(m3)"}


def test_exportacion_anual_igual_recalculo(comex_indep):
    a = H.web("comex_anual.csv").set_index("anio")
    n = _neu(comex_indep).groupby("anio").agg(m3=("cantidad", "sum"), usd=("monto", "sum"))
    for y in range(2020, 2027):
        assert abs(n.loc[y, "m3"] - a.loc[y, "exportacion_m3"]) < 0.5, y
        assert abs(n.loc[y, "usd"] - a.loc[y, "exportacion_usd"]) < 50, y
    assert round(n.loc[2025, "m3"]) == 11_113_169


def test_precio_implicito_anual(comex_indep):
    n = _neu(comex_indep).groupby("anio").agg(m3=("cantidad", "sum"), usd=("monto", "sum"))
    px = n.usd / (n.m3 * BBL)
    assert {y: round(px.loc[y], 1) for y in (2020, 2021, 2022, 2023, 2024, 2025, 2026)} == {2020: 34.3, 2021: 68.8, 2022: 92.5, 2023: 76.1, 2024: 76.0, 2025: 64.9, 2026: 83.1}
    assert 20 < px.min() and px.max() < 120, "precio implícito fuera de un rango plausible"


def test_validacion_contra_precio_fob_oficial(raw):
    v = H.web("comex_validacion_precios.csv")
    assert len(v) == 9
    assert v.usd_por_bbl.corr(v.medanito_fob_oficial) > 0.98
    assert abs((100 * (v.usd_por_bbl / v.medanito_fob_oficial - 1)).mean()) < 3


def test_produccion_oficial_de_la_cuenca(raw):
    o = pd.read_csv(H.raw_dir() / SERIE, encoding="utf-8-sig")
    o["fecha"] = pd.to_datetime(o.indice_tiempo + "-01")
    assert o.fecha.min() == pd.Timestamp("2006-01-01") and not o.fecha.duplicated().any()
    a = H.web("comex_anual.csv").set_index("anio")
    m3 = o.groupby(o.fecha.dt.year).cuenca_neuquina.sum()
    for y in range(2020, 2026):
        assert abs(a.loc[y, "prod_cuenca_bbl_dia"] - m3.loc[y] * BBL / (366 if y % 4 == 0 else 365)) < 0.5, y
    assert {y: round(m3.loc[y] / 1e6, 2) for y in range(2022, 2026)} == {2022: 20.44, 2023: 23.83, 2024: 28.47, 2025: 34.36}


def test_septiembre_2024_unica_diferencia_de_produccion_por_pozo(raw):
    o = pd.read_csv(H.raw_dir() / SERIE, encoding="utf-8-sig")
    o["fecha"] = pd.to_datetime(o.indice_tiempo + "-01")
    o = o.set_index("fecha")
    pm = H.clean("produccion_cuenca_neuquina_mensual.csv", parse_dates=["fecha"]).set_index("fecha")
    d = (o.cuenca_neuquina - pm.prod_cuenca_total_m3).loc["2022-01-01":"2025-12-01"]
    assert abs(d.loc["2024-09-01"] - 157_933.4) < 1
    assert d.drop(pd.Timestamp("2024-09-01")).abs().max() < 50


def test_comercio_exterior_vs_terminales_menos_de_3pct_hasta_2022():
    a = H.web("comex_anual.csv").set_index("anio")
    assert all(abs(a.loc[y, "razon_comex_sobre_terminales"] - 1) < 0.03 for y in (2020, 2021, 2022))
    assert all(a.loc[y, "razon_comex_sobre_terminales_mas_oleoducto"] < 0.9 for y in (2023, 2024, 2025))     # las fuentes no concilian desde 2023
    assert all(a.loc[y, "razon_comex_sobre_terminales"] > 1.1 for y in (2023, 2024, 2025))


def test_afirmacion_exportacion_crece_mas_que_produccion_de_la_cuenca():
    """Texto publicado: con las bases 2021, 2022 y 2023, en cada año posterior a la base, el índice de exportación supera al de la producción de la cuenca;
    en 2025 también al de Vaca Muerta."""
    a = H.web("comex_anual.csv").set_index("anio")
    for b in (2021, 2022, 2023):
        for y in range(b + 1, 2026):
            assert a.loc[y, f"idx_exportacion_base{b}"] > a.loc[y, f"idx_produccion_cuenca_base{b}"], (b, y)
        assert a.loc[2025, f"idx_exportacion_base{b}"] > a.loc[2025, f"idx_produccion_vm_base{b}"], b


def test_afirmacion_vale_con_las_dos_fuentes_y_las_tres_bases():
    """Texto publicado: con comercio exterior y con terminales + oleoducto a Chile, el índice de exportación supera al de la producción de la cuenca
    en cada año posterior a la base (bases 2021, 2022 y 2023) y el % exportado sube cada año de 2022 a 2025."""
    a = H.web("comex_anual.csv").set_index("anio")
    for b in (2021, 2022, 2023):
        for y in range(b + 1, 2026):
            for col in ("idx_exportacion", "idx_exportacion_alt"):
                assert a.loc[y, f"{col}_base{b}"] > a.loc[y, f"idx_produccion_cuenca_base{b}"], (col, b, y)
    for col in ("pct_exportado_cuenca", "alt_pct_exportado_cuenca"):
        assert all(a.loc[y, col] < a.loc[y + 1, col] for y in range(2020, 2025)), col


def test_validacion_del_valor_en_usd_contra_el_brent():
    v = H.web("comex_validacion_brent.csv")
    r = H.web_json("registro_cifras.json")
    assert len(v) == r["val_brent_meses"]["valor"] == 65 and v.fecha.max() <= "2025-12-01"
    assert v.usd_por_bbl.corr(v.brent) > 0.95
    assert 0 < r["val_brent_dif_min"]["valor"] < r["val_brent_dif_max"]["valor"] < 10        # el precio implícito queda por debajo del Brent cada año


def test_porcentaje_exportado_de_la_cuenca():
    a = H.web("comex_anual.csv").set_index("anio")
    assert {y: round(a.loc[y, "pct_exportado_cuenca"], 1) for y in range(2020, 2026)} == {2020: 7.6, 2021: 10.1, 2022: 20.5, 2023: 22.1, 2024: 24.5, 2025: 32.3}
    assert a.loc[2022, "meses_con_exportacion"] == 12 and a.loc[2021, "meses_con_exportacion"] == 11 and a.loc[2020, "meses_con_exportacion"] == 6


def test_anio_base_2022_cumple_el_criterio():
    a = H.web("comex_anual.csv").set_index("anio")
    ok = a[(a.meses_con_exportacion == 12) & (a.pct_exportado_cuenca >= 10) & (~a.anio_parcial.astype(bool))]
    assert ok.index.min() == 2022


def test_destinos_y_concentracion_publicados(comex_indep):
    n = _neu(comex_indep)
    tot = n.groupby(n.pais.str.upper()).cantidad.sum().sort_values(ascending=False)
    r = H.web_json("registro_cifras.json")
    assert tot.index[0] == "ESTADOS UNIDOS" and tot.index[1] == "CHILE"
    assert abs(100 * tot["ESTADOS UNIDOS"] / tot.sum() - r["comex_eeuu_pct"]["valor"]) < 0.01
    per = n[n.anio.between(2020, 2025)].groupby("empresa").cantidad.sum().sort_values(ascending=False)
    assert abs(100 * per.head(3).sum() / per.sum() - r["conc_exp_top3_sin_agrupar_pct"]["valor"]) < 0.01
    # el agrupado por razón social solo puede aumentar la concentración
    assert r["conc_exp_top3_pct"]["valor"] >= r["conc_exp_top3_sin_agrupar_pct"]["valor"]


def test_html_igual_a_las_tablas_comex(DATA):
    p = H.web("comex_neuquina_por_pais_anual.csv")
    p = p[~p.pais.str.upper().str.startswith("SIN PAIS")]
    tot = p.groupby("pais").volumen_m3.sum().sort_values(ascending=False)
    top = [r for r in DATA["paises_rank"] if not r["pais"].startswith("Otros")]
    assert [r["pais"] for r in top] == list(tot.head(10).index)
    assert all(abs(r["vol"] - tot[r["pais"]]) < 0.2 for r in top)
    otros = [r for r in DATA["paises_rank"] if r["pais"].startswith("Otros")][0]["vol"]
    assert abs(otros - tot.iloc[10:].sum()) < 0.5
    c = H.web("comex_neuquina_concentracion_2020_2025.csv")
    ag = c[c.nivel == "empresa_agrupada"].head(6)
    assert [r["e"] for r in DATA["exportadores"]] == [n.upper() for n in ag.nombre] and [r["pct"] for r in DATA["exportadores"]] == list(ag.pct)
    m = H.web("comex_comparacion_mensual.csv").dropna(subset=["idx_produccion_vm_ma12_base2022"])
    assert len(DATA["ma12"]) == len(m) and DATA["ma12"][-1]["m"] == "2025-12"
    assert abs(DATA["ma12"][-1]["exp"] - m.iloc[-1].idx_exportacion_ma12_base2022) < 0.01


def test_terminales_informan_mas_que_comercio_exterior_en_los_destinos_citados(comex_indep, export_raw):
    """Texto publicado: para Estados Unidos, Brasil, Perú y Uruguay los terminales marítimos informan más volumen que el comercio exterior (2023-2025)."""
    n = _neu(comex_indep)
    n = n.assign(p=n.pais.str.upper().str.replace("Ú", "U"))
    t = export_raw[export_raw.empresa.isin(H.OPERADORES_NEUQUINOS)].copy()
    t["p"] = t.pais.fillna("").str.upper().str.replace("Ú", "U")
    for pais in ("ESTADOS UNIDOS", "BRASIL", "PERU", "URUGUAY"):
        c = n[(n.p == pais) & n.anio.between(2023, 2025)].cantidad.sum()
        v = t[(t.p == pais) & t.anio.between(2023, 2025)].volumen.sum()
        assert v > c, (pais, v, c)


def test_acumulado_no_converge_y_septiembre_2024_es_shell(comex_indep):
    a = H.web("comex_anual.csv").set_index("anio")
    ac = a.loc[2020:2025, "exportacion_m3"].sum() / (a.loc[2020:2025, "terminales_m3"].sum() + a.loc[2020:2025, "oleoducto_chile_planilla20_m3"].sum())
    assert 0.8 < ac < 0.9
    d = pd.read_csv(H.raw_dir() / "produccin-de-pozos-de-gas-y-petrleo-2024.csv", encoding="latin-1", low_memory=False)
    d.columns = [c.replace("\ufeff", "").replace("ï»¿", "").strip().lower() for c in d.columns]
    d = d[d.cuenca.astype(str).str.lower().str.contains("neuquina") & d.empresa.str.contains("SHELL ARGENTINA", na=False)]
    por_mes = d.groupby("mes").prod_pet.sum()
    assert por_mes.get(9, 0) == 0 and por_mes[8] > 100_000 and por_mes[10] > 100_000
