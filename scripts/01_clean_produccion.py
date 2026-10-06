"""
Limpieza del dataset de produccion de pozos (gas y petroleo), filtrado a formacion Vaca Muerta.

Fuentes reales (data/raw/):
  - produccin-de-pozos-de-gas-y-petrleo-2022.csv .. -2025.csv   (combinado convencional + no convencional, 2022-2025)
  - produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv    (solo no convencional, 2006-2026, incluye coordenadas)

Hallazgos clave vs. la guia original:
  - El campo que contiene el string "Vaca Muerta" es `formacion` (texto largo, minusculas, sin tilde:
    "vaca muerta"), NO `formprod` (que es un codigo corto, ej. "VMUT"). La guia apuntaba al campo equivocado.
  - No existe columna `periodo` (AAAAMM); la fecha esta partida en `anio` (int) y `mes` (int).
  - No existe columna `dias_del_mes`; se calcula a partir de anio/mes.
  - Vaca Muerta tiene pozos tipo_de_recurso = CONVENCIONAL y NO CONVENCIONAL (no es un area 100% no convencional).
  - El archivo "no-convencional" SOLAPA 100% con las filas NO CONVENCIONAL de los archivos anuales 2022-2025
    (verificado para 2023: 43219/43219 filas coinciden exactamente en prod_pet). Se usa unicamente para
    aportar el historico 2006-2021, que no esta en los archivos anuales.
  - Las coordenadas (coordenadax/coordenaday) SOLO existen en el archivo no-convencional -> los pozos
    convencionales de Vaca Muerta (y todo 2022-2025 convencional) no tienen coordenadas en estos datos crudos.
  - CORRECCION (2026-09-10): el diagnostico de encoding de abajo estaba MAL. Verificado a nivel de bytes: los
    crudos son UTF-8 puro con BOM (ej. cuenca "ÑIRIHUAU" esta guardada como los bytes 0xC3 0x91 + "IRIHUAU",
    que es exactamente la codificacion UTF-8 correcta de "Ñ" -- no hay perdida de caracter en origen). El
    mojibake que se observaba era autoinfligido: este script lee con encoding="latin-1", que reinterpreta mal
    los bytes UTF-8 y fabrica el "ÃIRIHUAU"/caracteres rotos que despues repara ftfy + CUENCA_FIX. Funciona en
    la practica (se verifico que clean/ no tiene caracteres de reemplazo reales), pero es una vuelta innecesaria:
    leer directamente con encoding="utf-8-sig" evitaria el problema de raiz y permitiria sacar la dependencia de
    ftfy y el diccionario CUENCA_FIX. Se deja documentado para una futura simplificacion, no se reescribio el
    pipeline en esta pasada para no invalidar los archivos ya generados en clean/ sin motivo.
"""
import os
import pandas as pd
import numpy as np
import ftfy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
CLEAN = os.path.join(ROOT, "clean")

BBL_PER_M3 = 6.2898

CUENCA_FIX = {
    "ÃIRIHUAU": "ÑIRIHUAU",
    "CAÃADON ASFALTO": "CAÑADON ASFALTO",
}

YEARLY_FILES = [
    "produccin-de-pozos-de-gas-y-petrleo-2022.csv",
    "produccin-de-pozos-de-gas-y-petrleo-2023.csv",
    "produccin-de-pozos-de-gas-y-petrleo-2024.csv",
    "produccin-de-pozos-de-gas-y-petrleo-2025.csv",
]
NC_FILE = "produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv"

KEEP_COLS = [
    "idempresa", "anio", "mes", "idpozo", "prod_pet", "prod_gas", "prod_agua",
    "tef", "tipoestado", "tipopozo", "empresa", "sigla", "formprod", "formacion",
    "areapermisoconcesion", "areayacimiento", "cuenca", "provincia",
    "tipo_de_recurso", "clasificacion", "subclasificacion", "sub_tipo_recurso",
]


def read_raw_csv(fname):
    path = os.path.join(RAW, fname)
    df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    df.columns = [c.replace("\ufeff", "").replace("ï»¿", "").strip().lower() for c in df.columns]
    return df


def fix_text_col(s: pd.Series) -> pd.Series:
    return s.map(lambda v: ftfy.fix_text(v) if isinstance(v, str) else v)


def clean_text_columns(df: pd.DataFrame, cols) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = fix_text_col(df[c])
            df[c] = df[c].replace(CUENCA_FIX)
    return df


def filter_vaca_muerta(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["formacion"].str.contains("vaca muerta", case=False, na=False)
    return df.loc[mask].copy()


TEXT_COLS = ["empresa", "sigla", "formacion", "areapermisoconcesion", "areayacimiento",
             "cuenca", "provincia", "tipo_de_recurso", "clasificacion", "subclasificacion",
             "sub_tipo_recurso", "tipoestado", "tipopozo"]

frames = []

print("Procesando archivos anuales 2022-2025 (fuente principal, convencional + no convencional)...")
for fname in YEARLY_FILES:
    print(" ->", fname)
    df = read_raw_csv(fname)
    df = df[[c for c in KEEP_COLS if c in df.columns]]
    df = clean_text_columns(df, TEXT_COLS)
    vm = filter_vaca_muerta(df)
    vm["fuente"] = "anual_2022_2025"
    frames.append(vm)
    del df

print("Procesando archivo no-convencional (aporta historico 2006-2021)...")
dfnc = read_raw_csv(NC_FILE)
dfnc_cols = [c for c in KEEP_COLS if c in dfnc.columns] + ["coordenadax", "coordenaday"]
dfnc = dfnc[dfnc_cols]
dfnc = clean_text_columns(dfnc, TEXT_COLS)
vm_nc = filter_vaca_muerta(dfnc)
vm_nc_hist = vm_nc[vm_nc["anio"] < 2022].copy()
vm_nc_hist["fuente"] = "no_convencional_historico_pre2022"
print(f"   filas historicas 2006-2021 incorporadas: {len(vm_nc_hist)}")

# Tabla de coordenadas por pozo (unica fuente que las tiene), para uso opcional como dimension
coords = vm_nc[["idpozo", "coordenadax", "coordenaday"]].dropna().drop_duplicates(subset="idpozo")
coords.to_csv(os.path.join(CLEAN, "dim_pozo_coordenadas_no_convencional.csv"), index=False, encoding="utf-8-sig")
print(f"dim_pozo_coordenadas_no_convencional.csv -> {len(coords)} pozos con coordenadas (solo no convencionales)")

del dfnc, vm_nc

frames.append(vm_nc_hist)
full = pd.concat(frames, ignore_index=True)
del frames

# --- Deduplicar por si acaso (idempresa+idpozo+anio+mes deberia ser unico) ---
before = len(full)
full = full.drop_duplicates(subset=["idempresa", "idpozo", "anio", "mes"])
print(f"Filas totales Vaca Muerta 2006-2025: {before} -> tras dedupe: {len(full)}")

# --- Conversion de unidades y fecha ---
full["prod_pet_bbl"] = full["prod_pet"] * BBL_PER_M3
full["fecha"] = pd.to_datetime(dict(year=full["anio"], month=full["mes"], day=1))
full["dias_mes"] = full["fecha"].dt.days_in_month

full = full.rename(columns={
    "prod_pet": "prod_pet_m3",
    "prod_gas": "prod_gas_miles_m3",
    "prod_agua": "prod_agua_m3",
})

# --- Nivel de detalle: pozo-mes (grano completo, listo para agregar en Power BI) ---
pozo_mes_cols = [
    "fecha", "anio", "mes", "idempresa", "empresa", "idpozo", "sigla",
    "formprod", "formacion", "tipo_de_recurso", "sub_tipo_recurso",
    "clasificacion", "subclasificacion", "cuenca", "provincia",
    "areapermisoconcesion", "areayacimiento", "tipoestado", "tipopozo",
    "prod_pet_m3", "prod_pet_bbl", "prod_gas_miles_m3", "prod_agua_m3",
    "tef", "dias_mes", "fuente",
]
pozo_mes = full[pozo_mes_cols].copy()
pozo_mes.to_csv(os.path.join(CLEAN, "fact_produccion_pozo_mes_vaca_muerta.csv"), index=False, encoding="utf-8-sig")
print(f"fact_produccion_pozo_mes_vaca_muerta.csv -> {pozo_mes.shape}")

# --- Nivel agregado: yacimiento-provincia-mes (esquema sugerido por la guia, corregido) ---
agg = (
    full.groupby(["fecha", "anio", "mes", "areayacimiento", "provincia", "cuenca",
                   "tipo_de_recurso", "sub_tipo_recurso"], dropna=False)
    .agg(
        prod_pet_bbl=("prod_pet_bbl", "sum"),
        prod_pet_m3=("prod_pet_m3", "sum"),
        prod_gas_miles_m3=("prod_gas_miles_m3", "sum"),
        prod_agua_m3=("prod_agua_m3", "sum"),
        pozos_reportados=("idpozo", "nunique"),
        dias_mes=("dias_mes", "first"),
    )
    .reset_index()
)
group_cols = ["fecha", "anio", "mes", "areayacimiento", "provincia", "cuenca", "tipo_de_recurso", "sub_tipo_recurso"]
productivos = (
    full[full["prod_pet_m3"] > 0]
    .groupby(group_cols, dropna=False)["idpozo"]
    .nunique()
    .reset_index(name="pozos_productivos")
)
agg = agg.merge(productivos, on=group_cols, how="left")
agg["pozos_productivos"] = agg["pozos_productivos"].fillna(0).astype(int)
agg.to_csv(os.path.join(CLEAN, "fact_produccion_yacimiento_mes_vaca_muerta.csv"), index=False, encoding="utf-8-sig")
print(f"fact_produccion_yacimiento_mes_vaca_muerta.csv -> {agg.shape}")

print("\nOK - produccion procesada.")
