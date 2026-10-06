"""
Tablas de produccion para la version web (data/web/): produccion_mapa.csv, produccion_anual.csv y top_yacimientos.csv.

Las series de exportacion, ductos, indices y KPIs las generan los scripts 11 (cuenca neuquina, exportacion, indices, KPIs)
y 12 (utilizacion de ductos). Hasta la auditoria de 2026-10-05 este script tambien generaba resumen_kpis.json,
indices_mensuales.csv (base 2019), exportacion_por_pais_anual.csv, exportacion_por_empresa.csv y capacidad_ductos.csv;
se retiraron porque mezclaban alcances (ver CHANGELOG_CORRECCIONES.md). Siguen en el historial de git.

  - Produccion en bbl/dia -> SUM(prod_pet_bbl) / SUMX(VALUES(fecha), AVERAGE(dias_mes)) (dias del mes una sola vez)
"""
import pandas as pd

from _rutas import RAW, CLEAN, WEB  # noqa: F401  (rutas configurables, ver _rutas.py)

prod_yac = pd.read_csv(f"{CLEAN}/fact_produccion_yacimiento_mes_vaca_muerta.csv", encoding="utf-8-sig")
prod_yac["fecha"] = pd.to_datetime(prod_yac["fecha"])
prod_pozo = pd.read_csv(f"{CLEAN}/fact_produccion_pozo_mes_vaca_muerta.csv", encoding="utf-8-sig")
prod_pozo["fecha"] = pd.to_datetime(prod_pozo["fecha"])
coords = pd.read_csv(f"{CLEAN}/dim_pozo_coordenadas_no_convencional.csv", encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# 2. produccion_mapa.csv (solo pozos no convencionales, que tienen coordenadas)
# ---------------------------------------------------------------------------
total_por_pozo = prod_pozo.groupby("idpozo")["prod_pet_bbl"].sum().rename("produccion_total_historica_bbl")
sub_tipo_por_pozo = prod_pozo.groupby("idpozo")["sub_tipo_recurso"].first()
area_reciente_por_pozo = prod_pozo.sort_values("fecha").groupby("idpozo")["areayacimiento"].last()

mapa = pd.concat([total_por_pozo, sub_tipo_por_pozo, area_reciente_por_pozo], axis=1).reset_index()
mapa = mapa.merge(coords, on="idpozo", how="inner")
mapa = mapa.rename(columns={"coordenaday": "latitud", "coordenadax": "longitud"})
mapa = mapa[["idpozo", "latitud", "longitud", "sub_tipo_recurso", "areayacimiento", "produccion_total_historica_bbl"]]
mapa.to_csv(f"{WEB}/produccion_mapa.csv", index=False)
print(f"\nproduccion_mapa.csv: {len(mapa)} pozos (de {prod_pozo['idpozo'].nunique()} pozos totales en Fact_Produccion_Pozo)")

# ---------------------------------------------------------------------------
# 3. produccion_anual.csv
# ---------------------------------------------------------------------------
anual = prod_yac.groupby(["anio", "tipo_de_recurso"])["prod_pet_bbl"].sum().reset_index()
anual.to_csv(f"{WEB}/produccion_anual.csv", index=False)
print(f"produccion_anual.csv: {len(anual)} filas")

# ---------------------------------------------------------------------------
# 5. top_yacimientos.csv
# ---------------------------------------------------------------------------

# fact_produccion_yacimiento_mes tiene grano yacimiento-provincia-cuenca-tipo_de_recurso-sub_tipo_recurso-mes,
# NO yacimiento-mes -- 23 de los 146 yacimientos tienen mas de 1 fila en el mismo mes (conviven pozos
# CONVENCIONAL y NO CONVENCIONAL en el mismo yacimiento). Sumar dias_mes directo por yacimiento cuenta esos
# meses varias veces e infla el denominador -- hay que deduplicar por (areayacimiento, fecha) primero, igual
# que hace SUMX(VALUES(fecha), ...) en la medida DAX para el total agregado.
por_yac_mes = prod_yac.groupby(["areayacimiento", "fecha"]).agg(
    bbl=("prod_pet_bbl", "sum"), dias=("dias_mes", "mean")
).reset_index()
por_yac = por_yac_mes.groupby("areayacimiento").agg(bbl=("bbl", "sum"), dias=("dias", "sum")).reset_index()
por_yac["produccion_bbl_dia"] = por_yac["bbl"] / por_yac["dias"]
por_yac = por_yac.sort_values("produccion_bbl_dia", ascending=False).reset_index(drop=True)
por_yac["rank"] = por_yac.index + 1
top_yac = por_yac[["areayacimiento", "produccion_bbl_dia", "rank"]].round({"produccion_bbl_dia": 1})
top_yac.to_csv(f"{WEB}/top_yacimientos.csv", index=False)
print(f"top_yacimientos.csv: {len(top_yac)} yacimientos")
