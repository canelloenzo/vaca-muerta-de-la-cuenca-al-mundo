"""
Serie principal de exportacion de crudo de la cuenca Neuquina: comercio exterior declarado por las empresas (decision B).

Fuentes (en RAW):
  TD_comercioexterior_actualizado_2026-09-24.xlsx   "Comercio exterior" de Refinacion y Comercializacion (Secretaria de Energia): 798.045 registros
                                                    2020-ago 2026 por empresa, producto, pais, cantidad y monto. La tabla dinamica visible muestra un solo mes, pero
                                                    los datos completos estan en la cache de la tabla dinamica (xl/pivotCache): se leen de ahi.
  serie-historica-produccion-petroleo-por-cuenca-subtipo-capitulo-iv.csv   produccion oficial mensual por cuenca, 2006-ago 2026 (m3)
Entradas de CLEAN:  produccion_cuenca_neuquina_mensual.csv (script 11; Vaca Muerta por pozo), fact_movimientos_exportacion_ductos.csv (planilla 21)
Salidas:
  CLEAN fact_exportacion_crudo_comex.csv           registros de exportacion de crudo (productos por cuenca de origen)
  WEB   comex_exportacion_cuenca_neuquina_mensual.csv   mensual: m3, bbl/dia, USD, USD/bbl, Chile, produccion oficial de la cuenca, % exportado, media movil 12m
        comex_anual.csv                                  anual: lo anterior + indices base 2021/2022/2023 + contraste con terminales (planilla 21)
        comex_neuquina_por_pais_anual.csv                crudo neuquino por pais de destino, con volumen "no aplica" aparte
        comex_neuquina_concentracion_2020_2025.csv       por empresa exportadora (quien declara)
        comex_validacion_precios.csv                     precio implicito vs precio FOB Medanito de la tabla oficial (2020-2021)

Alcances:
  * "Exportacion de crudo de la cuenca Neuquina" = productos "Cuenca Neuquina - ..." (Neuquen, Rio Negro, La Pampa y Mendoza). Incluye crudo convencional y
    no convencional de la cuenca y todas las vias (terminales maritimas y oleoducto a Chile). Es el origen declarado por la empresa.
  * "monto" = USD FOB declarado. Validado contra la tabla oficial de precios FOB (script, comex_validacion_precios.csv).
  * La produccion de la cuenca es la serie oficial (convencional + no convencional, todas las provincias).
"""
import json
import os
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from _rutas import CLEAN, RAW, WEB

BBL_POR_M3 = 6.2898
UMBRAL_EXPORTACION_MATERIAL = 0.10
CORTE = pd.Timestamp("2025-12-01")
XLSX = os.path.join(RAW, "TD_comercioexterior_actualizado_2026-09-24.xlsx")
SERIE = os.path.join(RAW, "serie-historica-produccion-petroleo-por-cuenca-subtipo-capitulo-iv.csv")
PRECIOS = os.path.join(RAW, "precio-exportacion-crudo.xlsx")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def leer_cache(path):
    x = zipfile.ZipFile(path)
    d = ET.fromstring(x.read("xl/pivotCache/pivotCacheDefinition1.xml"))
    campos = []
    for cf in d.find(NS + "cacheFields"):
        si = cf.find(NS + "sharedItems")
        items = [e.get("v") for e in si] if si is not None and len(si) else None
        campos.append((cf.get("name"), items))
    filas = []
    with x.open("xl/pivotCache/pivotCacheRecords1.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "r":
                r = []
                for k, c in enumerate(el):
                    v = c.get("v")
                    if c.tag == NS + "x":
                        r.append(campos[k][1][int(v)] if campos[k][1] else v)
                    elif c.tag == NS + "m":
                        r.append(None)
                    else:
                        r.append(v)
                filas.append(r)
                el.clear()
    df = pd.DataFrame(filas, columns=[n for n, _ in campos])
    for c in ("anio", "mes", "cantidad", "monto"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


print("1. Comercio exterior (cache de la tabla dinamica)...")
df = leer_cache(XLSX)
ex = df[(df["tipodecomercializacion"] == "Exportación") & df["producto"].str.startswith("Cuenca", na=False)].copy()
ex["fecha"] = pd.to_datetime(dict(year=ex["anio"], month=ex["mes"], day=1))
ex["cuenca"] = ex["producto"].str.extract(r"^(Cuenca [A-Za-zñÑ ]+?)(?: - |$)")[0].str.strip()
assert (ex["unidad"] == "(m3)").all(), "unidades distintas de m3"
n_dup = int(ex.duplicated(["fecha", "empresa", "producto", "pais", "provincia", "subtipodecomercializacion", "cantidad", "monto"]).sum())
print(f"   registros de exportacion de crudo por cuenca: {len(ex)} | filas repetidas exactas (se informan, no se eliminan): {n_dup}")
ex.drop(columns=["tipodecomercializacion", "unidad"]).to_csv(os.path.join(CLEAN, "fact_exportacion_crudo_comex.csv"), index=False, encoding="utf-8-sig")
ULTIMO_MES = ex["fecha"].max()

neu = ex[ex["cuenca"] == "Cuenca Neuquina"].copy()
neu["chile"] = neu["pais"].str.upper().eq("CHILE")

fx = pd.date_range("2020-01-01", ULTIMO_MES, freq="MS")
m = pd.DataFrame(index=fx)
m.index.name = "fecha"
g = neu.groupby("fecha").agg(m3=("cantidad", "sum"), usd=("monto", "sum"))
m["exportacion_m3"] = g["m3"].reindex(fx).fillna(0.0)
m["exportacion_usd"] = g["usd"].reindex(fx).fillna(0.0)
m["exportacion_chile_m3"] = neu[neu["chile"]].groupby("fecha")["cantidad"].sum().reindex(fx).fillna(0.0)
m["estado"] = np.where(m["exportacion_m3"] > 0, "con_exportacion", "sin_exportacion_declarada")
m["dias_mes"] = m.index.days_in_month
m["exportacion_bbl_dia"] = m["exportacion_m3"] * BBL_POR_M3 / m["dias_mes"]
m["usd_por_bbl"] = np.where(m["exportacion_m3"] > 0, m["exportacion_usd"] / (m["exportacion_m3"] * BBL_POR_M3), np.nan)

print("2. Produccion oficial de la cuenca...")
o = pd.read_csv(SERIE, encoding="utf-8-sig")
o["fecha"] = pd.to_datetime(o["indice_tiempo"] + "-01")
o = o.set_index("fecha")
o.to_csv(os.path.join(CLEAN, "produccion_cuenca_oficial_mensual.csv"), encoding="utf-8-sig")
pm = pd.read_csv(os.path.join(CLEAN, "produccion_cuenca_neuquina_mensual.csv"), encoding="utf-8-sig", parse_dates=["fecha"]).set_index("fecha")
m["prod_cuenca_oficial_m3"] = o["cuenca_neuquina"].reindex(fx)
m["prod_cuenca_bbl_dia"] = m["prod_cuenca_oficial_m3"] * BBL_POR_M3 / m["dias_mes"]
m["prod_vm_m3"] = pm["prod_vm_m3"].reindex(fx)
m["prod_vm_bbl_dia"] = m["prod_vm_m3"] * BBL_POR_M3 / m["dias_mes"]
# control: Vaca Muerta por pozo vs la columna "shale" oficial (informativo; septiembre de 2024 es el unico mes con diferencia relevante en 2022-2025)
cmp_vm = (pm["prod_vm_m3"] / o["shale"]).loc["2022-01-01":"2025-12-01"]
sep24 = float(o.loc["2024-09-01", "shale"] / pm.loc["2024-09-01", "prod_vm_m3"] - 1)
dif_cuenca = (o["cuenca_neuquina"] - pm["prod_cuenca_total_m3"]).loc["2022-01-01":"2025-12-01"]

mc = m[m.index <= CORTE].copy()
mc["pct_exportado_cuenca"] = 100 * mc["exportacion_bbl_dia"] / mc["prod_cuenca_bbl_dia"]
for col in ("exportacion_bbl_dia", "prod_vm_bbl_dia", "prod_cuenca_bbl_dia"):
    mc[col.replace("_bbl_dia", "_ma12_bbl_dia")] = mc[col].rolling(12, min_periods=12).mean()

print("3. Anual e indices...")
an = pd.DataFrame(index=range(2020, 2027))
an.index.name = "anio"
for y in an.index:
    e = m[m.index.year == y]
    an.loc[y, "meses_con_exportacion"] = int((e["estado"] == "con_exportacion").sum())
    an.loc[y, "meses_del_anio_con_dato"] = len(e)
    an.loc[y, "exportacion_m3"] = e["exportacion_m3"].sum()
    an.loc[y, "exportacion_usd"] = e["exportacion_usd"].sum()
    an.loc[y, "exportacion_chile_m3"] = e["exportacion_chile_m3"].sum()
    an.loc[y, "exportacion_bbl_dia"] = e["exportacion_m3"].sum() * BBL_POR_M3 / e["dias_mes"].sum()
    an.loc[y, "usd_por_bbl"] = e["exportacion_usd"].sum() / (e["exportacion_m3"].sum() * BBL_POR_M3) if e["exportacion_m3"].sum() else np.nan
    an.loc[y, "prod_cuenca_bbl_dia"] = e["prod_cuenca_oficial_m3"].sum() * BBL_POR_M3 / e["dias_mes"].sum()
    an.loc[y, "prod_vm_bbl_dia"] = e["prod_vm_m3"].sum() * BBL_POR_M3 / e["dias_mes"].sum() if e["prod_vm_m3"].notna().all() else np.nan
an["anio_parcial"] = an["meses_del_anio_con_dato"] < 12
an["pct_exportado_cuenca"] = 100 * an["exportacion_bbl_dia"] / an["prod_cuenca_bbl_dia"]
an["chile_pct_de_exportacion"] = 100 * an["exportacion_chile_m3"] / an["exportacion_m3"]

# contraste con terminales (planilla 21) y oleoducto (planilla 20) del script 11
t = pd.read_csv(os.path.join(WEB, "exportacion_cuenca_neuquina_mensual.csv"), parse_dates=["fecha"]).set_index("fecha")
tt = t.groupby(t.index.year).agg(terminales_m3=("exportacion_m3", "sum"), oleoducto_chile_planilla20_m3=("exportacion_oleoducto_chile_m3", "sum"))
an = an.join(tt, how="left")
an["razon_comex_sobre_terminales"] = an["exportacion_m3"] / an["terminales_m3"]
an["razon_comex_sobre_terminales_mas_oleoducto"] = an["exportacion_m3"] / (an["terminales_m3"] + an["oleoducto_chile_planilla20_m3"])
an["razon_chile_comex_sobre_planilla20"] = np.where(an["oleoducto_chile_planilla20_m3"] > 0, an["exportacion_chile_m3"] / an["oleoducto_chile_planilla20_m3"], np.nan)

an["alt_exportacion_m3"] = an["terminales_m3"] + an["oleoducto_chile_planilla20_m3"].fillna(0)
an["alt_exportacion_bbl_dia"] = an["alt_exportacion_m3"] * BBL_POR_M3 / [(366 if y % 4 == 0 else 365) for y in an.index]
an["alt_pct_exportado_cuenca"] = 100 * an["alt_exportacion_bbl_dia"] / an["prod_cuenca_bbl_dia"]

completos = an[(an["meses_con_exportacion"] == 12) & (an["pct_exportado_cuenca"] >= 100 * UMBRAL_EXPORTACION_MATERIAL) & (~an["anio_parcial"])]
ANIO_BASE = int(completos.index.min())
BASES = [ANIO_BASE - 1, ANIO_BASE, ANIO_BASE + 1]
for b in BASES:
    for serie, col in (("exportacion", "exportacion_bbl_dia"), ("produccion_vm", "prod_vm_bbl_dia"), ("produccion_cuenca", "prod_cuenca_bbl_dia")):
        an[f"idx_{serie}_base{b}"] = 100 * an[col] / an.loc[b, col]
for b in BASES:
    an[f"idx_exportacion_alt_base{b}"] = 100 * an["alt_exportacion_bbl_dia"] / an.loc[b, "alt_exportacion_bbl_dia"]
for serie, col in (("exportacion", "exportacion_ma12_bbl_dia"), ("produccion_vm", "prod_vm_ma12_bbl_dia"), ("produccion_cuenca", "prod_cuenca_ma12_bbl_dia")):
    base_col = {"exportacion": "exportacion_bbl_dia", "produccion_vm": "prod_vm_bbl_dia", "produccion_cuenca": "prod_cuenca_bbl_dia"}[serie]
    mc[f"idx_{serie}_ma12_base{ANIO_BASE}"] = 100 * mc[col] / an.loc[ANIO_BASE, base_col]

m.reset_index().round(3).to_csv(os.path.join(WEB, "comex_exportacion_cuenca_neuquina_mensual.csv"), index=False)
mc.reset_index()[["fecha", "estado", "exportacion_bbl_dia", "prod_vm_bbl_dia", "prod_cuenca_bbl_dia", "pct_exportado_cuenca",
                  "exportacion_ma12_bbl_dia", "prod_vm_ma12_bbl_dia", "prod_cuenca_ma12_bbl_dia",
                  f"idx_exportacion_ma12_base{ANIO_BASE}", f"idx_produccion_vm_ma12_base{ANIO_BASE}", f"idx_produccion_cuenca_ma12_base{ANIO_BASE}"]
                 ].round(3).to_csv(os.path.join(WEB, "comex_comparacion_mensual.csv"), index=False)
an.reset_index().round(4).to_csv(os.path.join(WEB, "comex_anual.csv"), index=False)

print("4. Paises, concentracion y validacion de precios...")
pais = neu.assign(pais_pub=np.where(neu["pais"].str.lower().eq("no aplica"), "SIN PAIS (no aplica)", neu["pais"].str.upper()))
pp = pais.groupby(["anio", "pais_pub"]).agg(volumen_m3=("cantidad", "sum"), monto_usd=("monto", "sum")).reset_index().rename(columns={"pais_pub": "pais"})
pp[pp["volumen_m3"] > 0].round(1).to_csv(os.path.join(WEB, "comex_neuquina_por_pais_anual.csv"), index=False)


def grupo(e):
    n = str(e).lower()
    if "vista" in n:
        return "VISTA (Vista Oil & Gas / Vista Energy, variantes de razon social)"
    if "pluspetrol" in n:
        return "PLUSPETROL (Pluspetrol / Pluspetrol Cuenca Neuquina, variantes)"
    if "pan american" in n:
        return "PAN AMERICAN ENERGY (variantes)"
    return str(e)


per = neu[neu["anio"].between(2020, 2025)]
conc = []
for nivel, serie in (("empresa_sin_agrupar", per["empresa"]), ("empresa_agrupada", per["empresa"].map(grupo))):
    v = per.groupby(serie)["cantidad"].sum().sort_values(ascending=False)
    for r, (n, vol) in enumerate(v.items(), 1):
        conc.append(dict(nivel=nivel, posicion=r, nombre=n, volumen_m3=round(vol, 1), pct=round(100 * vol / v.sum(), 2)))
pd.DataFrame(conc).to_csv(os.path.join(WEB, "comex_neuquina_concentracion_2020_2025.csv"), index=False)

p = pd.read_excel(PRECIOS, sheet_name="precios", header=None, skiprows=4).iloc[:, [0, 1, 6]]
p.columns = ["fecha", "brent", "medanito_fob_oficial"]
p["fecha"] = pd.to_datetime(p["fecha"], errors="coerce")
p = p.dropna(subset=["fecha"]).set_index("fecha")
val = m[["usd_por_bbl"]].join(p, how="inner").dropna(subset=["usd_por_bbl", "medanito_fob_oficial"])
val.reset_index().round(2).to_csv(os.path.join(WEB, "comex_validacion_precios.csv"), index=False)

brent_path = os.path.join(RAW, "eia_brent_mensual_2026-10-08.xls")
brent = pd.read_excel(brent_path, sheet_name="Data 1", header=None, skiprows=3)
brent.columns = ["fecha", "brent"]
brent["fecha"] = pd.to_datetime(brent["fecha"]).dt.to_period("M").dt.to_timestamp()
vb = m[["exportacion_m3", "exportacion_usd", "usd_por_bbl"]].join(brent.dropna().set_index("fecha")["brent"], how="inner")
vb = vb[(vb["exportacion_m3"] > 5000) & (vb.index <= CORTE)].dropna(subset=["usd_por_bbl", "brent"]).copy()
vb["dif_usd_bbl"] = vb["usd_por_bbl"] - vb["brent"]
vb.reset_index().assign(fecha=lambda d: d["fecha"].dt.strftime("%Y-%m-%d")).round(2).to_csv(os.path.join(WEB, "comex_validacion_brent.csv"), index=False)
dif_anual = vb.groupby(vb.index.year).apply(lambda d: float((d["exportacion_usd"].sum() / (d["exportacion_m3"].sum() * BBL_POR_M3)) - d["brent"].mean()), include_groups=False)

meta = {
    "anio_base": ANIO_BASE, "bases": BASES, "ultimo_mes_comex": str(ULTIMO_MES.date()),
    "registros_exportacion_crudo": int(len(ex)), "filas_repetidas_exactas": n_dup,
    "validacion_precios": {"meses": int(len(val)), "correlacion": round(float(val["usd_por_bbl"].corr(val["medanito_fob_oficial"])), 4),
                           "diferencia_media_pct": round(float((100 * (val["usd_por_bbl"] / val["medanito_fob_oficial"] - 1)).mean()), 2)},
    "validacion_brent": {"meses": int(len(vb)), "correlacion": round(float(vb["usd_por_bbl"].corr(vb["brent"])), 4),
                         "dif_anual_min": round(float(dif_anual.min()), 2), "dif_anual_max": round(float(dif_anual.max()), 2),
                         "meses_sobre_brent": int((vb["dif_usd_bbl"] > 0).sum())},
    "control_produccion": {"mes_con_diferencia": "2024-09", "shale_oficial_sobre_vm_por_pozo_pct": round(100 * sep24, 2),
                           "dif_cuenca_sep2024_m3": float(dif_cuenca.loc["2024-09-01"]),
                           "dif_cuenca_resto_2022_2025_m3_max_abs": float(dif_cuenca.drop(pd.Timestamp("2024-09-01")).abs().max())},
}
with open(os.path.join(WEB, "comex_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print(json.dumps(meta, ensure_ascii=False, indent=1))
print(an[["meses_con_exportacion", "exportacion_m3", "exportacion_usd", "usd_por_bbl", "pct_exportado_cuenca"]].round(1).to_string())
