"""1.1 y 1.2 de la auditoría: reconciliación raw -> clean (producción), recalculada de forma independiente."""
import numpy as np
import pandas as pd
import pytest

import helpers as H

KEY = ["idempresa", "idpozo", "anio", "mes"]


def test_filas_por_etapa(vm_raw_data):
    anual = sum(len(d) for d in vm_raw_data["anual"])
    nc = vm_raw_data["nc"]
    assert anual == 117_925
    assert len(nc) == 213_064
    assert len(nc[nc.anio.between(2022, 2025)]) == 106_729       # solape con los anuales
    assert int((nc.anio == 2026).sum()) == 19_178                  # ene-jun 2026, no usado por el pipeline


def test_unica_variante_de_formacion(vm_raw_data):
    for d in vm_raw_data["anual"] + [vm_raw_data["nc"]]:
        assert set(d.formacion.dropna().unique()) == {"vaca muerta"}


def test_solape_nc_2022_2025_identico_a_anuales(vm_raw_data):
    ann = pd.concat(vm_raw_data["anual"], ignore_index=True)
    ann_nc = ann[ann.tipo_de_recurso == "NO CONVENCIONAL"]
    nc = vm_raw_data["nc"]
    nc = nc[nc.anio.between(2022, 2025)]
    m = nc.merge(ann_nc, on=KEY, how="outer", suffixes=("_nc", "_an"), indicator=True)
    assert (m._merge == "both").all(), m._merge.value_counts().to_dict()
    assert np.allclose(m.prod_pet_nc, m.prod_pet_an, atol=1e-6)


def test_no_hay_duplicados_de_clave(vm):
    assert not vm.duplicated(KEY).any()
    assert len(vm) == 205_082


def test_total_bbl_raw_igual_clean(vm, clean_ok):
    cl = H.clean("fact_produccion_pozo_mes_vaca_muerta.csv")
    assert len(cl) == len(vm)
    assert abs(vm.bbl.sum() - cl.prod_pet_bbl.sum()) < 1e-3
    assert round(vm.bbl.sum()) == 722_439_535


def test_pozo_mes_fila_a_fila(vm, clean_ok):
    cl = H.clean("fact_produccion_pozo_mes_vaca_muerta.csv")
    m = vm.merge(cl, on=KEY, how="outer", indicator=True, suffixes=("_raw", "_cl"))
    assert (m._merge == "both").all()
    for a, b in [("prod_pet", "prod_pet_m3"), ("prod_gas", "prod_gas_miles_m3"), ("prod_agua", "prod_agua_m3")]:
        assert (m[a] - m[b]).abs().max() < 1e-6, a


def test_sin_produccion_negativa(vm):
    assert (vm[["prod_pet", "prod_gas", "prod_agua"]] >= 0).all().all()


def test_yacimiento_mes_igual_agregacion_desde_raw(vm, clean_ok):
    yac = H.clean("fact_produccion_yacimiento_mes_vaca_muerta.csv")
    yac["fecha"] = pd.to_datetime(yac.fecha)
    keys = ["fecha", "areayacimiento", "provincia", "cuenca", "tipo_de_recurso", "sub_tipo_recurso"]
    v = vm.copy()
    for c in keys[1:]:
        v[c] = v[c].fillna("<NA>")
    y = yac.copy()
    for c in keys[1:]:
        y[c] = y[c].fillna("<NA>")
    g = v.groupby(keys).agg(m3=("prod_pet", "sum"), gas=("prod_gas", "sum"), agua=("prod_agua", "sum"),
                            n=("idpozo", "nunique")).reset_index()
    prod = v[v.prod_pet > 0].groupby(keys).idpozo.nunique().rename("np").reset_index()
    g = g.merge(prod, on=keys, how="left").fillna({"np": 0})
    m = g.merge(y, on=keys, how="outer", indicator=True)
    assert (m._merge == "both").all() and len(m) == 15_762
    assert (m.m3 - m.prod_pet_m3).abs().max() < 1e-6
    assert (m.gas - m.prod_gas_miles_m3).abs().max() < 1e-6
    assert (m.agua - m.prod_agua_m3).abs().max() < 1e-6
    assert (m.n == m.pozos_reportados).all() and (m.np == m.pozos_productivos).all()


def test_dias_mes_es_calendario(clean_ok):
    for f in ["fact_produccion_pozo_mes_vaca_muerta.csv", "fact_produccion_yacimiento_mes_vaca_muerta.csv",
              "fact_capacidad_ductos.csv"]:
        d = H.clean(f)
        assert (d.dias_mes.values == pd.to_datetime(d.fecha).dt.days_in_month.values).all(), f


def test_el_nc_trae_2026_no_usado(vm_raw_data, clean_ok):
    """Hecho de los datos (F6): el NC trae ene-jun 2026 y clean termina en dic-2025."""
    nc = vm_raw_data["nc"]
    assert nc[nc.anio == 2026].mes.max() == 6
    cl = H.clean("fact_produccion_pozo_mes_vaca_muerta.csv")
    assert pd.to_datetime(cl.fecha).max() == pd.Timestamp("2025-12-01")
