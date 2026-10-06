"""Utilidades de las pruebas: rutas, lectores independientes de raw/ y recálculos.

Los recálculos NO importan los scripts de scripts/: reimplementan cada cuenta a partir de raw/ para que
una prueba pueda detectar un error del pipeline.

Variables de entorno (ver README, sección "Cómo correr las pruebas"):
  VM_DATA_ROOT  carpeta que contiene raw/ y clean/ (por defecto ../data si existe, si no la raíz del repo)
  VM_RAW_DIR    sobreescribe raw/
  VM_CLEAN_DIR  sobreescribe clean/
"""
import json
import os
import pickle
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "tests" / ".cache"
WEB = REPO / "data" / "web"
BBL_PER_M3 = 6.2898

RAW_ANUALES = [f"produccin-de-pozos-de-gas-y-petrleo-{y}.csv" for y in (2022, 2023, 2024, 2025)]
RAW_NC = "produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv"
RAW_P20 = "volumnenes-de-transporte-de-hidrocarburos-planilla-20.csv"
RAW_P21 = "volumenes-de-transporte-de-hidrocarburos-planilla-21.csv"
RAW_ANEXO2A = "anexo-2a-capacidad-de-transporte-de-hidrocarburos-a-travs-de-ductos.csv"
RAW_BALANCE = {2023: "Balance_2023_V0_H.xlsx", 2024: "Balance_2024_V0_H.xlsx", 2025: "balance_2025_v0_h.xlsx"}
DUCTOS_EXCLUIDOS_ORIGINAL = {42, 97, 149, 171, 221, 329}
OPERADORES_NEUQUINOS = ["Oiltanking EBYTEM S.A.", "Refineria Bahia Blanca SAU"]
GAS_PRODUCTOS = {"gas", "gas natural", "gas 9300", "gas @9300"}   # gas natural; los derivados del gas (GLP, LGN) son liquidos


def data_root() -> Path:
    env = os.environ.get("VM_DATA_ROOT")
    if env:
        return Path(env)
    sib = REPO.parent / "data"
    return sib if (sib / "raw").exists() else REPO


def raw_dir() -> Path:
    return Path(os.environ.get("VM_RAW_DIR") or data_root() / "raw")


def clean_dir() -> Path:
    return Path(os.environ.get("VM_CLEAN_DIR") or data_root() / "clean")


def norm(s) -> str:
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()


def _cache_key(paths) -> str:
    return "|".join(f"{p.name}:{p.stat().st_size}" for p in paths)


def _cached(name, paths, builder):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = _cache_key(paths)
    f = CACHE / f"{name}.pkl"
    if f.exists():
        with open(f, "rb") as fh:
            k, obj = pickle.load(fh)
        if k == key:
            return obj
    obj = builder()
    with open(f, "wb") as fh:
        pickle.dump((key, obj), fh)
    return obj


# ----------------------------------------------------------------------------------------------
# Producción (raw)
# ----------------------------------------------------------------------------------------------
PROD_COLS = ["idempresa", "anio", "mes", "idpozo", "prod_pet", "prod_gas", "prod_agua", "tef", "formacion",
             "areayacimiento", "cuenca", "provincia", "tipo_de_recurso", "sub_tipo_recurso", "rectificado",
             "coordenadax", "coordenaday", "tipopozo", "tipoestado"]


def _read_prod(path: Path, solo_vm: bool) -> pd.DataFrame:
    hdr = pd.read_csv(path, encoding="utf-8-sig", nrows=0).columns.tolist()
    df = pd.read_csv(path, encoding="utf-8-sig", usecols=[c for c in PROD_COLS if c in hdr], low_memory=False)
    n_raw = len(df)
    if solo_vm:
        df = df[df.formacion.fillna("").map(norm).str.contains("vaca muerta")]
    df.attrs["filas_raw"] = n_raw
    return df


def vm_raw():
    """dict con filas de Vaca Muerta por archivo crudo y el conteo de filas crudas."""
    paths = [raw_dir() / f for f in RAW_ANUALES + [RAW_NC]]

    def build():
        out = {"filas_raw": {}, "anual": [], "nc": None}
        for f in RAW_ANUALES:
            d = _read_prod(raw_dir() / f, True)
            out["filas_raw"][f] = d.attrs["filas_raw"]
            out["anual"].append(d)
        d = _read_prod(raw_dir() / RAW_NC, True)
        out["filas_raw"][RAW_NC] = d.attrs["filas_raw"]
        out["nc"] = d
        return out

    return _cached("vm_raw", paths, build)


def vm_dedup(raw=None) -> pd.DataFrame:
    """Reconstrucción independiente de la tabla pozo-mes: anuales 2022-2025 + NC histórico (< 2022)."""
    raw = raw or vm_raw()
    ann = pd.concat(raw["anual"], ignore_index=True)
    hist = raw["nc"][raw["nc"].anio < 2022]
    full = pd.concat([ann, hist], ignore_index=True).drop_duplicates(["idempresa", "idpozo", "anio", "mes"])
    full["fecha"] = pd.to_datetime(dict(year=full.anio, month=full.mes, day=1))
    full["dias"] = full.fecha.dt.days_in_month
    full["bbl"] = full.prod_pet * BBL_PER_M3
    return full


def monthly_bbl_dia(full: pd.DataFrame) -> pd.Series:
    g = full.groupby("fecha").agg(bbl=("bbl", "sum"), dias=("dias", "first"))
    return g.bbl / g.dias


# ----------------------------------------------------------------------------------------------
# Exportación (planilla 21) y transporte (planilla 20)
# ----------------------------------------------------------------------------------------------
def p21_raw() -> pd.DataFrame:
    return pd.read_csv(raw_dir() / RAW_P21, encoding="utf-8-sig", low_memory=False)


def p21_export() -> pd.DataFrame:
    """Filas de exportación (tipo_operacion == Exportacion) sin duplicados exactos."""
    r = p21_raw().drop_duplicates()
    ex = r[r.tipo_operacion == "Exportacion"].copy()
    ex["fecha"] = pd.to_datetime(dict(year=ex.anio, month=ex.mes, day=1))
    return ex


def p20_raw() -> pd.DataFrame:
    return pd.read_csv(raw_dir() / RAW_P20, encoding="utf-8-sig", low_memory=False)


def p20_dedup() -> pd.DataFrame:
    """Planilla 20 sin duplicados exactos ni filas repetidas solo por `longitud_tramo` (F13: doble conteo por tramo)."""
    t = p20_raw().drop_duplicates()
    return t.drop_duplicates(subset=[c for c in t.columns if c != "longitud_tramo"])


def anexo2a_raw() -> pd.DataFrame:
    a = pd.read_csv(raw_dir() / RAW_ANEXO2A, encoding="utf-8-sig", low_memory=False)
    a.columns = [c.strip().lower() for c in a.columns]
    return a


# ----------------------------------------------------------------------------------------------
# Tablas limpias y publicadas
# ----------------------------------------------------------------------------------------------
def clean(name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(clean_dir() / name, encoding="utf-8-sig", low_memory=False, **kw)


def web(name: str) -> pd.DataFrame:
    return pd.read_csv(WEB / name)


def web_json(name: str) -> dict:
    return json.loads((WEB / name).read_text(encoding="utf-8"))


def html_text() -> str:
    return (REPO / "docs" / "index.html").read_text(encoding="utf-8")


def html_data() -> dict:
    m = re.search(r"const DATA = (\{.*?\});\s*\n", html_text(), re.S)
    return json.loads(m.group(1))


def html_visible_text() -> str:
    h = html_text()
    body = h[h.find("<body"):]
    body = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", body)
    return " ".join(re.sub(r"<[^>]+>", " ", body).split())


def html_js_strings() -> str:
    """Texto de usuario que arma el JavaScript (fuera del objeto DATA)."""
    h = html_text()
    scripts = re.findall(r"<script(?![^>]*src)[^>]*>([\s\S]*?)</script>", h)
    js = scripts[0] if scripts else ""
    js = re.sub(r"const DATA = \{.*?\};\s*\n", "", js, flags=re.S)
    return js


# ----------------------------------------------------------------------------------------------
# Utilización de ductos (recálculo independiente desde raw/)
# ----------------------------------------------------------------------------------------------
def util_ducto_mes() -> pd.DataFrame:
    """Por ducto-mes: volumen total, de líquidos, de gas, segmento más cargado (líquidos) y capacidades anuales."""
    paths = [raw_dir() / RAW_P20, raw_dir() / RAW_ANEXO2A]

    def build():
        t = p20_dedup()
        pn = t.producto.fillna("").map(norm).str.replace(r"\s+", " ", regex=True)
        t["liq"] = ~((t.tipo_producto == "Gas") | (t.tipo_producto.isna() & pn.isin(GAS_PRODUCTOS)))
        a = anexo2a_raw()
        ca = a.groupby(["idducto", "anio"]).agg(
            op=("capacidad_operativa_maxima", "first"), dis=("capacidad_disenio", "first"),
            emp=("capacidad_empleada", "first"), diasop=("dias_operativos", "first"),
            ntramos=("idtramo", "nunique")).reset_index()
        rows = []
        for (i, y, m), d in t.groupby(["idducto", "anio", "mes"]):
            liq = d[d.liq]
            seg = liq.groupby(["nodo_origen", "nodo_destino"]).volumen.sum() if len(liq) else pd.Series(dtype=float)
            rows.append((i, y, m, d.volumen.sum(), liq.volumen.sum(), d[~d.liq].volumen.sum(),
                         seg.max() if len(seg) else 0.0, int((seg > 0).sum())))
        mes = pd.DataFrame(rows, columns=["idducto", "anio", "mes", "vol_total", "vol_liq", "vol_gas", "vol_segmax", "nseg"])
        mes["dias"] = pd.to_datetime(dict(year=mes.anio, month=mes.mes, day=1)).dt.days_in_month
        return mes.merge(ca, on=["idducto", "anio"], how="inner")

    return _cached("util_ducto_mes_v3_sin_doble_conteo_tramo", paths, build)   # el nombre cambia si cambia la definición de líquido


def utilizacion(df: pd.DataFrame, num: str, cap: str = "op") -> float:
    d = df[df[cap] > 0]
    return 100 * d[num].sum() / (d[cap] * d.dias).sum()


# ----------------------------------------------------------------------------------------------
# Cuenca Neuquina (producción total) y exportación por terminal
# ----------------------------------------------------------------------------------------------
def cuenca_raw():
    """Producción mensual (m3) de toda la cuenca NEUQUINA desde los archivos anuales 2022-2025 (conv + NC) y NC histórico."""
    paths = [raw_dir() / f for f in RAW_ANUALES + [RAW_NC]]

    def build():
        cols = ["idempresa", "anio", "mes", "idpozo", "prod_pet", "formacion", "cuenca", "tipo_de_recurso"]

        def leer(f):
            d = pd.read_csv(raw_dir() / f, encoding="utf-8-sig", usecols=cols, low_memory=False)
            d = d[d.cuenca.fillna("").map(norm) == "neuquina"].drop_duplicates(["idempresa", "idpozo", "anio", "mes"])
            d["vm"] = d.formacion.fillna("").map(norm).str.contains("vaca muerta")
            d["fecha"] = pd.to_datetime(dict(year=d.anio, month=d.mes, day=1))
            return d
        ann = pd.concat([leer(f) for f in RAW_ANUALES], ignore_index=True)
        ncd = leer(RAW_NC)
        return {"anual": ann.groupby("fecha").prod_pet.sum(), "anual_conv": ann[ann.tipo_de_recurso == "CONVENCIONAL"].groupby("fecha").prod_pet.sum(),
                "anual_vm": ann[ann.vm].groupby("fecha").prod_pet.sum(), "nc": ncd.groupby("fecha").prod_pet.sum(),
                "nc_vm": ncd[ncd.vm].groupby("fecha").prod_pet.sum(), "nc_anual": ann[ann.tipo_de_recurso == "NO CONVENCIONAL"].groupby("fecha").prod_pet.sum()}

    return _cached("cuenca_raw", paths, build)


def export_neuquina_mensual(ex: pd.DataFrame) -> pd.Series:
    return ex[ex.empresa.isin(OPERADORES_NEUQUINOS)].groupby("fecha").volumen.sum()


def bbl_dia(m3, fechas):
    return m3 * BBL_PER_M3 / pd.DatetimeIndex(fechas).days_in_month


def reglas_capacidad(util: pd.DataFrame, r1=5.0, r3=2.0, r5=90):
    """Implementación independiente de las reglas R1, R3, R4, R5 y R2 (a revisar). Devuelve sets de (idducto, anio)."""
    a = anexo2a_raw()
    ca = a.groupby(["idducto", "anio"]).agg(op=("capacidad_operativa_maxima", "first"), dis=("capacidad_disenio", "first"),
                                            emp=("capacidad_empleada", "first"), diasop=("dias_operativos", "first")).reset_index()
    ca = ca.sort_values(["idducto", "anio"]).reset_index(drop=True)
    out = {"R1": set(), "R3": set(), "R4": set(), "R5": set(), "R2": set(), "R6": set()}
    for i, d in ca.groupby("idducto"):
        d = d.reset_index(drop=True)
        for k in range(1, len(d)):
            o0, o1 = d.op[k - 1], d.op[k]
            if d.anio[k] - d.anio[k - 1] == 1 and o0 > 0 and o1 > 0 and max(o1 / o0, o0 / o1) > r1:
                out["R1"] |= {(i, int(d.anio[k])), (i, int(d.anio[k - 1]))}
    obs = util.groupby(["idducto", "anio"]).apply(lambda g: g.vol_segmax.sum() / g.dias.sum(), include_groups=False)
    for _, r in ca.iterrows():
        key = (r.idducto, int(r.anio))
        o = obs.get(key, np.nan)
        if r.emp > 0 and o / r.emp > r3:
            out["R3"].add(key)
        if r.emp == 0 and r.op > 0 and o > 0:
            out["R3"].add(key)
        if r.op > 0 and r.emp > 0 and r.op < r.emp:
            out["R4"].add(key)
        if r.op > 0 and r.diasop <= r5:
            out["R5"].add(key)
        if r.op > 0 and r.op == r.dis == r.emp:
            out["R6"].add(key)
    trip = ca[ca.op > 0].groupby(["op", "dis", "emp"]).idducto.nunique()
    trip = set(trip[trip > 1].index)
    for _, r in ca.iterrows():
        if r.op > 0 and (r.op, r.dis, r.emp) in trip:
            out["R2"].add((r.idducto, int(r.anio)))
    return out
