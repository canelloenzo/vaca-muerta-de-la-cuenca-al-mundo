"""
Limpieza de transporte por ductos:
  - volumnenes-de-transporte-de-hidrocarburos-planilla-20.csv  (nivel ducto/tramo, mayormente domestico)
  - volumenes-de-transporte-de-hidrocarburos-planilla-21.csv   (nivel nodo/cargador, con pais destino explicito)
  - registro-del-midstream-ductos-empresas.csv                 (registro de ductos, dimension)

Hallazgo critico vs. la guia:
  - NINGUNO de estos archivos trae capacidad nominal de transporte. `registro-del-midstream-ductos-empresas.csv`
    trae longitud (km) y anio de construccion, pero no m3/dia de capacidad. El KPI de la guia
    "Utilizacion % = flujo_promedio / capacidad_nominal" NO se puede calcular con los datos entregados.
  - Planilla 20 tiene columna `pais` pero esta 99.1% vacia (solo se completa en filas de exportacion directa
    por ducto). Planilla 21 es la que sistematicamente registra pais destino (24 paises distintos), y es el
    mejor proxy disponible para "comercio exterior", pero es en VOLUMEN, no en USD.
"""
import os
import pandas as pd
import ftfy

from _rutas import RAW, CLEAN, WEB  # noqa: F401  (rutas configurables, ver _rutas.py)

# Un mismo ducto figura con dos idducto en el registro (INFERENCIA, no dato de origen): mismo nombre (salvo
# mayusculas), periodos contiguos y sin solape (255: 2018-01..2025-04 / 532: 2025-05..2026-06;
# 122: 2019-01..2025-04 / 533: 2025-05..2026-06). Se conservan los ids originales y se agregan
# `idducto_logico` / `denominacion_logica`; el alias se usa solo para contar ductos y unir nombres.
ALIAS_DUCTOS = {532: 255, 533: 122}


def estado_pais(original, corregido):
    """Conserva el motivo por el que `pais` queda vacio (la etiqueta original se pierde en PAIS_FIX)."""
    if isinstance(corregido, str):
        return "identificado"
    if original == "NO IDENTIFICADO":
        return "no_identificado"
    if original == "no aplica":
        return "no_aplica"
    return "sin_dato"


PAIS_FIX = {
    "GRAN BRETA�A": "GRAN BRETAÑA", "GRAN BRETAÃA": "GRAN BRETAÑA",
    "ESPA�A": "ESPAÑA", "ESPAÃA": "ESPAÑA",
    "no aplica": None, "NO IDENTIFICADO": None,
}


def read_raw_csv(fname):
    path = os.path.join(RAW, fname)
    df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    df.columns = [c.replace("\ufeff", "").replace("ï»¿", "").strip().lower() for c in df.columns]
    return df


def fix_text_col(s: pd.Series) -> pd.Series:
    return s.map(lambda v: ftfy.fix_text(v) if isinstance(v, str) else v)


def clean_text_columns(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = fix_text_col(df[c])
    return df


# ---------- registro-del-midstream-ductos-empresas.csv -> dim_ducto ----------
print("Procesando dim_ducto...")
ductos = read_raw_csv("registro-del-midstream-ductos-empresas.csv")
ductos = clean_text_columns(ductos, ["denominacion", "tipo_ducto", "provincia", "tipo_jurisdiccion", "empresa", "provincias_ducto"])
ductos["tipo_ducto"] = ductos["tipo_ducto"].str.strip()
ductos["anio_construccion"] = ductos["anio_construccion"].astype("Int64")
ductos["fechacargainfo"] = pd.to_datetime(ductos["fechacargainfo"], errors="coerce", utc=True).dt.tz_localize(None)
ductos = ductos.rename(columns={"longitud": "longitud_km"})
ductos["idducto_logico"] = ductos["idducto"].map(lambda i: ALIAS_DUCTOS.get(i, i))
ductos.to_csv(os.path.join(CLEAN, "dim_ducto.csv"), index=False, encoding="utf-8-sig")
print(f"dim_ducto.csv -> {ductos.shape}")

# ---------- planilla-20 -> fact_transporte_ductos ----------
print("Procesando fact_transporte_ductos (planilla 20)...")
p20 = read_raw_csv("volumnenes-de-transporte-de-hidrocarburos-planilla-20.csv")
text_cols_20 = ["empresa", "denominacion_ducto", "tipo_ducto", "tipo_jurisdiccion", "nodo_origen",
                 "nodo_destino", "tipo_destino", "area", "cargador", "tipo_producto", "producto",
                 "tipo_mercado", "tipo_operacion", "pais", "tramo_transporte", "obs"]
p20 = clean_text_columns(p20, text_cols_20)
p20["pais_original"] = p20["pais"]
p20["pais"] = p20["pais"].replace(PAIS_FIX)
p20["pais_estado"] = [estado_pais(o, c) for o, c in zip(p20["pais_original"], p20["pais"])]
p20["idducto_logico"] = p20["idducto"].map(lambda i: ALIAS_DUCTOS.get(i, i))
_den = p20.drop_duplicates("idducto").set_index("idducto")["denominacion_ducto"]
p20["denominacion_logica"] = p20["idducto_logico"].map(_den)
p20["fecha"] = pd.to_datetime(dict(year=p20["anio"], month=p20["mes"], day=1))
p20["es_operacion_exportacion"] = p20["tipo_operacion"].eq("Exportacion")
# `producto` trae 156 variantes de escritura (mayus/minus, espacios, tildes) para ~15 categorias reales
p20["producto_norm"] = (
    p20["producto"].str.strip().str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("utf-8")
)
p20 = p20.drop_duplicates()
# F13: 344 filas son identicas en todo salvo `longitud_tramo` (el volumen del ducto repetido por tramo: ductos 374, 489 y
# 156). Es doble conteo (con la repeticion, caudal/capacidad empleada da ~2,0; sin ella ~1,0). Se conserva una por grupo.
_n20 = len(p20)
p20 = p20.drop_duplicates(subset=[c for c in p20.columns if c != "longitud_tramo"])
print(f"planilla 20: {_n20 - len(p20)} filas repetidas por tramo eliminadas (F13)")
p20.to_csv(os.path.join(CLEAN, "fact_transporte_ductos.csv"), index=False, encoding="utf-8-sig")
print(f"fact_transporte_ductos.csv -> {p20.shape}")
print("cobertura idducto vs dim_ducto:", round(p20["idducto"].isin(ductos["idducto"]).mean(), 3))

# ---------- planilla-21 -> fact_movimientos_exportacion (proxy de comercio exterior, en volumen) ----------
print("Procesando fact_movimientos_exportacion (planilla 21)...")
p21 = read_raw_csv("volumenes-de-transporte-de-hidrocarburos-planilla-21.csv")
text_cols_21 = ["empresa", "nodo_origen", "tipo_mercado", "tipo_operacion", "pais", "cargador",
                 "producto", "obs", "nodo_destino"]
p21 = clean_text_columns(p21, text_cols_21)
p21["pais_original"] = p21["pais"]
p21["pais"] = p21["pais"].replace(PAIS_FIX)
p21["pais_estado"] = [estado_pais(o, c) for o, c in zip(p21["pais_original"], p21["pais"])]
p21["producto"] = p21["producto"].str.strip().str.rstrip(".")
p21["fecha"] = pd.to_datetime(dict(year=p21["anio"], month=p21["mes"], day=1))
p21 = p21.drop_duplicates()
p21.to_csv(os.path.join(CLEAN, "fact_movimientos_exportacion_ductos.csv"), index=False, encoding="utf-8-sig")
print(f"fact_movimientos_exportacion_ductos.csv -> {p21.shape}")

print("\nOK - transporte y ductos procesados.")
