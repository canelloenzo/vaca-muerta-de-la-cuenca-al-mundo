"""1.4 y 1.5 de la auditoría: exportación (planilla 21) recalculada desde raw/ y contraste con el Balance."""
import numpy as np
import pandas as pd
import pytest

import helpers as H

SIN_PAIS = {"NO IDENTIFICADO", "no aplica"}


def test_duplicados_exactos_raw_y_clean(raw, clean_ok):
    r = H.p21_raw()
    assert len(r) == 3551 and int(r.duplicated().sum()) == 8
    cl = H.clean("fact_movimientos_exportacion_ductos.csv")
    assert len(cl) == len(r.drop_duplicates()) == 3543


def test_exportacion_igual_mercado_externo(raw):
    r = H.p21_raw().drop_duplicates()
    a = r[r.tipo_operacion == "Exportacion"]
    b = r[r.tipo_mercado == "Externo"]
    assert set(a.index) == set(b.index) and len(a) == 1433


def test_volumen_total_exportado(export_raw):
    assert round(export_raw.volumen.sum(), 1) == 53_755_750.1


def test_web_por_pais_igual_recalculo(export_raw):
    con = export_raw[export_raw.pais.notna() & ~export_raw.pais.isin(SIN_PAIS)]
    rr = con.groupby(["anio", "pais"]).volumen.sum().reset_index()
    w = H.web("exportacion_nacional_por_pais_anual.csv")
    assert set(w.pais) >= {"NO IDENTIFICADO"}                       # F7: el volumen sin pais se conserva en la serie nacional
    w = w[~w.pais.isin(SIN_PAIS)]
    m = rr.merge(w, on=["anio", "pais"], how="outer", indicator=True)
    assert (m._merge == "both").all()
    assert (m.volumen - m.volumen_m3).abs().max() < 0.2          # redondeo a 1 decimal en el CSV
    assert abs(w.volumen_m3.sum() - con.volumen.sum()) < 1 and round(con.volumen.sum(), 1) == 38_710_764.2


def test_sin_pais_es_no_identificado_de_termap(export_raw):
    sin = export_raw[export_raw.pais.isna() | export_raw.pais.isin(SIN_PAIS)]
    no_id = export_raw[export_raw.pais == "NO IDENTIFICADO"]
    assert round(sin.volumen.sum()) == 15_044_986 and len(no_id) == 168
    assert set(no_id.empresa) == {"TERMAP S.A."}
    assert round(100 * (1 - sin.volumen.sum() / export_raw.volumen.sum()), 2) == 72.01


def test_concentracion_operadores_2020_2025(export_raw):
    e = export_raw[export_raw.anio.between(2020, 2025)].groupby("empresa").volumen.sum().sort_values(ascending=False)
    pct = (100 * e / e.sum()).round(2)
    assert list(pct.head(3)) == [61.08, 27.94, 5.23]
    assert round(pct.head(3).sum(), 2) == 94.25
    w = H.web("concentracion_exportacion_2020_2025.csv")
    w = w[w.nivel == "operador_terminal"]
    assert list(w.pct.head(3)) == [61.08, 27.94, 5.23]


def test_empresas_de_terminal_sin_variantes_de_nombre(export_raw):
    assert export_raw.empresa.nunique() == 6
    assert (export_raw.groupby("empresa").cuit.nunique() == 1).all()


def test_operador_neuquino_por_anio(export_raw):
    """Base de D1: volumen por año de Oiltanking + Refinería Bahía Blanca."""
    neu = export_raw[export_raw.empresa.isin(H.OPERADORES_NEUQUINOS)].groupby("anio").volumen.sum().round()
    assert neu.loc[2022] == 4_247_905 and neu.loc[2025] == 9_642_378


def _balance_petroleo(path):
    df = pd.read_excel(path, sheet_name=0, header=None)
    i = [k for k in range(len(df)) if isinstance(df.iat[k, 3], str) and df.iat[k, 3].strip() == "Petróleo"][0]
    return float(df.iat[i, 4]), -float(df.iat[i, 7])      # producción, exportación y bunker (en miles de TEP)


@pytest.mark.parametrize("anio", [2023, 2024, 2025])
def test_orden_de_magnitud_contra_balance(raw, vm, export_raw, anio):
    prod_ktep, exp_ktep = _balance_petroleo(raw / H.RAW_BALANCE[anio])
    vm_m3 = vm[vm.anio == anio].prod_pet.sum()
    ex_m3 = export_raw[export_raw.anio == anio].volumen.sum()
    for f in (0.80, 0.86, 0.95):                          # TEP por m3 de petróleo, rango explícito
        prod_nac = prod_ktep * 1000 / f
        exp_nac = exp_ktep * 1000 / f
        assert vm_m3 < prod_nac                           # Vaca Muerta no puede superar el total nacional
        assert 0.40 < vm_m3 / prod_nac < 0.75            # rango observado: 43%-67% según el factor
        assert ex_m3 < 1.10 * exp_nac                     # exportación de terminales <= Balance (+10% por unidad)
