import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(ROOT, "clean")

for f in ["fact_produccion_pozo_mes_vaca_muerta.csv", "fact_produccion_yacimiento_mes_vaca_muerta.csv"]:
    df = pd.read_csv(os.path.join(CLEAN, f), encoding="utf-8-sig", low_memory=False)
    print(f"\n{f}  shape={df.shape}")
    print("anio range:", df["anio"].min(), df["anio"].max())
    print("tipo_de_recurso:\n", df["tipo_de_recurso"].value_counts(dropna=False))
    if "sub_tipo_recurso" in df.columns:
        print("sub_tipo_recurso:\n", df["sub_tipo_recurso"].value_counts(dropna=False))
    print("nulls:\n", (df.isnull().mean() * 100).round(1))
    if "prod_pet_bbl" in df.columns:
        print("total prod_pet_bbl:", df["prod_pet_bbl"].sum())
        print("filas con prod_pet_m3 negativo:", (df["prod_pet_m3"] < 0).sum())
        print("filas con prod_gas_miles_m3 negativo:", (df["prod_gas_miles_m3"] < 0).sum())
