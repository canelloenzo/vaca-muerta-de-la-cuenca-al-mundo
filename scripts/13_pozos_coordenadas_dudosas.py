"""
Pozos con coordenadas dudosas (F18).

Regla: distancia (km, haversine) del pozo a la mediana de las coordenadas de los pozos de su mismo yacimiento > UMBRAL_KM.
Justificacion del umbral (distribucion de los 3.062 pozos no convencionales con coordenada): mediana 4,5 km, P90 11,8 km,
P99 22,8 km, P99,9 28,2 km, maximo 47,3 km. Solo 2 pozos superan 30 km (ambos por encima de 41 km); 44 pozos estan entre
20 y 30 km, casi todos en yacimientos muy extensos (Loma Campana-LLL, 633 pozos). Los pozos marcados NO se borran de los datos:
solo se omiten del mapa publicado y se avisa con una nota al pie.

Entradas (CLEAN): dim_pozo_coordenadas_no_convencional.csv, fact_produccion_pozo_mes_vaca_muerta.csv
Salida   (WEB):   pozos_coordenadas_dudosas.csv
"""
import os

import numpy as np
import pandas as pd

from _rutas import CLEAN, WEB

UMBRAL_KM = 30.0


def haversine_km(lon1, lat1, lon2, lat2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


coords = pd.read_csv(os.path.join(CLEAN, "dim_pozo_coordenadas_no_convencional.csv"), encoding="utf-8-sig")
pozo = pd.read_csv(os.path.join(CLEAN, "fact_produccion_pozo_mes_vaca_muerta.csv"), encoding="utf-8-sig", low_memory=False,
                   usecols=["fecha", "idpozo", "sigla", "areayacimiento", "prod_pet_bbl"])
att = pozo.sort_values("fecha").groupby("idpozo").agg(sigla=("sigla", "last"), yacimiento=("areayacimiento", "last"),
                                                       produccion_acumulada_bbl=("prod_pet_bbl", "sum")).reset_index()
m = coords.merge(att, on="idpozo", how="inner").rename(columns={"coordenadax": "longitud", "coordenaday": "latitud"})
med = m.groupby("yacimiento").agg(med_lon=("longitud", "median"), med_lat=("latitud", "median"), pozos_con_coordenada=("idpozo", "size")).reset_index()
m = m.merge(med, on="yacimiento")
m["distancia_a_mediana_del_yacimiento_km"] = haversine_km(m["longitud"], m["latitud"], m["med_lon"], m["med_lat"]).round(1)
dud = m[m["distancia_a_mediana_del_yacimiento_km"] > UMBRAL_KM].copy()
dud["motivo"] = f"coordenada a mas de {UMBRAL_KM:.0f} km de la mediana de su yacimiento"
dud["produccion_acumulada_bbl"] = dud["produccion_acumulada_bbl"].round(0)
cols = ["idpozo", "sigla", "yacimiento", "longitud", "latitud", "med_lon", "med_lat", "pozos_con_coordenada",
        "distancia_a_mediana_del_yacimiento_km", "produccion_acumulada_bbl", "motivo"]
dud.sort_values("distancia_a_mediana_del_yacimiento_km", ascending=False)[cols].round(4).to_csv(
    os.path.join(WEB, "pozos_coordenadas_dudosas.csv"), index=False)
print(f"pozos con coordenada en produccion: {len(m)} | marcados (> {UMBRAL_KM:.0f} km): {len(dud)} | "
      f"produccion acumulada de los marcados: {dud['produccion_acumulada_bbl'].sum():,.0f} bbl "
      f"({100 * dud['produccion_acumulada_bbl'].sum() / m['produccion_acumulada_bbl'].sum():.3f}% del total)")
print(dud[["idpozo", "sigla", "yacimiento", "distancia_a_mediana_del_yacimiento_km"]].to_string(index=False))
