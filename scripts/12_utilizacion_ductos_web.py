"""
Tablas web de utilizacion de ductos (reemplazan a capacidad_ductos.csv, que sumaba gas y segmentos en serie).

Entradas (en CLEAN):  fact_capacidad_ductos.csv y fact_transporte_ductos.csv  (generados por los scripts 02 y 08)
Salidas (en data/web/):
  utilizacion_ductos_ranking.csv       ducto-anio mas reciente con capacidad NO dudosa; utilizacion = segmento mas cargado
                                       (solo liquidos) / capacidad operativa informada
  ductos_capacidad_dudosa.csv          ducto-anios excluidos del ranking, con el motivo. NO incluye utilizacion
  clasificacion_ductos_petroleo.csv    clasificacion explicita de los ductos que mueven petroleo
  resumen_ductos.json                  conteos para textos y pruebas

Definiciones (todas documentadas en documentacion/diccionario_datos.md):
  * "Ducto que mueve petroleo": ducto logico con volumen > 0 de `tipo_producto = Petroleo` en algun mes.
  * "Segmento mas cargado": para cada ducto-mes, el mayor volumen de liquidos entre sus segmentos nodo_origen -> nodo_destino.
    No es una cota: es el volumen del tramo mas exigido; coincide con la utilizacion real solo si la capacidad informada
    corresponde a ese tramo (el Anexo 2A y la planilla 20 no comparten identificador de tramo).
  * Capacidad dudosa: ver reglas R1-R5 y D2 en 08_clean_capacidad_ductos.py. R2 solo marca "a revisar".
  * "Parcial": el ducto-anio tiene menos de 12 meses con transporte.
"""
import json
import os

import numpy as np
import pandas as pd

from _rutas import CLEAN, WEB

cap = pd.read_csv(os.path.join(CLEAN, "fact_capacidad_ductos.csv"), encoding="utf-8-sig", low_memory=False)
tr = pd.read_csv(os.path.join(CLEAN, "fact_transporte_ductos.csv"), encoding="utf-8-sig", low_memory=False)
ALIAS = dict(zip(tr["idducto"], tr["idducto_logico"]))
den_logica = tr.drop_duplicates("idducto_logico").set_index("idducto_logico")["denominacion_logica"]

# ------------------------------------------------------------------ universo: ductos logicos que mueven petroleo
pet = tr[(tr["tipo_producto"] == "Petroleo") & (tr["volumen"] > 0)]
pet_ids = sorted(pet["idducto_logico"].unique())
vol_pet = pet.groupby("idducto_logico")["volumen"].sum()
anios_tr = tr[tr["volumen"] > 0].groupby("idducto_logico")["anio"].agg(["min", "max"])

# ------------------------------------------------------------------ ducto-anio con capacidad
cap["idducto_logico"] = cap["idducto_logico"].astype(int)
ya = (cap[cap["capacidad_valida"]]
      .groupby(["idducto_logico", "idducto", "anio"])
      .apply(lambda d: pd.Series({
          "meses_con_dato": len(d),
          "cap_op": d["capacidad_operativa_maxima_m3_dia"].iloc[0], "cap_dis": d["capacidad_disenio_m3_dia"].iloc[0],
          "cap_emp": d["capacidad_empleada_m3_dia"].iloc[0],
          "util_segmax": d["volumen_segmento_mas_cargado"].sum() / d["capacidad_mensual_m3"].sum(),
          "util_liq": d["volumen_liquidos"].sum() / d["capacidad_mensual_m3"].sum(),
          "n_seg_max": d["n_segmentos_con_volumen"].max(),
          "dudosa": bool(d["capacidad_dudosa"].iloc[0]), "a_revisar": bool(d["a_revisar_capacidad"].iloc[0]),
          "motivo": d["motivo_capacidad_dudosa"].fillna("").iloc[0]}), include_groups=False)
      .reset_index())
ya["denominacion"] = ya["idducto_logico"].map(den_logica)

# ------------------------------------------------------------------ ranking (ductos de petroleo, ultimo anio no dudoso)
buenos = ya[(~ya["dudosa"]) & (ya["idducto_logico"].isin(pet_ids))]
ult = buenos.sort_values("anio").groupby("idducto_logico").tail(1).sort_values("util_segmax", ascending=False)
rank = pd.DataFrame({
    "idducto_logico": ult["idducto_logico"], "denominacion_ducto": ult["denominacion"], "anio": ult["anio"].astype(int),
    "meses_con_dato": ult["meses_con_dato"].astype(int), "parcial": ult["meses_con_dato"] < 12,
    "utilizacion_segmento_mas_cargado_pct": (100 * ult["util_segmax"]).round(1),
    "utilizacion_liquidos_total_pct": (100 * ult["util_liq"]).round(1),
    "multi_segmento": ult["n_seg_max"] > 1, "a_revisar_capacidad": ult["a_revisar"],
    "capacidad_operativa_m3_dia": ult["cap_op"], "capacidad_disenio_m3_dia": ult["cap_dis"],
    "capacidad_empleada_m3_dia": ult["cap_emp"],
    "sobre_100_pct": 100 * ult["util_segmax"] > 100}).reset_index(drop=True)
rank.insert(0, "posicion", np.arange(1, len(rank) + 1))
rank.to_csv(os.path.join(WEB, "utilizacion_ductos_ranking.csv"), index=False)

# ------------------------------------------------------------------ ducto-anios dudosos (sin utilizacion)
dud = ya[ya["dudosa"]].copy()
dud["mueve_petroleo"] = dud["idducto_logico"].isin(pet_ids)
dud_out = dud[["idducto_logico", "idducto", "denominacion", "anio", "motivo", "cap_op", "cap_dis", "cap_emp", "mueve_petroleo"]].rename(
    columns={"denominacion": "denominacion_ducto", "motivo": "motivo_capacidad_dudosa", "cap_op": "capacidad_operativa_m3_dia",
             "cap_dis": "capacidad_disenio_m3_dia", "cap_emp": "capacidad_empleada_m3_dia"}).sort_values(["idducto_logico", "anio"])
dud_out.to_csv(os.path.join(WEB, "ductos_capacidad_dudosa.csv"), index=False)

# ------------------------------------------------------------------ clasificacion de los ductos que mueven petroleo
con_cap_any = set(cap["idducto_logico"])                         # ducto con alguna fila en fact_capacidad
rows = []
for i in pet_ids:
    y = ya[ya["idducto_logico"] == i]
    buenos_i = y[~y["dudosa"]]
    cap_cero = cap[(cap["idducto_logico"] == i) & (~cap["capacidad_valida"])]
    if len(buenos_i):
        cat = "EN_RANKING"
    elif len(y):
        cat = "CAPACIDAD_DUDOSA_TODOS_LOS_ANIOS"
    elif len(cap_cero):
        cat = "CAPACIDAD_INFORMADA_EN_CERO"
    else:
        cat = "SIN_CAPACIDAD_EN_ANEXO_2A"
    rows.append(dict(idducto_logico=i, denominacion_ducto=den_logica[i], categoria=cat,
                     anios_con_capacidad_no_dudosa=",".join(map(str, buenos_i["anio"].astype(int))),
                     anios_con_capacidad_dudosa=",".join(map(str, y[y["dudosa"]]["anio"].astype(int))),
                     primer_anio_transporte=int(anios_tr.loc[i, "min"]), ultimo_anio_transporte=int(anios_tr.loc[i, "max"]),
                     volumen_petroleo_total_m3=round(vol_pet.loc[i], 1),
                     idducto_originales=",".join(map(str, sorted(k for k, v in ALIAS.items() if v == i)))))
clasif = pd.DataFrame(rows)
clasif.to_csv(os.path.join(WEB, "clasificacion_ductos_petroleo.csv"), index=False)

# ------------------------------------------------------------------ petroleo transportado por ducto logico y anio (dato directo, sin capacidad)
# Un ducto con varios segmentos en serie cuenta dos veces el mismo barril si se suman todos los tramos (p. ej. VMOC). Por eso la medida publicada
# es el volumen del TRAMO MAS CARGADO de cada mes (suma de los 12 meses); la suma de todos los tramos se conserva en otra columna.
# se incluyen los volumenes negativos (rectificaciones): el volumen es neto
pet_neto = tr[tr["tipo_producto"] == "Petroleo"]
seg_m = (pet_neto.groupby(["idducto_logico", "anio", "mes", "nodo_origen", "nodo_destino"], dropna=False)["volumen"].sum().reset_index())
tramo_max = seg_m.groupby(["idducto_logico", "anio", "mes"])["volumen"].max().reset_index()
vol = (tramo_max.groupby(["idducto_logico", "anio"]).agg(volumen_tramo_mas_cargado_m3=("volumen", "sum"), meses_con_dato=("mes", "nunique")).reset_index())
vol = vol.merge(pet_neto.groupby(["idducto_logico", "anio"])["volumen"].sum().rename("volumen_suma_de_tramos_m3").reset_index(), on=["idducto_logico", "anio"])
vol["denominacion_ducto"] = vol["idducto_logico"].map(den_logica)
vol = vol[["idducto_logico", "denominacion_ducto", "anio", "meses_con_dato", "volumen_tramo_mas_cargado_m3", "volumen_suma_de_tramos_m3"]].round(1)
vol.to_csv(os.path.join(WEB, "volumen_petroleo_ductos_anual.csv"), index=False)

resumen = {
    "ductos_logicos_que_mueven_petroleo": len(pet_ids),
    "categorias": clasif["categoria"].value_counts().to_dict(),
    "ranking_n_ductos": int(len(rank)), "ranking_sobre_100": int(rank["sobre_100_pct"].sum()),
    "ranking_con_anio_parcial": int(rank["parcial"].sum()), "ranking_multi_segmento": int(rank["multi_segmento"].sum()),
    "ranking_a_revisar": int(rank["a_revisar_capacidad"].sum()),
    "duct_anios_con_capacidad_dudosa": int(len(dud_out)), "ductos_con_algun_anio_dudoso": int(dud_out["idducto_logico"].nunique()),
    "reglas": {"R1_umbral_veces": float(os.environ.get("VM_R1_UMBRAL", 5)), "R3_umbral_veces": float(os.environ.get("VM_R3_UMBRAL", 2)),
               "R5_dias": int(os.environ.get("VM_R5_DIAS", 90))},
}
with open(os.path.join(WEB, "resumen_ductos.json"), "w", encoding="utf-8") as f:
    json.dump(resumen, f, ensure_ascii=False, indent=2)
print(json.dumps(resumen, ensure_ascii=False, indent=2))
