"""1.3 de la auditoría: unicidad del grano real de cada tabla de clean/ y de data/web/."""
import pandas as pd
import pytest

import helpers as H

CLEAN_GRANOS = {
    "fact_produccion_pozo_mes_vaca_muerta.csv": ["idpozo", "fecha"],
    "fact_produccion_yacimiento_mes_vaca_muerta.csv": ["fecha", "areayacimiento", "provincia", "cuenca",
                                                       "tipo_de_recurso", "sub_tipo_recurso"],
    "fact_capacidad_ductos.csv": ["idducto", "fecha"],
    "dim_ducto.csv": ["idducto"],
    "dim_pozo_coordenadas_no_convencional.csv": ["idpozo"],
    "dim_precio_exportacion_crudo.csv": ["tipo_crudo", "tipo_precio", "fecha"],
    "dim_tipo_crudo_cuenca.csv": ["tipo_de_crudo"],
    "fact_balance_energetico_nacional.csv": ["grupo_energia", "producto", "categoria", "subcategoria", "anio"],
}
WEB_GRANOS = {
    "produccion_mapa.csv": ["idpozo"],
    "produccion_anual.csv": ["anio", "tipo_de_recurso"],
    "top_yacimientos.csv": ["areayacimiento"],
    "exportacion_por_empresa.csv": ["empresa"],
}


@pytest.mark.parametrize("fname,key", CLEAN_GRANOS.items())
def test_clean_grano_unico(clean_ok, fname, key):
    d = H.clean(fname)
    assert not d.duplicated().any(), f"{fname}: filas exactas duplicadas"
    assert not d.duplicated(key).any(), f"{fname}: clave {key} no es única"


@pytest.mark.parametrize("fname", ["fact_transporte_ductos.csv", "fact_movimientos_exportacion_ductos.csv"])
def test_clean_sin_filas_exactas_duplicadas(clean_ok, fname):
    assert not H.clean(fname).duplicated().any()


@pytest.mark.parametrize("fname,key", WEB_GRANOS.items())
def test_web_grano_unico(fname, key):
    d = H.web(fname)
    assert not d.duplicated().any()
    assert not d.duplicated(key).any()


def test_web_indices_una_fila_por_mes():
    for f in ("indices_mensuales.csv",):
        p = H.WEB / f
        if p.exists():
            assert not H.web(f).anio_mes.duplicated().any()


def test_web_pais_anio_unico():
    d = H.web("exportacion_por_pais_anual.csv")
    assert not d.duplicated(["anio", "pais"]).any()


def test_idducto_determina_la_denominacion(clean_ok):
    t = H.clean("fact_transporte_ductos.csv")
    assert (t.groupby("idducto").denominacion_ducto.nunique() == 1).all()


@pytest.mark.objetivo
def test_denominacion_normalizada_apunta_a_un_ducto_logico(clean_ok):
    """F15: tras el alias, cada denominación normalizada debe tener un único idducto_logico."""
    t = H.clean("fact_transporte_ductos.csv")
    assert "idducto_logico" in t.columns, "falta la columna idducto_logico (alias documentado)"
    k = t.denominacion_ducto.map(H.norm).str.replace(r"[^a-z0-9]", "", regex=True)
    pares = t.assign(k=k).drop_duplicates(["k", "idducto_logico"]).groupby("k").size()
    # los nombres repetidos por ductos realmente distintos se listan en el diccionario; los de F15 deben unificarse
    assert pares.loc["elcondorpuntaloyola"] == 1 and pares.loc["elcondorposesion"] == 1
