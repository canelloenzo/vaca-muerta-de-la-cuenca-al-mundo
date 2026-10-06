import os
import pandas as pd

from _rutas import RAW, CLEAN, WEB  # noqa: F401  (rutas configurables, ver _rutas.py)

files = [
    "anexo-2a-capacidad-de-transporte-de-hidrocarburos-a-travs-de-ductos.csv",
    "anexo-2b-capacidad-de-tanques-de-almacenamiento-de-hidrocarburos.csv",
    "anexo-2b-por-plantas-capacidad-de-plantas-de-almacenamiento-de-hidrocarburos.csv",
]

for f in files:
    path = os.path.join(RAW, f)
    size_kb = os.path.getsize(path) / 1024
    print(f"\n{'='*100}\n{f}  ({size_kb:,.1f} KB)\n{'='*100}")
    # raw bytes peek for encoding
    with open(path, "rb") as fh:
        raw = fh.read(200)
    print("raw bytes head:", raw)
    df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    df.columns = [c.replace("\ufeff", "").replace("ï»¿", "").strip() for c in df.columns]
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print(df.head(5).to_string())
    print("\ndtypes:\n", df.dtypes)
