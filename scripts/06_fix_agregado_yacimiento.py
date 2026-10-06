"""
Reconstruye fact_produccion_yacimiento_mes_vaca_muerta.csv a partir de fact_produccion_pozo_mes_vaca_muerta.csv
(ya limpia), corrigiendo un bug de desalineacion de indice en el calculo de `pozos_productivos` del script 01
(el groupby+transform se hacia sobre un subset filtrado y se asignaba por posicion a un dataframe con otro
indice, generando ~37% de nulos espurios).
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(ROOT, "clean")

full = pd.read_csv(os.path.join(CLEAN, "fact_produccion_pozo_mes_vaca_muerta.csv"), encoding="utf-8-sig", low_memory=False)
full["fecha"] = pd.to_datetime(full["fecha"])

group_cols = ["fecha", "anio", "mes", "areayacimiento", "provincia", "cuenca", "tipo_de_recurso", "sub_tipo_recurso"]

agg = (
    full.groupby(group_cols, dropna=False)
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

productivos = (
    full[full["prod_pet_m3"] > 0]
    .groupby(group_cols, dropna=False)["idpozo"]
    .nunique()
    .reset_index(name="pozos_productivos")
)

agg = agg.merge(productivos, on=group_cols, how="left")
agg["pozos_productivos"] = agg["pozos_productivos"].fillna(0).astype(int)

agg.to_csv(os.path.join(CLEAN, "fact_produccion_yacimiento_mes_vaca_muerta.csv"), index=False, encoding="utf-8-sig")
print("fact_produccion_yacimiento_mes_vaca_muerta.csv ->", agg.shape)
print("nulls pozos_productivos tras fix:", agg["pozos_productivos"].isnull().mean())
print("total prod_pet_bbl (debe matchear 722439535.1074312):", agg["prod_pet_bbl"].sum())
