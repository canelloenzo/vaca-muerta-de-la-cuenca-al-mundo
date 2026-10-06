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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
CLEAN = os.path.join(ROOT, "clean")


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

cols = ["fecha", "anio", "mes", "idducto", "denominacion_ducto", "empresa", "tipo_jurisdiccion",
        "n_tramos_reportados", "capacidad_operativa_maxima_m3_dia", "capacidad_disenio_m3_dia",
        "capacidad_empleada_m3_dia", "dias_mes", "capacidad_mensual_m3", "volumen_transportado",
        "capacidad_valida", "utilizacion_pct"]
fact = fact[cols].sort_values(["idducto", "fecha"])
fact.to_csv(os.path.join(CLEAN, "fact_capacidad_ductos.csv"), index=False, encoding="utf-8-sig")
print(f"\nfact_capacidad_ductos.csv -> {fact.shape}")
print("filas con capacidad_valida=False (capacidad reportada = 0):", (~fact["capacidad_valida"]).sum())
print("utilizacion_pct describe (solo capacidad_valida):\n", fact.loc[fact["capacidad_valida"], "utilizacion_pct"].describe())
valid = fact[fact["capacidad_valida"]]
print("filas con utilizacion_pct > 1 (posible sobre-nominal o cambio de capacidad intra-anio):",
      (valid["utilizacion_pct"] > 1).sum(), "/", len(valid),
      f"({(valid['utilizacion_pct'] > 1).mean()*100:.1f}%)")
