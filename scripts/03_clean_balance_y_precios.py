"""
Limpieza de:
  - Balance_2023_V0_H.xlsx, Balance_2024_V0_H.xlsx, balance_2025_v0_h.xlsx  -> Balance Energetico Nacional anual
  - precio-exportacion-crudo.xlsx (hojas "precios" y "tipos de crudo")

Hallazgo critico vs. la guia:
  - Los archivos "Balance_*" NO son el dataset "Comercio Exterior de Hidrocarburos por pais destino" que
    pide la guia. Son el Balance Energetico Nacional: 1 fila por FORMA DE ENERGIA (incluye electricidad,
    carbon, lena, biocombustibles, etc., no solo hidrocarburos), a nivel ANUAL (no mensual), en unidades de
    "miles de TEP" (tonelada equivalente de petroleo), sin apertura por pais. Sirven como contexto/validacion
    agregada a nivel pais (ej. "% de la produccion de petroleo que se exporto en el 2023"), pero no reemplazan
    una tabla de exportaciones mensuales por pais en USD -- ese dataset no esta entre los archivos entregados.
  - precio-exportacion-crudo.xlsx trae PRECIOS (USD/bbl) por tipo de crudo, no volumenes ni USD totales;
    sirve para estimar valor (volumen x precio) o como referencia de mercado, no como fact de comercio exterior.
"""
import os
import pandas as pd

from _rutas import RAW, CLEAN, WEB  # noqa: F401  (rutas configurables, ver _rutas.py)

BALANCE_FILES = {
    2023: "Balance_2023_V0_H.xlsx",
    2024: "Balance_2024_V0_H.xlsx",
    2025: "balance_2025_v0_h.xlsx",
}

CATEGORIA_COLS = {
    4: ("OFERTA", "PRODUCCION"),
    5: ("OFERTA", "IMPORTACION"),
    6: ("OFERTA", "VARIACION DE STOCK"),
    7: ("OFERTA", "EXPORTACION Y BUNKER"),
    8: ("OFERTA", "NO APROVECHADO"),
    9: ("OFERTA", "PERDIDAS"),
    10: ("OFERTA", "AJUSTES"),
    11: ("OFERTA", "OFERTA INTERNA"),
    12: ("CENTROS DE TRANSFORMACION", "CENTRALES ELECTRICAS - SERVICIO PUBLICO"),
    13: ("CENTROS DE TRANSFORMACION", "CENTRALES ELECTRICAS - AUTOPRODUCCION"),
    14: ("CENTROS DE TRANSFORMACION", "PLANTAS DE TRATAMIENTO DE GAS"),
    15: ("CENTROS DE TRANSFORMACION", "REFINERIAS"),
    16: ("CENTROS DE TRANSFORMACION", "ACEITERAS Y DESTILERIAS"),
    17: ("CENTROS DE TRANSFORMACION", "COQUERIAS"),
    18: ("CENTROS DE TRANSFORMACION", "CARBONERAS"),
    19: ("CENTROS DE TRANSFORMACION", "ALTOS HORNOS"),
    20: ("CONSUMO", "CONSUMO PROPIO"),
    21: ("CONSUMO", "CONSUMO FINAL TOTAL"),
    22: ("CONSUMO", "CONSUMO FINAL NO ENERGETICO"),
    23: ("CONSUMO", "RESIDENCIAL"),
    24: ("CONSUMO", "COMERCIAL Y PUBLICO"),
    25: ("CONSUMO", "TRANSPORTE"),
    26: ("CONSUMO", "AGROPECUARIO"),
    27: ("CONSUMO", "INDUSTRIA"),
}

rows_out = []
for anio, fname in BALANCE_FILES.items():
    path = os.path.join(RAW, fname)
    raw = pd.read_excel(path, sheet_name=0, header=None)
    grupo = None
    for i in range(len(raw)):
        g = raw.iat[i, 2] if pd.notna(raw.iat[i, 2]) else None
        if isinstance(g, str) and g.strip() in ("PRIMARIA", "SECUNDARIA"):
            grupo = g.strip()
        producto = raw.iat[i, 3] if raw.shape[1] > 3 else None
        if not isinstance(producto, str):
            continue
        producto = producto.strip()
        if producto in ("FORMAS DE ENERGÍA", "TOTAL I", "TOTAL II") or producto == "":
            continue
        if grupo is None:
            continue
        for col_idx, (categoria, subcategoria) in CATEGORIA_COLS.items():
            if col_idx >= raw.shape[1]:
                continue
            val = raw.iat[i, col_idx]
            if pd.isna(val):
                continue
            rows_out.append({
                "anio": anio,
                "grupo_energia": grupo,
                "producto": producto,
                "categoria": categoria,
                "subcategoria": subcategoria,
                "valor_miles_tep": val,
            })

balance = pd.DataFrame(rows_out)
balance["es_hidrocarburo"] = balance["producto"].str.lower().isin(
    ["gas natural de pozo", "petróleo", "gas distribuido por redes", "gas de refinería",
     "gas licuado", "gasolina natural", "otras naftas", "motonafta total",
     "kerosene y aerokerosene", "diesel oil + gas oil", "fuel oil"]
)
balance.to_csv(os.path.join(CLEAN, "fact_balance_energetico_nacional.csv"), index=False, encoding="utf-8-sig")
print(f"fact_balance_energetico_nacional.csv -> {balance.shape}")
print(balance["producto"].unique())

# ---------- precio-exportacion-crudo.xlsx ----------
path = os.path.join(RAW, "precio-exportacion-crudo.xlsx")
xl = pd.ExcelFile(path)

precios_raw = xl.parse("precios", header=None)
# fila 0 = titulo, fila 1 = blanco, fila 2 = tipo de precio (merged), fila 3 = 'Mes/Tipo crudo' + tipos de crudo, filas 4+ = datos
tipo_precio_row = precios_raw.iloc[2].ffill()
crudo_row = precios_raw.iloc[3]
data = precios_raw.iloc[4:].copy()
data.columns = range(data.shape[1])

long_rows = []
for col in range(1, data.shape[1]):
    tipo_precio = tipo_precio_row[col]
    tipo_crudo = crudo_row[col]
    if pd.isna(tipo_precio) or pd.isna(tipo_crudo):
        continue
    for _, r in data.iterrows():
        fecha = r[0]
        val = r[col]
        if pd.isna(fecha) or pd.isna(val):
            continue
        long_rows.append({
            "fecha": fecha,
            "tipo_precio": str(tipo_precio).strip(),
            "tipo_crudo": str(tipo_crudo).strip(),
            "precio_usd_bbl": val,
        })

precios = pd.DataFrame(long_rows)
precios["fecha"] = pd.to_datetime(precios["fecha"])
precios.to_csv(os.path.join(CLEAN, "dim_precio_exportacion_crudo.csv"), index=False, encoding="utf-8-sig")
print(f"dim_precio_exportacion_crudo.csv -> {precios.shape}")
print("tipo_precio unicos:", precios["tipo_precio"].unique())
print("tipo_crudo unicos:", precios["tipo_crudo"].unique())

tipos_crudo = xl.parse("tipos de crudo", header=1)
tipos_crudo.columns = [str(c).strip().lower().replace(" ", "_") for c in tipos_crudo.columns]
tipos_crudo.to_csv(os.path.join(CLEAN, "dim_tipo_crudo_cuenca.csv"), index=False, encoding="utf-8-sig")
print(f"dim_tipo_crudo_cuenca.csv -> {tipos_crudo.shape}")

print("\nOK - balance y precios procesados.")
