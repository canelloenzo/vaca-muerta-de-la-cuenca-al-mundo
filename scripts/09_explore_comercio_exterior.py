import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
FILE = "TD_comercioexterior.xlsx"

path = os.path.join(RAW, FILE)
size_kb = os.path.getsize(path) / 1024
print(f"\n{'='*100}\n{FILE}  ({size_kb:,.1f} KB)\n{'='*100}")

xls = pd.ExcelFile(path)
print("hojas:", xls.sheet_names)

for sheet in xls.sheet_names:
    print(f"\n{'-'*100}\nhoja: {sheet}\n{'-'*100}")
    df = pd.read_excel(path, sheet_name=sheet, nrows=20)
    print("shape (primeras 20 filas leidas):", df.shape)
    print("columns:", list(df.columns))
    print(df.head(10).to_string())
    print("\ndtypes:\n", df.dtypes)

    # shape real de la hoja completa (sin limitar filas)
    full = pd.read_excel(path, sheet_name=sheet)
    print("\nshape completo:", full.shape)
    for col in full.columns:
        nun = full[col].nunique(dropna=True)
        if nun <= 30:
            print(f"  valores unicos de '{col}' ({nun}):", sorted(full[col].dropna().unique().tolist(), key=str))
        else:
            print(f"  '{col}': {nun} valores unicos (muestra):", full[col].dropna().unique()[:10].tolist())
