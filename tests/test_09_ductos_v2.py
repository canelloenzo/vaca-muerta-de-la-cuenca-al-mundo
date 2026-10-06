"""Fase 2 (D2; F2, F3, F4, F5, F15): numerador de líquidos, segmento más cargado, reglas de capacidad dudosa,
ranking y clasificación de los ductos que mueven petróleo. Recálculo independiente desde raw/ (planilla 20 + Anexo 2A)."""
import json

import numpy as np
import pandas as pd
import pytest

import helpers as H

ALIAS = {532: 255, 533: 122}
D2 = {(539, 2025)}


def _dudosas(util, r1=5.0):
    r = H.reglas_capacidad(util, r1=r1)
    return r, (r["R1"] | r["R3"] | r["R4"] | r["R5"] | D2)


def test_columnas_nuevas_de_fact_capacidad_igual_recalculo(util, clean_ok):
    c = H.clean("fact_capacidad_ductos.csv")
    m = util.merge(c, on=["idducto", "anio", "mes"])
    assert len(m) == 3603
    assert (m.vol_liq - m.volumen_liquidos).abs().max() < 1e-4
    assert (m.vol_gas - m.volumen_gas).abs().max() < 1e-4
    assert (m.vol_liq + m.vol_gas - m.volumen_transportado).abs().max() < 1e-4
    assert (m.vol_segmax - m.volumen_segmento_mas_cargado).abs().max() < 1e-4
    assert (m.nseg == m.n_segmentos_con_volumen).all()


def test_el_numerador_viejo_sumaba_gas(util):
    """F3: los ductos con gas en el numerador son los que daban cifras absurdas."""
    g = util[util.vol_gas > 0].groupby("idducto").vol_gas.sum()
    assert {97, 171, 329} <= set(g.index)
    assert (util[util.idducto == 329].vol_gas.sum() / util[util.idducto == 329].vol_total.sum()) > 0.99


def test_reglas_de_capacidad_dudosa_igual_implementacion_independiente(util, clean_ok):
    r, dud = _dudosas(util)
    c = H.clean("fact_capacidad_ductos.csv").drop_duplicates(["idducto", "anio"])
    present = set(zip(c.idducto, c.anio))
    got = {(i, y) for i, y, d in zip(c.idducto, c.anio, c.capacidad_dudosa) if d}
    assert got == dud & present
    rev = {(i, y) for i, y, d in zip(c.idducto, c.anio, c.a_revisar_capacidad) if d}
    assert rev == ((r["R2"] | r["R6"]) & present) - dud         # R2 y R6 solo marcan "a revisar"
    motivos = dict(zip(zip(c.idducto, c.anio), c.motivo_capacidad_dudosa.fillna("")))
    assert motivos[(539, 2025)] == "D2" and "R5" in motivos[(516, 2025)] and "R1" in motivos[(42, 2021)]


def test_sensibilidad_de_r1_5_vs_10(util):
    r5, _ = _dudosas(util, 5.0)
    r10, _ = _dudosas(util, 10.0)
    # R1 mira años consecutivos: el ducto 149 pasa de 2024 a 2026 sin dato de 2025, por eso no se marca
    assert {i for i, _ in r5["R1"]} == {42, 166, 252}
    assert {i for i, _ in r10["R1"]} == {42, 166}
    assert len(r10["R1"]) < len(r5["R1"])


def _ranking_independiente(util, r1=5.0):
    r, dud = _dudosas(util, r1)
    t = H.p20_raw()
    pet = set(t[(t.volumen > 0) & (t.tipo_producto == "Petroleo")].idducto.map(lambda i: ALIAS.get(i, i)))
    u = util[(util.op > 0) & util.idducto.map(lambda i: ALIAS.get(i, i)).isin(pet)]
    out = {}
    for i, d in u.groupby("idducto"):
        buenos = [y for y in sorted(d.anio.unique()) if (i, int(y)) not in dud]
        if buenos:
            y = buenos[-1]
            dd = d[d.anio == y]
            out[i] = (int(y), 100 * dd.vol_segmax.sum() / (dd.op * dd.dias).sum())
    return out


def test_ranking_igual_recalculo_independiente(util):
    ind = _ranking_independiente(util)
    r = H.web("utilizacion_ductos_ranking.csv")
    assert len(r) == len(ind) == 44
    got = {int(i): (int(a), u) for i, a, u in zip(r.idducto_logico, r.anio, r.utilizacion_segmento_mas_cargado_pct)}
    assert set(got) == set(ind)
    for i in ind:
        assert got[i][0] == ind[i][0] and abs(got[i][1] - ind[i][1]) < 0.06
    assert (r.utilizacion_segmento_mas_cargado_pct.diff().dropna() <= 0).all()
    assert int(r.sobre_100_pct.sum()) == sum(1 for v in ind.values() if v[1] > 100) == 3


def test_el_ranking_no_cambia_con_r1_10x(util):
    assert set(_ranking_independiente(util, 5.0)) == set(_ranking_independiente(util, 10.0))
    a, b = _ranking_independiente(util, 5.0), _ranking_independiente(util, 10.0)
    assert all(a[i][0] == b[i][0] and abs(a[i][1] - b[i][1]) < 1e-9 for i in a)


def test_ranking_no_incluye_ducto_anios_dudosos_ni_publica_su_utilizacion():
    r = H.web("utilizacion_ductos_ranking.csv")
    d = H.web("ductos_capacidad_dudosa.csv")
    dud = set(zip(d.idducto_logico, d.anio))
    assert not any((i, y) in dud for i, y in zip(r.idducto_logico, r.anio))
    assert not any("utilizacion" in c.lower() for c in d.columns)
    assert not r.denominacion_ducto.str.contains("VMOC").any()
    assert not d.motivo_capacidad_dudosa.isna().any()


def test_clasificacion_de_ductos_que_mueven_petroleo(raw):
    t = H.p20_raw()
    pet = set(t[(t.volumen > 0) & (t.tipo_producto == "Petroleo")].idducto.map(lambda i: ALIAS.get(i, i)))
    cl = H.web("clasificacion_ductos_petroleo.csv")
    assert len(cl) == len(pet) == 83 and set(cl.idducto_logico) == pet
    assert cl.categoria.value_counts().to_dict() == {"EN_RANKING": 44, "SIN_CAPACIDAD_EN_ANEXO_2A": 34, "CAPACIDAD_DUDOSA_TODOS_LOS_ANIOS": 5}
    vmoc = cl[cl.denominacion_ducto.str.contains("VMOC")].iloc[0]
    assert vmoc.categoria == "CAPACIDAD_DUDOSA_TODOS_LOS_ANIOS" and vmoc.anios_con_capacidad_dudosa == "2025"
    d = H.web("ductos_capacidad_dudosa.csv")
    assert d[d.idducto_logico == 539].motivo_capacidad_dudosa.tolist() == ["D2"]
    r = json.loads((H.WEB / "resumen_ductos.json").read_text(encoding="utf-8"))
    assert r["ductos_logicos_que_mueven_petroleo"] == 83 and r["ranking_n_ductos"] == 44 and r["ranking_sobre_100"] == 3


def test_ningun_archivo_nuevo_publica_171_de_vmoc():
    for f in ("utilizacion_ductos_ranking.csv", "ductos_capacidad_dudosa.csv", "clasificacion_ductos_petroleo.csv", "resumen_ductos.json"):
        txt = (H.WEB / f).read_text(encoding="utf-8")
        assert "171.1" not in txt and "171,1" not in txt, f


def test_alias_de_ductos_conserva_los_ids_originales(clean_ok):
    t = H.clean("fact_transporte_ductos.csv")
    assert set(t.idducto) >= {255, 532, 122, 533}
    m = t.drop_duplicates("idducto").set_index("idducto").idducto_logico
    assert m[532] == 255 and m[533] == 122 and m[255] == 255
    sol = t[t.idducto.isin([255, 532])].groupby("idducto").fecha.agg(["min", "max"])
    assert sol.loc[255, "max"] < sol.loc[532, "min"]            # periodos contiguos y sin solape (base de la inferencia)
    p = H.clean("fact_movimientos_exportacion_ductos.csv")
    assert "NO IDENTIFICADO" in set(p.pais_original.dropna()) and (p.pais_estado == "no_identificado").sum() == 168
