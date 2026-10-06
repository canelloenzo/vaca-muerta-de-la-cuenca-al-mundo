"""2.1, 2.6 y 2.7 de la auditoría: transporte y utilización de ductos, recalculados desde raw/ (planilla 20 + Anexo 2A)."""
import numpy as np
import pandas as pd
import pytest

import helpers as H

EXCL = H.DUCTOS_EXCLUIDOS_ORIGINAL


def test_planilla20_raw_igual_clean(raw, clean_ok):
    r = H.p20_raw()
    c = H.clean("fact_transporte_ductos.csv")
    assert len(r) == len(c) == 56_566 and not r.duplicated().any()
    assert abs(r.volumen.sum() - c.volumen.sum()) < 1e-3


def test_universo_de_ductos(raw):
    t = H.p20_raw()
    assert t.idducto.nunique() == 133
    assert t[t.volumen > 0].idducto.nunique() == 129
    assert t[(t.volumen > 0) & (t.tipo_producto == "Petroleo")].idducto.nunique() == 84


def test_fact_capacidad_reconciliada(util, clean_ok):
    c = H.clean("fact_capacidad_ductos.csv")
    m = util.merge(c, on=["idducto", "anio", "mes"], how="outer", indicator=True)
    assert (m._merge == "both").all() and len(m) == 3603
    assert (m.vol_total - m.volumen_transportado).abs().max() < 1e-4
    assert (m.op * m.dias - m.capacidad_mensual_m3).abs().max() < 1e-4


def test_capacidad_valida_es_operativa_positiva(clean_ok):
    c = H.clean("fact_capacidad_ductos.csv")
    assert (c.capacidad_valida == (c.capacidad_operativa_maxima_m3_dia > 0)).all()


@pytest.mark.parametrize("ducto,anio", [(329, 2022), (329, 2023), (329, 2024), (171, 2023), (97, 2022)])
def test_utilizacion_absurda_era_mezcla_de_gas(util, ducto, anio):
    """F3: con solo líquidos, los ductos 97/171/329 quedan por debajo de 100% en los años 'absurdos'."""
    d = util[(util.idducto == ducto) & (util.anio == anio)]
    assert H.utilizacion(d, "vol_total") > 300
    assert H.utilizacion(d, "vol_liq") < 100


def test_vmoc_segmento_unico(util):
    """F2: VMOC 2025 -> 171,1% (todo) / 123,3% (segmento más cargado) / 89,3% contra capacidad de diseño."""
    d = util[(util.idducto == 539) & (util.anio == 2025)]
    assert len(d) == 8
    assert round(H.utilizacion(d, "vol_total"), 1) == 171.1
    assert round(H.utilizacion(d, "vol_segmax"), 1) == 123.3
    assert round(H.utilizacion(d, "vol_segmax", "dis"), 1) == 89.3
    assert (d.nseg == 2).all() and (d.op == 25349).all() and (d.dis == 35000).all() and (d.emp == 17399).all()


def _por_ducto(util, num, cap="op", ultimo=True, excluir=EXCL):
    u = util[(util[cap] > 0) & ~util.idducto.isin(excluir)]
    out = {}
    for i, d in u.groupby("idducto"):
        if ultimo:
            d = d[d.anio == d.anio.max()]
        out[i] = H.utilizacion(d, num, cap)
    return pd.Series(out)


def test_conteo_de_ductos_sobre_100_segun_definicion(util):
    """Tabla de F2: 57 ductos; sobre 100% -> año más reciente 6 (todo) / 5 (segmento máx); acumulado 3 / 3."""
    ult_total = _por_ducto(util, "vol_total", ultimo=True)
    assert len(ult_total) == 57
    assert int((ult_total > 100).sum()) == 6
    assert int((_por_ducto(util, "vol_segmax", ultimo=True) > 100).sum()) == 5
    assert int((_por_ducto(util, "vol_total", ultimo=False) > 100).sum()) == 3
    assert int((_por_ducto(util, "vol_segmax", ultimo=False) > 100).sum()) == 3


def test_capacidades_sospechosas_documentadas(raw):
    """F5: hechos de datos que sostienen las reglas de capacidad dudosa."""
    ca = H.anexo2a_raw().groupby(["idducto", "anio"]).agg(op=("capacidad_operativa_maxima", "first"),
                                                          dis=("capacidad_disenio", "first"),
                                                          emp=("capacidad_empleada", "first")).reset_index()
    d166 = ca[ca.idducto == 166].set_index("anio").op
    assert d166.loc[2023] == 1800 and d166.loc[2024] == 38
    trip = ca[ca.op > 0].groupby(["op", "dis", "emp"]).idducto.nunique()
    assert trip.loc[(1800.0, 1800.0, 1087.0)] == 3
    r = ca[(ca.idducto == 216) & (ca.anio == 2024)].iloc[0]
    assert r.op == r.dis == r.emp == 36000


def test_universo_petrolero_y_capacidad(raw, util):
    """F4: de los 84 ductos que mueven petróleo, cuántos tienen capacidad válida (sin los 6 excluidos) o no."""
    t = H.p20_raw()
    pet = set(t[(t.volumen > 0) & (t.tipo_producto == "Petroleo")].idducto)
    con_cap = set(util[util.op > 0].idducto)
    assert len(pet & (con_cap - EXCL)) == 44
    assert len(pet & EXCL & con_cap) == 5
    assert len(pet - set(util.idducto)) == 35
