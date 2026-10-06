"""
Series de la Cuenca Neuquina: produccion total de la cuenca, exportacion por terminal, comparacion y KPIs.
(Decisiones D1 y D3 de la correccion; hallazgos F1, F6, F7, F8 de la auditoria.)

Entradas:
  RAW   produccion por pozo (4 archivos anuales + archivo no convencional), planilla 21 (via CLEAN), Anexo/planilla 20 (via CLEAN)
  CLEAN fact_produccion_pozo_mes_vaca_muerta.csv, fact_movimientos_exportacion_ductos.csv, fact_transporte_ductos.csv
Salidas:
  CLEAN produccion_cuenca_neuquina_mensual.csv
  WEB   exportacion_cuenca_neuquina_mensual.csv       exportacion de crudo por terminal (Oiltanking + Refineria Bahia Blanca), bbl/dia,
                                                      con meses "sin dato" (NO son ceros) y, aparte, el oleoducto a Chile (planilla 20)
        comparacion_produccion_exportacion.csv        mensual, cierra en dic-2025 (D3): produccion VM, produccion de la cuenca,
                                                      exportacion, % exportado, medias moviles de 12 meses e indice (base elegida)
        comparacion_anual.csv                         promedios anuales y razones; indices para las bases de sensibilidad
        indices_sensibilidad.csv                      indices en formato largo (bases base-1, base, base+1)
        exportacion_nacional_por_terminal_anual.csv   planilla 21 completa por operador de terminal, con el volumen NO IDENTIFICADO
        exportacion_nacional_por_pais_anual.csv       idem por pais (incluye NO IDENTIFICADO)
        concentracion_exportacion_2020_2025.csv       por operador de terminal y por cargador
        kpis_resumen.json                             cifras de las tarjetas, con alcance y fecha

Alcances que deben leerse junto con cada serie (F1/F6):
  * Exportacion "Cuenca Neuquina (proxy por terminal)": volumen que sale por las terminales de Oiltanking (Puerto Rosales) y de la
    Refineria Bahia Blanca (Posta 3). Es un PROXY: el crudo "Neuquen/Medanito" incluye convencional de la cuenca, y la planilla 21 solo cubre
    terminales maritimas (titulo oficial: "Volumenes operados por Terminales Maritimas - Planilla 21"). Las exportaciones por ducto estan en
    la planilla 20 (p. ej. "Puesto Hernandez - Buta Mallin", Oleoducto Trasandino, a Chile) y NO se suman a la serie principal.
  * Produccion de Vaca Muerta: formacion "vaca muerta" (cuenca Neuquina; Neuquen, Mendoza y Rio Negro). 2006-2021: solo no convencional.
  * Produccion total de la cuenca: cuenca == NEUQUINA, todas las provincias, convencional + no convencional. Solo se puede construir
    para 2022-2025 (los archivos anuales previos a 2022 no estan en raw/).
"""
import json
import os
import unicodedata

import numpy as np
import pandas as pd

from _rutas import CLEAN, RAW, WEB

BBL_POR_M3 = 6.2898
OPERADORES_NEUQUINOS = ["Oiltanking EBYTEM S.A.", "Refineria Bahia Blanca SAU"]
UMBRAL_EXPORTACION_MATERIAL = 0.10     # exportacion / produccion de VM (promedio anual) para elegir el anio base
CORTE_COMPARACIONES = pd.Timestamp("2025-12-01")   # D3
ORIGEN_POR_TERMINAL = {
    "oiltanking": "Cuenca Neuquina (proxy por terminal: Puerto Rosales)",
    "refineria bahia blanca": "Cuenca Neuquina (proxy por terminal: Posta 3, Refineria Bahia Blanca)",
    "termap": "Golfo San Jorge (proxy: crudo Escalante / Canadon Seco)",
    "total austral": "Austral (proxy: crudo Hidra / San Sebastian)",
    "compania general de combustibles": "Sin clasificar (producto 'Crudo MI', Punta Loyola)",
    "ypf": "Sin clasificar (terminal Cruz del Sur)",
}


def norm(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()


def origen(empresa):
    n = norm(empresa)
    for k, v in ORIGEN_POR_TERMINAL.items():
        if n.startswith(k):
            return v
    return "Sin clasificar"


def grupo_cargador(c):
    """Agrupa variantes de razon social del mismo cargador (documentado en el diccionario)."""
    n = norm(c)
    if "vista" in n:
        return "VISTA (Vista Energy / Vista Oil & Gas, 4 variantes)"
    if "pan american" in n:
        return "PAN AMERICAN ENERGY (3 variantes)"
    return str(c)


# ---------------------------------------------------------------------------------------------------------------
# 1. Produccion
# ---------------------------------------------------------------------------------------------------------------
print("1. Produccion...")
pozo = pd.read_csv(os.path.join(CLEAN, "fact_produccion_pozo_mes_vaca_muerta.csv"), encoding="utf-8-sig", low_memory=False,
                   usecols=["fecha", "prod_pet_m3", "tipo_de_recurso"])
pozo["fecha"] = pd.to_datetime(pozo["fecha"])
prod_vm = pozo.groupby("fecha")["prod_pet_m3"].sum().rename("prod_vm_m3")


def leer_prod(archivo):
    p = os.path.join(RAW, archivo)
    hdr = pd.read_csv(p, encoding="utf-8-sig", nrows=0).columns
    cols = [c for c in ["idempresa", "anio", "mes", "idpozo", "prod_pet", "formacion", "cuenca", "provincia", "tipo_de_recurso"] if c in hdr]
    d = pd.read_csv(p, encoding="utf-8-sig", usecols=cols, low_memory=False)
    d["cuenca_n"] = d["cuenca"].fillna("").map(norm)
    d["es_vm"] = d["formacion"].fillna("").map(norm).str.contains("vaca muerta")
    d["fecha"] = pd.to_datetime(dict(year=d.anio, month=d.mes, day=1))
    return d


anuales = pd.concat([leer_prod(f"produccin-de-pozos-de-gas-y-petrleo-{y}.csv") for y in (2022, 2023, 2024, 2025)], ignore_index=True)
cuenca = anuales[anuales["cuenca_n"] == "neuquina"].drop_duplicates(["idempresa", "idpozo", "anio", "mes"])
prod_cuenca_total = cuenca.groupby("fecha")["prod_pet"].sum().rename("prod_cuenca_total_m3")
prod_cuenca_conv = cuenca[cuenca["tipo_de_recurso"] == "CONVENCIONAL"].groupby("fecha")["prod_pet"].sum().rename("prod_cuenca_conv_m3")
del anuales

nc = leer_prod("produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv")
nc_cuenca = nc[nc["cuenca_n"] == "neuquina"].drop_duplicates(["idempresa", "idpozo", "anio", "mes"])
prod_cuenca_nc = nc_cuenca.groupby("fecha")["prod_pet"].sum().rename("prod_cuenca_nc_m3")
prod_vm_nc = nc_cuenca[nc_cuenca["es_vm"]].groupby("fecha")["prod_pet"].sum().rename("prod_vm_nc_m3")

fechas = pd.date_range("2006-01-01", "2026-06-01", freq="MS")
pm = pd.DataFrame(index=fechas)
for s in (prod_vm, prod_vm_nc, prod_cuenca_total, prod_cuenca_conv, prod_cuenca_nc):
    pm = pm.join(s)
pm["anio"], pm["mes"], pm["dias_mes"] = pm.index.year, pm.index.month, pm.index.days_in_month
pm.index.name = "fecha"
pm.reset_index().to_csv(os.path.join(CLEAN, "produccion_cuenca_neuquina_mensual.csv"), index=False, encoding="utf-8-sig")


def bbl_dia(m3, dias):
    return m3 * BBL_POR_M3 / dias


pm["prod_vm_bbl_dia"] = bbl_dia(pm["prod_vm_m3"], pm["dias_mes"])
pm["prod_cuenca_bbl_dia"] = bbl_dia(pm["prod_cuenca_total_m3"], pm["dias_mes"])
pm["prod_vm_nc_bbl_dia"] = bbl_dia(pm["prod_vm_nc_m3"], pm["dias_mes"])

# ---------------------------------------------------------------------------------------------------------------
# 2. Exportacion por terminal (planilla 21) y oleoducto a Chile (planilla 20)
# ---------------------------------------------------------------------------------------------------------------
print("2. Exportacion...")
mov = pd.read_csv(os.path.join(CLEAN, "fact_movimientos_exportacion_ductos.csv"), encoding="utf-8-sig", low_memory=False)
mov["fecha"] = pd.to_datetime(mov["fecha"])
# El archivo de origen trae "COMPA��A" (caracteres de reemplazo ya grabados en la fuente): se restituye el nombre solo para publicar.
for _c in ("empresa", "cargador"):
    mov[_c] = mov[_c].map(lambda v: v.replace("COMPA��A", "COMPAÑÍA") if isinstance(v, str) else v)
exp = mov[mov["tipo_operacion"] == "Exportacion"].copy()
neu = mov[mov["empresa"].isin(OPERADORES_NEUQUINOS)]
neu_exp = exp[exp["empresa"].isin(OPERADORES_NEUQUINOS)].groupby("fecha")["volumen"].sum()
neu_reporto = neu.groupby("fecha").size()
inicio = neu["fecha"].min()
fx = pd.date_range(inicio, "2026-06-01", freq="MS")
ex = pd.DataFrame(index=fx)
ex["operadores_con_filas"] = neu.groupby("fecha")["empresa"].nunique().reindex(fx).fillna(0).astype(int)
ex["exportacion_m3"] = neu_exp.reindex(fx)
ex["estado"] = np.where(ex["exportacion_m3"].fillna(0) > 0, "con_exportacion",
                        np.where(neu_reporto.reindex(fx).notna(), "sin_exportacion_reportada", "sin_dato"))
ex.loc[ex["estado"] == "sin_exportacion_reportada", "exportacion_m3"] = 0.0
ex.loc[ex["estado"] == "sin_dato", "exportacion_m3"] = np.nan
ex["dias_mes"] = ex.index.days_in_month
ex["exportacion_terminales_bbl_dia"] = bbl_dia(ex["exportacion_m3"], ex["dias_mes"])

tr = pd.read_csv(os.path.join(CLEAN, "fact_transporte_ductos.csv"), encoding="utf-8-sig", low_memory=False,
                 usecols=["idducto", "fecha", "volumen", "tipo_operacion", "tipo_producto", "denominacion_ducto"])
tr["fecha"] = pd.to_datetime(tr["fecha"])
otasa = tr[(tr["idducto"] == 379) & (tr["tipo_operacion"] == "Exportacion") & (tr["tipo_producto"] == "Petroleo")]
otasa_m = otasa.groupby("fecha")["volumen"].sum()
ex["exportacion_oleoducto_chile_m3"] = otasa_m.reindex(fx)
ex["exportacion_oleoducto_chile_bbl_dia"] = bbl_dia(ex["exportacion_oleoducto_chile_m3"], ex["dias_mes"])
ex.index.name = "fecha"
out = ex.reset_index()[["fecha", "estado", "operadores_con_filas", "exportacion_m3", "exportacion_terminales_bbl_dia",
                        "exportacion_oleoducto_chile_m3", "exportacion_oleoducto_chile_bbl_dia"]].round(3)
out.to_csv(os.path.join(WEB, "exportacion_cuenca_neuquina_mensual.csv"), index=False)

# ---------------------------------------------------------------------------------------------------------------
# 3. Comparacion mensual (cierra en dic-2025) y anual
# ---------------------------------------------------------------------------------------------------------------
print("3. Comparacion...")
cmp_ = ex.join(pm[["dias_mes", "prod_vm_bbl_dia", "prod_cuenca_bbl_dia"]].rename(columns={"dias_mes": "_d"}), how="left")
cmp_ = cmp_[cmp_.index <= CORTE_COMPARACIONES].copy()
cmp_["pct_exportado_cuenca"] = 100 * cmp_["exportacion_terminales_bbl_dia"] / cmp_["prod_cuenca_bbl_dia"]
cmp_["pct_exportado_vm"] = 100 * cmp_["exportacion_terminales_bbl_dia"] / cmp_["prod_vm_bbl_dia"]
cmp_["pct_exportado_cuenca_con_oleoducto"] = 100 * (cmp_["exportacion_terminales_bbl_dia"] + cmp_["exportacion_oleoducto_chile_bbl_dia"]) / cmp_["prod_cuenca_bbl_dia"]
for col in ("prod_vm_bbl_dia", "prod_cuenca_bbl_dia", "exportacion_terminales_bbl_dia"):
    cmp_[col.replace("_bbl_dia", "_ma12_bbl_dia")] = cmp_[col].rolling(12, min_periods=12).mean()
cmp_["pct_exportado_cuenca_ma12"] = 100 * cmp_["exportacion_terminales_ma12_bbl_dia"] / cmp_["prod_cuenca_ma12_bbl_dia"]
cmp_["pct_exportado_vm_ma12"] = 100 * cmp_["exportacion_terminales_ma12_bbl_dia"] / cmp_["prod_vm_ma12_bbl_dia"]

an = pd.DataFrame(index=range(2019, 2026))
for y in an.index:
    e = ex[ex.index.year == y]
    con = e[e["estado"] != "sin_dato"]
    an.loc[y, "meses_exportacion_con_dato"] = len(con)
    an.loc[y, "meses_con_exportacion"] = int((e["estado"] == "con_exportacion").sum())
    an.loc[y, "meses_sin_exportacion_reportada"] = int((e["estado"] == "sin_exportacion_reportada").sum())
    an.loc[y, "exportacion_terminales_bbl_dia"] = (con["exportacion_m3"].sum() * BBL_POR_M3 / con["dias_mes"].sum()) if len(con) else np.nan
    p = pm[pm.index.year == y]
    an.loc[y, "prod_vm_bbl_dia"] = p["prod_vm_m3"].sum() * BBL_POR_M3 / p["dias_mes"].sum()
    an.loc[y, "prod_cuenca_bbl_dia"] = (p["prod_cuenca_total_m3"].sum() * BBL_POR_M3 / p["dias_mes"].sum()) if p["prod_cuenca_total_m3"].notna().all() else np.nan
    o = e[e["exportacion_oleoducto_chile_m3"].notna()]
    an.loc[y, "meses_oleoducto_chile_con_dato"] = len(o)
    an.loc[y, "exportacion_oleoducto_chile_bbl_dia"] = (o["exportacion_oleoducto_chile_m3"].sum() * BBL_POR_M3 / o["dias_mes"].sum()) if len(o) else np.nan
an["pct_exportado_vm"] = 100 * an["exportacion_terminales_bbl_dia"] / an["prod_vm_bbl_dia"]
an["pct_exportado_cuenca"] = 100 * an["exportacion_terminales_bbl_dia"] / an["prod_cuenca_bbl_dia"]
an["prod_cuenca_menos_vm_bbl_dia"] = an["prod_cuenca_bbl_dia"] - an["prod_vm_bbl_dia"]
an["vm_sobre_cuenca_pct"] = 100 * an["prod_vm_bbl_dia"] / an["prod_cuenca_bbl_dia"]
an["anio_parcial_exportacion"] = an["meses_exportacion_con_dato"] < 12

# criterio del anio base: primer anio con 12/12 meses de exportacion neuquina y exportacion >= 10% de la produccion de VM
# ("con exportacion" = el operador reporto exportaciones ese mes; un mes en que reporto operaciones pero ninguna exportacion cuenta como 0)
cumple = an[(an["meses_con_exportacion"] == 12) & (an["pct_exportado_vm"] >= 100 * UMBRAL_EXPORTACION_MATERIAL)]
ANIO_BASE = int(cumple.index.min())
BASES = [ANIO_BASE - 1, ANIO_BASE, ANIO_BASE + 1]
largo = []
for b in BASES:
    for serie, col in (("exportacion_terminales", "exportacion_terminales_bbl_dia"), ("produccion_vm", "prod_vm_bbl_dia"),
                       ("produccion_cuenca", "prod_cuenca_bbl_dia")):
        base = an.loc[b, col]
        an[f"idx_{serie}_base{b}"] = 100 * an[col] / base if pd.notna(base) else np.nan
        for y in an.index:
            largo.append(dict(base=b, anio=y, serie=serie, indice=an.loc[y, f"idx_{serie}_base{b}"], meses_base=an.loc[b, "meses_exportacion_con_dato"] if serie == "exportacion_terminales" else 12))
pd.DataFrame(largo).round(2).to_csv(os.path.join(WEB, "indices_sensibilidad.csv"), index=False)
an.index.name = "anio"
an.reset_index().round(3).to_csv(os.path.join(WEB, "comparacion_anual.csv"), index=False)

for serie, col in (("exportacion_terminales", "exportacion_terminales_ma12_bbl_dia"), ("produccion_vm", "prod_vm_ma12_bbl_dia"),
                   ("produccion_cuenca", "prod_cuenca_ma12_bbl_dia")):
    sub = cmp_[cmp_.index.year == ANIO_BASE]
    base_ref = an.loc[ANIO_BASE, {"exportacion_terminales": "exportacion_terminales_bbl_dia", "produccion_vm": "prod_vm_bbl_dia", "produccion_cuenca": "prod_cuenca_bbl_dia"}[serie]]
    cmp_[f"idx_{serie}_ma12_base{ANIO_BASE}"] = 100 * cmp_[col] / base_ref
cmp_.index.name = "fecha"
cols_cmp = ["estado", "prod_vm_bbl_dia", "prod_cuenca_bbl_dia", "exportacion_terminales_bbl_dia", "pct_exportado_cuenca", "pct_exportado_vm",
            "exportacion_oleoducto_chile_bbl_dia", "pct_exportado_cuenca_con_oleoducto",
            "prod_vm_ma12_bbl_dia", "prod_cuenca_ma12_bbl_dia", "exportacion_terminales_ma12_bbl_dia", "pct_exportado_cuenca_ma12", "pct_exportado_vm_ma12",
            f"idx_produccion_vm_ma12_base{ANIO_BASE}", f"idx_produccion_cuenca_ma12_base{ANIO_BASE}", f"idx_exportacion_terminales_ma12_base{ANIO_BASE}"]
cmp_.reset_index()[["fecha"] + cols_cmp].round(3).to_csv(os.path.join(WEB, "comparacion_produccion_exportacion.csv"), index=False)

# ---------------------------------------------------------------------------------------------------------------
# 4. Serie nacional por terminal (contexto) y concentracion
# ---------------------------------------------------------------------------------------------------------------
print("4. Serie nacional...")
exp["origen_crudo_proxy"] = exp["empresa"].map(origen)
exp["sin_pais"] = exp["pais_estado"].isin(["no_identificado", "no_aplica", "sin_dato"])
g = exp.groupby(["anio", "empresa", "origen_crudo_proxy"]).apply(lambda d: pd.Series({
    "volumen_total_m3": d["volumen"].sum(),
    "volumen_con_pais_m3": d.loc[~d["sin_pais"], "volumen"].sum(),
    "volumen_no_identificado_m3": d.loc[d["pais_estado"] == "no_identificado", "volumen"].sum()}), include_groups=False).reset_index()
tot = g.groupby("anio")[["volumen_total_m3", "volumen_con_pais_m3", "volumen_no_identificado_m3"]].sum().reset_index()
tot["empresa"], tot["origen_crudo_proxy"] = "TOTAL", "Todas las terminales (planilla 21)"
g = pd.concat([g, tot], ignore_index=True)
g["pct_no_identificado"] = 100 * g["volumen_no_identificado_m3"] / g["volumen_total_m3"]
g.rename(columns={"empresa": "operador_terminal"}).round(2).to_csv(os.path.join(WEB, "exportacion_nacional_por_terminal_anual.csv"), index=False)

pp = exp.assign(pais_pub=exp["pais_original"].where(exp["pais_estado"].isin(["identificado", "no_identificado"]), "SIN DATO / NO APLICA")).groupby(["anio", "pais_pub"])["volumen"].sum().reset_index()
pp.columns = ["anio", "pais", "volumen_m3"]
pp[pp["volumen_m3"] > 0].round(1).to_csv(os.path.join(WEB, "exportacion_nacional_por_pais_anual.csv"), index=False)

per = exp[exp["anio"].between(2020, 2025)]
conc = []
for nivel, serie in (("operador_terminal", per["empresa"]), ("cargador", per["cargador"].map(grupo_cargador))):
    v = per.groupby(serie)["volumen"].sum().sort_values(ascending=False)
    for r, (n, vol) in enumerate(v.items(), 1):
        conc.append(dict(nivel=nivel, posicion=r, nombre=n, volumen_m3=round(vol, 1), pct=round(100 * vol / v.sum(), 2)))
conc = pd.DataFrame(conc)
conc.to_csv(os.path.join(WEB, "concentracion_exportacion_2020_2025.csv"), index=False)

# ---------------------------------------------------------------------------------------------------------------
# 5. KPIs
# ---------------------------------------------------------------------------------------------------------------
print("5. KPIs...")
j26, j25 = pm.loc["2026-06-01"], pm.loc["2025-06-01"]
d25, d24 = pm.loc["2025-12-01"], pm.loc["2024-12-01"]
vm_total_m3 = pozo["prod_pet_m3"].sum()
nc_total_m3 = pozo.loc[pozo["tipo_de_recurso"] == "NO CONVENCIONAL", "prod_pet_m3"].sum()
p22 = pozo[pozo["fecha"].dt.year >= 2022]
vol_mensual_exp = ex.loc["2022-01-01":"2025-12-01", "exportacion_terminales_bbl_dia"]
vol_mensual_vm = pm.loc["2022-01-01":"2025-12-01", "prod_vm_bbl_dia"]
nacional = mov[(mov["tipo_operacion"] == "Exportacion")]
nac_mensual = nacional.groupby("fecha")["volumen"].sum().reindex(pd.date_range("2020-01-01", "2025-12-01", freq="MS"))
vm20 = pm.loc["2020-01-01":"2025-12-01", "prod_vm_bbl_dia"]
def top3_pct(nivel):
    """Top 3 calculado desde los volumenes (no sumando porcentajes ya redondeados)."""
    v = conc.loc[conc.nivel == nivel, "volumen_m3"]
    return 100 * v.head(3).sum() / v.sum()


op_top3 = top3_pct("operador_terminal")
carg_top3 = top3_pct("cargador")
ult = ex.loc["2026-06-01"]
kpis = {
    "corte_comparaciones": "2025-12-01",
    "fecha_ultimo_mes_produccion": "2026-06-01",
    "produccion_ultimo_mes_bbl_dia": round(float(j26["prod_vm_nc_bbl_dia"]), 1),
    "produccion_alcance": "Solo no convencional (archivo no convencional; el convencional de 2026 no esta en las fuentes cargadas, "
                          "y en 2022-2025 fue 0,08%-0,20% del volumen anual de Vaca Muerta)",
    "variacion_interanual_produccion_pct": round(100 * (float(j26["prod_vm_nc_bbl_dia"]) / float(j25["prod_vm_nc_bbl_dia"]) - 1), 1),
    "variacion_interanual_base": "jun-2026 vs jun-2025, ambos solo no convencional",
    "produccion_vm_dic_2025_bbl_dia": round(float(d25["prod_vm_bbl_dia"]), 1),
    "variacion_interanual_vm_dic_2025_pct": round(100 * (float(d25["prod_vm_bbl_dia"]) / float(d24["prod_vm_bbl_dia"]) - 1), 2),
    "produccion_cuenca_2025_bbl_dia": round(float(an.loc[2025, "prod_cuenca_bbl_dia"]), 1),
    "vm_sobre_cuenca_2025_pct": round(float(an.loc[2025, "vm_sobre_cuenca_pct"]), 1),
    "pct_no_convencional_2006_2025": round(100 * nc_total_m3 / vm_total_m3, 2),
    "pct_no_convencional_2022_2025": round(100 * p22.loc[p22["tipo_de_recurso"] == "NO CONVENCIONAL", "prod_pet_m3"].sum() / p22["prod_pet_m3"].sum(), 2),
    "pct_no_convencional_nota": "2006-2021 solo incluye no convencional (los archivos anuales previos a 2022 no estan cargados)",
    "fecha_ultimo_mes_exportacion": "2026-06-01",
    "exportacion_terminales_neuquinos_ultimo_mes_bbl_dia": round(float(ult["exportacion_terminales_bbl_dia"]), 1),
    "exportacion_terminales_neuquinos_ultimo_mes_m3": round(float(ult["exportacion_m3"]), 1),
    "exportacion_nacional_terminales_ultimo_mes_m3": round(float(nacional.loc[nacional["fecha"] == "2026-06-01", "volumen"].sum()), 1),
    "exportacion_nacional_terminales_total_2018_2026_m3": round(float(nacional["volumen"].sum()), 1),
    "volumen_no_identificado_m3": round(float(nacional.loc[nacional["pais_estado"] == "no_identificado", "volumen"].sum()), 1),
    "pct_no_identificado": round(100 * float(nacional.loc[nacional["pais_estado"] == "no_identificado", "volumen"].sum() / nacional["volumen"].sum()), 2),
    "pct_con_pais_identificado": round(100 * float(nacional.loc[nacional["pais_estado"] == "identificado", "volumen"].sum() / nacional["volumen"].sum()), 2),
    "pct_exportado_cuenca_por_anio": {str(y): round(float(an.loc[y, "pct_exportado_cuenca"]), 1) for y in range(2022, 2026)},
    "pct_exportado_vm_por_anio": {str(y): round(float(an.loc[y, "pct_exportado_vm"]), 1) for y in range(2019, 2026)},
    "pct_exportado_nota": "Numerador: crudo exportado por terminales neuquinos (proxy). Denominador: produccion total de la cuenca (solo 2022-2025). "
                          "No incluye el oleoducto a Chile (planilla 20).",
    "indice_anio_base": ANIO_BASE,
    "indice_criterio_base": f"primer anio calendario con exportacion neuquina en 12 de 12 meses y exportacion >= {int(UMBRAL_EXPORTACION_MATERIAL * 100)}% de la produccion de Vaca Muerta (promedio anual)",
    "indice_sensibilidad_bases": BASES,
    "indice_meses_con_exportacion_por_anio": {str(y): int(an.loc[y, "meses_con_exportacion"]) for y in an.index},
    "concentracion_top3_operadores_terminal_pct_2020_2025": round(float(op_top3), 2),
    "concentracion_top3_cargadores_pct_2020_2025": round(float(carg_top3), 2),
    "volatilidad_mensual_2022_2025_exportacion_terminales_pct": round(float(vol_mensual_exp.pct_change().dropna().std() * 100), 2),
    "volatilidad_mensual_2022_2025_produccion_vm_pct": round(float(vol_mensual_vm.pct_change().dropna().std() * 100), 2),
    "volatilidad_mensual_2020_2025_exportacion_nacional_terminales_pct": round(float(nac_mensual.pct_change().dropna().std() * 100), 2),
    "volatilidad_mensual_2020_2025_produccion_vm_pct": round(float(vm20.pct_change().dropna().std() * 100), 2),
    "oleoducto_chile_2025_bbl_dia": round(float(an.loc[2025, "exportacion_oleoducto_chile_bbl_dia"]), 1),
    "oleoducto_chile_nota": "Planilla 20, ducto 'Puesto Hernandez - Buta Mallin' (Oleoducto Trasandino Argentina S.A.), 2023-05 a 2026-06. "
                            "No se suma a la serie principal (pendiente de decision).",
}
with open(os.path.join(WEB, "kpis_resumen.json"), "w", encoding="utf-8") as f:
    json.dump(kpis, f, ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in kpis.items() if not k.endswith("nota")}, ensure_ascii=False, indent=1)[:3500])
