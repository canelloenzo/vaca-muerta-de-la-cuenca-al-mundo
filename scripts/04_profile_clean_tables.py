import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(ROOT, "clean")

pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 200)

for fname in sorted(os.listdir(CLEAN)):
    if not fname.endswith(".csv"):
        continue
    path = os.path.join(CLEAN, fname)
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    print(f"\n{'='*100}\n{fname}  shape={df.shape}\n{'='*100}")
    for col in df.columns:
        s = df[col]
        null_pct = round(s.isnull().mean() * 100, 1)
        nunique = s.nunique(dropna=True)
        dtype = s.dtype
        sample = s.dropna().unique()[:4].tolist()
        print(f"  {col:35s} dtype={str(dtype):10s} nulls={null_pct:5.1f}%  nunique={nunique:8d}  sample={sample}")
