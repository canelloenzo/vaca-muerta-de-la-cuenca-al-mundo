"""
Anexo 2A -> fact_capacidad_ductos.csv

Validaciones hechas antes de construir el KPI (ver conversación/plan_powerbi.md seccion 1.2):

1. Clave de union: `idtramo` NO es un espacio de IDs compartido con planilla 20 (fact_transporte_ductos):
   de 88 valores de idtramo que "matchean" numericamente entre ambos archivos, el idducto asociado coincide
   en apenas 1/88 -> coincidencia espuria, NO USAR idtramo como clave.
   `idducto` SI es una clave real y estable (viene del mismo registro de ductos): 70/91 idductos de Anexo 2A
   aparecen en fact_transporte_ductos.

2. Grano real de Anexo 2A: idducto x idtramo x cargador x anio (fila por asignacion de capacidad a cada
   cargador dentro de cada tramo). Se verifico que `capacidad_operativa_maxima` (y el resto de los campos de
   capacidad) es IDENTICO para todos los cargadores de un mismo tramo, y tambien IDENTICO entre tramos de un
   mismo ducto-anio en el 100% de los casos (0/77 grupos con mas de un tramo muestran variacion). Es decir,
   sumar por cargador o por tramo multiplicaria artificialmente la capacidad real del ducto. Se dedupe a
   grano idducto-anio quedandonos con un unico valor de capacidad.

3. Unidades: no hay columna de unidad explicita. Se comparo capacidad_operativa_maxima contra el promedio
   diario de `volumen` de fact_transporte_ductos (volumen mensual / dias del mes) para los mismos idducto+anio:
   el cociente cae sistematicamente en el orden de 1x-10x (nunca en O(1000) ni O(0.001)), lo que confirma que
   ambas magnitudes estan en la misma unidad base (m3) pero a distinta frecuencia: capacidad_operativa_maxima
   es un caudal DIARIO (m3/dia) mientras que volumen en fact_transporte_ductos es un total MENSUAL (m3/mes).
   Conclusion: para el % de utilizacion mensual hay que comparar volumen_mensual contra
   (capacidad_operativa_maxima * dias_del_mes), NO dividir volumen mensual por la capacidad diaria directamente.

4. Anexo 2A es ANUAL (dias_operativos ~365), no mensual. Para llevarlo a grano ducto-mes (pedido por el
   usuario) se replica el mismo valor de capacidad anual en los 12 meses del anio correspondiente -- se
   documenta como supuesto (capacidad constante intra-anio), no como dato medido mes a mes.
"""
import os
import numpy as np
import pandas as pd
import ftfy

from _rutas import RAW, CLEAN, WEB  # noqa: F401  (rutas configurables, ver _rutas.py)


def read_raw_csv(fname):
    df = pd.read_csv(os.path.join(RAW, fname), encoding="latin-1", low_memory=False)
    df.columns = [c.replace("\ufeff", "").replace("ï»¿", "").strip().lower() for c in df.columns]
    return df


def fix_text_col(s):
    return s.map(lambda v: ftfy.fix_text(v) if isinstance(v, str) else v)


a2a = read_raw_csv("anexo-2a-capacidad-de-transporte-de-hidrocarburos-a-travs-de-ductos.csv")
for c in ["empresa", "denominacion_ducto", "tipo_jurisdiccion", "capacidad_uso", "uso_mejorador", "tramo", "cargador", "observaciones"]:
    a2a[c] = fix_text_col(a2a[c])

# --- dedupe a grano idducto-anio (capacidad NO varia por tramo ni por cargador, ver docstring) ---
cap_anual = (
    a2a.drop_duplicates(subset=["idducto", "anio"])
    [["idducto", "denominacion_ducto", "empresa", "tipo_jurisdiccion", "anio",
      "capacidad_operativa_maxima", "capacidad_disenio", "capacidad_empleada", "dias_operativos"]]
    .rename(columns={
        "capacidad_operativa_maxima": "capacidad_operativa_maxima_m3_dia",
        "capacidad_disenio": "capacidad_disenio_m3_dia",
        "capacidad_empleada": "capacidad_empleada_m3_dia",
    })
    .reset_index(drop=True)
)
n_tramos = a2a.groupby(["idducto", "anio"])["idtramo"].nunique().rename("n_tramos_reportados").reset_index()
cap_anual = cap_anual.merge(n_tramos, on=["idducto", "anio"])
print("cap_anual (idducto-anio unico):", cap_anual.shape)

# --- volumen mensual real por idducto-anio-mes desde fact_transporte_ductos ---
p20 = pd.read_csv(os.path.join(CLEAN, "fact_transporte_ductos.csv"), encoding="utf-8-sig", low_memory=False)
vol_mensual = p20.groupby(["idducto", "anio", "mes"])["volumen"].sum().reset_index()

# --- cobertura del cruce, medida a nivel fila (grano pedido: ducto-mes) ---
total_ducto_mes = vol_mensual[["idducto", "anio"]].drop_duplicates().shape[0]
match_ducto_anio = vol_mensual[["idducto", "anio"]].drop_duplicates().merge(
    cap_anual[["idducto", "anio"]], on=["idducto", "anio"], how="inner"
).shape[0]
print(f"\nCobertura del cruce (grano idducto-anio, base = combinaciones idducto-anio con transporte real):")
print(f"  {match_ducto_anio} / {total_ducto_mes} = {match_ducto_anio/total_ducto_mes*100:.1f}%")

rows_total = len(vol_mensual)
rows_matched = vol_mensual.merge(cap_anual[["idducto", "anio"]], on=["idducto", "anio"], how="inner").shape[0]
print(f"Cobertura a nivel fila ducto-mes: {rows_matched} / {rows_total} = {rows_matched/rows_total*100:.1f}%")

# --- broadcast anual -> mensual y calculo de utilizacion ---
meses = pd.DataFrame({"mes": range(1, 13)})
cap_mensual = cap_anual.merge(meses, how="cross")
cap_mensual["fecha"] = pd.to_datetime(dict(year=cap_mensual["anio"], month=cap_mensual["mes"], day=1))
cap_mensual["dias_mes"] = cap_mensual["fecha"].dt.days_in_month

fact = cap_mensual.merge(vol_mensual, on=["idducto", "anio", "mes"], how="inner")
fact = fact.rename(columns={"volumen": "volumen_transportado"})
fact["capacidad_mensual_m3"] = fact["capacidad_operativa_maxima_m3_dia"] * fact["dias_mes"]
# 120/3603 filas (3.3%) tienen capacidad_operativa_maxima_m3_dia = 0 en el Anexo 2A crudo (ducto probablemente
# fuera de servicio o dato no cargado ese anio) -> se flagean en vez de dejar inf/NaN silencioso
fact["capacidad_valida"] = fact["capacidad_operativa_maxima_m3_dia"] > 0
fact["utilizacion_pct"] = np.where(fact["capacidad_valida"], fact["volumen_transportado"] / fact["capacidad_mensual_m3"], np.nan)

# ------------------------------------------------------------------------------------------------------
# Correcciones de la auditoria (F2, F3, F5). Las columnas `volumen_transportado` y `utilizacion_pct` se
# conservan por compatibilidad pero estan DEPRECADAS: suman TODOS los productos (incluido gas natural) y todos
# los segmentos en serie contra la capacidad de una sola fila. Las columnas nuevas corrigen eso.
# ------------------------------------------------------------------------------------------------------
R1_UMBRAL = float(os.environ.get("VM_R1_UMBRAL", 5))   # salto interanual de la capacidad operativa (veces)
R3_UMBRAL = float(os.environ.get("VM_R3_UMBRAL", 2))   # caudal liquido observado / capacidad empleada informada
R5_DIAS = int(os.environ.get("VM_R5_DIAS", 90))        # dias operativos informados en el Anexo 2A
DUCTOS_RETIRADOS_D2 = {(539, 2025): "D2"}               # VMOC 2025: decision del autor (capacidad vs caudal)
GAS_PRODUCTOS = {"gas", "gas natural", "gas 9300", "gas @9300"}   # solo si `tipo_producto` viene vacio
ALIAS_DUCTOS = {532: 255, 533: 122}                     # ver 02_clean_transporte_ductos.py (inferencia)

# 1) Numerador: solo liquidos (todo salvo gas natural). "Derivados del Gas" (GLP, LGN) son liquidos en m3.
p20["es_gas"] = (p20["tipo_producto"] == "Gas") | (p20["tipo_producto"].isna() & p20["producto_norm"].isin(GAS_PRODUCTOS))
liq = p20[~p20["es_gas"]]
llave = ["idducto", "anio", "mes"]
seg = liq.groupby(llave + ["nodo_origen", "nodo_destino"], dropna=False)["volumen"].sum().reset_index()
seg_mes = seg.groupby(llave).agg(volumen_segmento_mas_cargado=("volumen", "max"),
                                 n_segmentos_con_volumen=("volumen", lambda v: int((v > 0).sum()))).reset_index()
liq_mes = liq.groupby(llave)["volumen"].sum().rename("volumen_liquidos").reset_index()
gas_mes = p20[p20["es_gas"]].groupby(llave)["volumen"].sum().rename("volumen_gas").reset_index()
for extra in (liq_mes, gas_mes, seg_mes):
    fact = fact.merge(extra, on=llave, how="left")
for c in ("volumen_liquidos", "volumen_gas", "volumen_segmento_mas_cargado", "n_segmentos_con_volumen"):
    fact[c] = fact[c].fillna(0)
fact["n_segmentos_con_volumen"] = fact["n_segmentos_con_volumen"].astype(int)

# 2) Reglas de capacidad dudosa, por ducto-anio (la capacidad del Anexo 2A es anual)
ca = cap_anual[["idducto", "anio", "capacidad_operativa_maxima_m3_dia", "capacidad_disenio_m3_dia",
                "capacidad_empleada_m3_dia", "dias_operativos"]].sort_values(["idducto", "anio"]).reset_index(drop=True)
op, dis, emp = ca["capacidad_operativa_maxima_m3_dia"], ca["capacidad_disenio_m3_dia"], ca["capacidad_empleada_m3_dia"]
ca["_op_prev"] = op.groupby(ca["idducto"]).shift()
ca["_anio_prev"] = ca["anio"].groupby(ca["idducto"]).shift()
razon = op / ca["_op_prev"]
salto = ((ca["anio"] - ca["_anio_prev"]) == 1) & (op > 0) & (ca["_op_prev"] > 0) & (np.maximum(razon, 1 / razon) > R1_UMBRAL)
r1 = set(zip(ca.loc[salto, "idducto"], ca.loc[salto, "anio"])) | set(zip(ca.loc[salto, "idducto"], ca.loc[salto, "anio"] - 1))
# R3: caudal diario medio de liquidos (segmento mas cargado) en los meses con transporte / capacidad empleada informada
obs = fact.groupby(["idducto", "anio"]).apply(
    lambda d: d["volumen_segmento_mas_cargado"].sum() / d["dias_mes"].sum()).rename("_obs").reset_index()
ca = ca.merge(obs, on=["idducto", "anio"], how="left")
r3 = set(zip(ca.loc[(emp > 0) & (ca["_obs"] / emp > R3_UMBRAL), "idducto"], ca.loc[(emp > 0) & (ca["_obs"] / emp > R3_UMBRAL), "anio"]))     | set(zip(ca.loc[(emp == 0) & (op > 0) & (ca["_obs"] > 0), "idducto"], ca.loc[(emp == 0) & (op > 0) & (ca["_obs"] > 0), "anio"]))
r4 = set(zip(ca.loc[(op > 0) & (emp > 0) & (op < emp), "idducto"], ca.loc[(op > 0) & (emp > 0) & (op < emp), "anio"]))
r5 = set(zip(ca.loc[(op > 0) & (ca["dias_operativos"] <= R5_DIAS), "idducto"], ca.loc[(op > 0) & (ca["dias_operativos"] <= R5_DIAS), "anio"]))
trip = ca[op > 0].groupby(["capacidad_operativa_maxima_m3_dia", "capacidad_disenio_m3_dia", "capacidad_empleada_m3_dia"])["idducto"].nunique()
trip = set(trip[trip > 1].index)
en_trip = np.array([(a, b, c) in trip for a, b, c in zip(op, dis, emp)])
m_r2 = en_trip & (op > 0).to_numpy()
r2 = set(zip(ca.loc[m_r2, "idducto"], ca.loc[m_r2, "anio"]))
reglas = {"R1": r1, "R3": r3, "R4": r4, "R5": r5, "D2": set(DUCTOS_RETIRADOS_D2)}
claves = list(zip(ca["idducto"], ca["anio"]))
ca["motivo_capacidad_dudosa"] = [",".join(k for k, v in reglas.items() if key in v) for key in claves]
ca["capacidad_dudosa"] = ca["motivo_capacidad_dudosa"] != ""
ca["a_revisar_capacidad"] = [(key in r2) and not d for key, d in zip(claves, ca["capacidad_dudosa"])]
print(f"\nReglas de capacidad dudosa (R1 {R1_UMBRAL}x, R3 {R3_UMBRAL}x, R5 <= {R5_DIAS} dias): duct-anios con capacidad > 0 =",
      int((op > 0).sum()), "| dudosos =", int(ca["capacidad_dudosa"].sum()),
      {k: len(v) for k, v in reglas.items()}, "| a revisar (R2 solo) =", int(ca["a_revisar_capacidad"].sum()))
fact = fact.merge(ca[["idducto", "anio", "capacidad_dudosa", "a_revisar_capacidad", "motivo_capacidad_dudosa"]],
                  on=["idducto", "anio"], how="left")

# 3) Utilizacion nueva (razon 0-1, igual que el campo historico `utilizacion_pct`)
fact["utilizacion_liquidos_ratio"] = np.where(fact["capacidad_valida"], fact["volumen_liquidos"] / fact["capacidad_mensual_m3"], np.nan)
fact["utilizacion_segmento_mas_cargado_ratio"] = np.where(
    fact["capacidad_valida"], fact["volumen_segmento_mas_cargado"] / fact["capacidad_mensual_m3"], np.nan)
fact["idducto_logico"] = fact["idducto"].map(lambda i: ALIAS_DUCTOS.get(i, i))

cols = ["fecha", "anio", "mes", "idducto", "idducto_logico", "denominacion_ducto", "empresa", "tipo_jurisdiccion",
        "n_tramos_reportados", "capacidad_operativa_maxima_m3_dia", "capacidad_disenio_m3_dia",
        "capacidad_empleada_m3_dia", "dias_mes", "capacidad_mensual_m3", "volumen_transportado",
        "capacidad_valida", "utilizacion_pct",
        "volumen_liquidos", "volumen_gas", "volumen_segmento_mas_cargado", "n_segmentos_con_volumen",
        "utilizacion_liquidos_ratio", "utilizacion_segmento_mas_cargado_ratio",
        "capacidad_dudosa", "a_revisar_capacidad", "motivo_capacidad_dudosa"]
fact = fact[cols].sort_values(["idducto", "fecha"])
fact.to_csv(os.path.join(CLEAN, "fact_capacidad_ductos.csv"), index=False, encoding="utf-8-sig")
print(f"\nfact_capacidad_ductos.csv -> {fact.shape}")
print("filas con capacidad_valida=False (capacidad reportada = 0):", (~fact["capacidad_valida"]).sum())
print("utilizacion_pct describe (solo capacidad_valida):\n", fact.loc[fact["capacidad_valida"], "utilizacion_pct"].describe())
valid = fact[fact["capacidad_valida"]]
print("filas con utilizacion_pct > 1 (posible sobre-nominal o cambio de capacidad intra-anio):",
      (valid["utilizacion_pct"] > 1).sum(), "/", len(valid),
      f"({(valid['utilizacion_pct'] > 1).mean()*100:.1f}%)")
