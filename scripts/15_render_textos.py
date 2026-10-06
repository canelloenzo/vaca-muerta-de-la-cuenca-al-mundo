"""
Genera los textos publicados a partir de plantillas y del registro de cifras (data/web/registro_cifras.json):

  documentacion/plantillas/index_*.{html,js}  ->  docs/index.html   (con el objeto DATA embebido, armado desde data/web/)
  documentacion/plantillas/README.plantilla.md -> README.md
  documentacion/plantillas/HANDOFF.plantilla.md -> HANDOFF_CHAT.md  (si existe)

Marcadores: {{clave}} o {{clave:N}} (N = decimales, formato es-AR) toman el valor del registro;
{{TABLA_*}} y {{LISTA_*}} son fragmentos armados aca con valores del registro. Si falta una clave, el script falla.
"""
import json
import math
import os
import re

import pandas as pd

from _rutas import REPO, WEB

PLANT = REPO / "documentacion" / "plantillas"
REG = json.load(open(os.path.join(WEB, "registro_cifras.json"), encoding="utf-8"))


def fnum(v, dec=0):
    """Formato es-AR: miles con punto, decimales con coma."""
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def val(clave):
    if clave not in REG:
        raise KeyError(f"cifra '{clave}' no esta en el registro")
    return REG[clave]["valor"]


def celda(clave, dec):
    return fnum(val(clave), dec) if clave in REG and REG[clave]["valor"] is not None else "sin dato"


def web(nombre, **kw):
    return pd.read_csv(os.path.join(WEB, nombre), **kw)


def limpio(v):
    return None if (v is None or (isinstance(v, float) and math.isnan(v))) else v


# ------------------------------------------------------------------ fragmentos con cifras del registro
rank = web("utilizacion_ductos_ranking.csv")


def lista_sobre_100():
    partes = []
    for i, r in rank[rank["sobre_100_pct"]].reset_index(drop=True).iterrows():
        extra = f"{int(r['meses_con_dato'])} meses" + ("; a revisar" if r["a_revisar_capacidad"] else "")
        partes.append(f"{r['denominacion_ducto'].strip()} ({int(r['anio'])}, {extra}) con {fnum(val(f'ducto_sobre100_{i + 1}_pct'), 1)}%")
    return "; ".join(partes)


def tabla(cabecera, filas):
    h = "".join(f"<th{' style=\"text-align:right\"' if i else ''}>{c}</th>" for i, c in enumerate(cabecera))
    b = "".join("<tr>" + "".join(f"<td{' class=\"num\"' if i else ''}>{c}</td>" for i, c in enumerate(f)) + "</tr>" for f in filas)
    return f'<table class="simple"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


def tabla_indices():
    filas = [[str(y), celda(f"idx_exp_{y}_base2022", 1), celda(f"idx_vm_{y}_base2022", 1), celda(f"idx_cuenca_{y}_base2022", 1)] for y in range(2022, 2026)]
    return tabla(["Año", "Exportación neuquina", "Producción Vaca Muerta", "Producción cuenca"], filas)


def tabla_sensibilidad():
    filas = [[f"Base {b}", celda(f"idx_exp_2025_base{b}", 1), celda(f"idx_vm_2025_base{b}", 1), celda(f"idx_cuenca_2025_base{b}", 1)] for b in (2021, 2022, 2023)]
    return tabla(["2025", "Exportación neuquina", "Producción Vaca Muerta", "Producción cuenca"], filas)


def tabla_pct():
    filas = [[str(y), celda(f"pct_exp_cuenca_{y}", 1) + "%", celda(f"pct_exp_vm_{y}", 1) + "%"] for y in range(2022, 2026)]
    return tabla(["Año", "De la cuenca", "De Vaca Muerta"], filas)


FRAGMENTOS = {"LISTA_SOBRE_100": lista_sobre_100, "TABLA_INDICES": tabla_indices, "TABLA_SENSIBILIDAD": tabla_sensibilidad,
              "TABLA_PCT_EXPORTADO": tabla_pct}
PAT = re.compile(r"\{\{([A-Za-z_0-9]+)(?::(\d))?\}\}")


def reemplazar(texto):
    def f(m):
        clave, dec = m.group(1), m.group(2)
        if clave in FRAGMENTOS:
            return FRAGMENTOS[clave]()
        return fnum(val(clave), int(dec or 0))
    return PAT.sub(f, texto)


# ------------------------------------------------------------------ DATA del HTML
def construir_data():
    ids_dud = set(web("pozos_coordenadas_dudosas.csv")["idpozo"])
    m = web("produccion_mapa.csv")
    m = m[~m["idpozo"].isin(ids_dud)]
    mapa = [[round(r.latitud, 5), round(r.longitud, 5), r.sub_tipo_recurso if isinstance(r.sub_tipo_recurso, str) else "N/D",
             r.areayacimiento, round(r.produccion_total_historica_bbl, 1)] for r in m.itertuples()]
    top = [{"r": int(r["rank"]), "n": r["areayacimiento"], "v": r["produccion_bbl_dia"]} for _, r in web("top_yacimientos.csv").iterrows()]
    pa = web("produccion_anual.csv")
    pv = pa.pivot_table(index="anio", columns="tipo_de_recurso", values="prod_pet_bbl", aggfunc="sum")
    prod_anual = [{"anio": int(y), "noconv": round(float(pv.loc[y, "NO CONVENCIONAL"]), 1),
                   "conv": (round(float(pv.loc[y, "CONVENCIONAL"]), 1) if y >= 2022 and pd.notna(pv.loc[y].get("CONVENCIONAL")) else None)}
                  for y in pv.index]
    c = web("comparacion_produccion_exportacion.csv")
    c = c.dropna(subset=["idx_produccion_vm_ma12_base2022"])
    ma12 = [{"m": r.fecha[:7], "vm": limpio(round(r.idx_produccion_vm_ma12_base2022, 2)),
             "cuenca": limpio(None if pd.isna(r.idx_produccion_cuenca_ma12_base2022) else round(r.idx_produccion_cuenca_ma12_base2022, 2)),
             "exp": limpio(None if pd.isna(r.idx_exportacion_terminales_ma12_base2022) else round(r.idx_exportacion_terminales_ma12_base2022, 2))}
            for r in c.itertuples()]
    util = [{"d": r.denominacion_ducto.strip(), "u": r.utilizacion_segmento_mas_cargado_pct, "a": int(r.anio), "m": int(r.meses_con_dato),
             "p": bool(r.parcial), "r": bool(r.a_revisar_capacidad)} for r in rank.head(20).itertuples()]
    cl = web("clasificacion_ductos_petroleo.csv")
    resp = cl[cl["categoria"] == "SIN_CAPACIDAD_EN_ANEXO_2A"].sort_values("volumen_petroleo_total_m3", ascending=False).head(18)
    ductos_resp = [{"d": r.denominacion_ducto.strip(), "v": r.volumen_petroleo_total_m3} for r in resp.itertuples()]
    ex = web("ductos_capacidad_dudosa.csv")
    excl = []
    for (i, d), g in ex.groupby(["idducto_logico", "denominacion_ducto"]):
        excl.append({"d": d.strip(), "a": ", ".join(str(int(a)) for a in sorted(g["anio"].unique())),
                     "m": ", ".join(sorted({x for s in g["motivo_capacidad_dudosa"].fillna("") for x in str(s).split(",") if x}))})
    pp = web("exportacion_nacional_por_pais_anual.csv")
    pp = pp[~pp["pais"].str.upper().isin(["NO IDENTIFICADO", "NO APLICA"])]   # el volumen sin pais se informa aparte
    tot = pp.groupby("pais")["volumen_m3"].sum().sort_values(ascending=False)
    paises_rank = [{"pais": p, "vol": round(float(v), 1)} for p, v in tot.head(10).items()]
    paises_rank.append({"pais": "Otros (" + str(len(tot) - 10) + " países)", "vol": round(float(tot.iloc[10:].sum()), 1)})
    anios = list(range(2019, 2026))
    top5 = list(tot.head(5).index)
    pais_series = {p: [round(float(pp[(pp.pais == p) & (pp.anio == y)]["volumen_m3"].sum()), 1) for y in anios] for p in top5}
    conc = web("concentracion_exportacion_2020_2025.csv")
    op = [{"e": r.nombre, "pct": r.pct} for r in conc[conc.nivel == "operador_terminal"].itertuples()]
    ca = [{"e": r.nombre, "pct": r.pct} for r in conc[conc.nivel == "cargador"].head(5).itertuples()]
    return {"mapa": mapa, "top_yac": top, "prod_anual": prod_anual, "ma12": ma12, "ductos_util": util, "ductos_resp": ductos_resp,
            "ductos_excl": excl, "paises_rank": paises_rank, "pais_years": anios, "pais_series": pais_series, "operadores": op, "cargadores": ca}


def escribir(ruta, texto):
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


def generar_html():
    css = (PLANT / "index_css.html").read_text(encoding="utf-8")
    cuerpo = (PLANT / "index_cuerpo.html").read_text(encoding="utf-8")
    js = (PLANT / "index_js_comun.js").read_text(encoding="utf-8") + (PLANT / "index_js_series.js").read_text(encoding="utf-8")
    data = json.dumps(construir_data(), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return css + reemplazar(cuerpo) + "<script>\nconst DATA = " + data + ";\n" + js + "</script>\n</body>\n</html>\n"


def render_html():
    doc = generar_html()
    escribir(REPO / "docs" / "index.html", doc)
    print("docs/index.html:", len(doc), "caracteres")


def generar_md(plantilla):
    p = PLANT / plantilla
    return reemplazar(p.read_text(encoding="utf-8")) if p.exists() else None


def render_md(plantilla, destino):
    txt = generar_md(plantilla)
    if txt is not None:
        escribir(REPO / destino, txt)
        print(destino, "generado")


if __name__ == "__main__":
    render_html()
    render_md("README.plantilla.md", "README.md")
    render_md("HANDOFF.plantilla.md", "HANDOFF_CHAT.md")
