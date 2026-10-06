"""
Genera las tablas livianas para la version web del dashboard (data/web/), replicando EXACTAMENTE la
logica de calculo ya validada en powerbi/dax_measures.md -- no se recalcula con supuestos distintos.

Mapeo medida DAX -> logica Python:
  - "Prod Petroleo (bbl-dia)"        -> SUM(prod_pet_bbl) / SUMX(VALUES(fecha), AVERAGE(dias_mes))
                                         (a nivel de un solo mes, dias_mes de ese mes; para un yacimiento
                                         puntual no hay riesgo de doble conteo porque hay 1 fila por
                                         yacimiento-mes)
  - "Indice Produccion/Exportacion (base 100)" -> base = promedio de los 12 valores mensuales de 2019
                                         (equivalente al fix ALL(Dim_Fecha)+anio=2019: la base es una
                                         constante fija, no depende del mes que se este mirando)
  - "Utilizacion %"                  -> SUM(volumen_transportado)/SUM(capacidad_mensual_m3), con
                                         capacidad_valida=True y excluyendo idducto sospechosos
  - "Volumen Transportado (respaldo)"-> SUM(Fact_TransporteDuctos.volumen) con tipo_producto="Petroleo"
  - "Volumen Exportado"              -> SUM(volumen) con tipo_operacion="Exportacion"

Se corren validaciones contra numeros ya confirmados en el chat (94.2% de concentracion en 3 empresas,
76.8%/5.2% de volatilidad) ANTES de escribir los archivos finales.
"""
import os
import json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(ROOT, "clean")
WEB = os.path.join(ROOT, "data", "web")
os.makedirs(WEB, exist_ok=True)

DUCTOS_SOSPECHOSOS = {42, 97, 149, 171, 221, 329}

# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------
prod_yac = pd.read_csv(f"{CLEAN}/fact_produccion_yacimiento_mes_vaca_muerta.csv", encoding="utf-8-sig")
prod_yac["fecha"] = pd.to_datetime(prod_yac["fecha"])

prod_pozo = pd.read_csv(f"{CLEAN}/fact_produccion_pozo_mes_vaca_muerta.csv", encoding="utf-8-sig")
prod_pozo["fecha"] = pd.to_datetime(prod_pozo["fecha"])

coords = pd.read_csv(f"{CLEAN}/dim_pozo_coordenadas_no_convencional.csv", encoding="utf-8-sig")

exp = pd.read_csv(f"{CLEAN}/fact_movimientos_exportacion_ductos.csv", encoding="utf-8-sig")
exp["fecha"] = pd.to_datetime(exp["fecha"])

cap = pd.read_csv(f"{CLEAN}/fact_capacidad_ductos.csv", encoding="utf-8-sig")
cap["fecha"] = pd.to_datetime(cap["fecha"])

transp = pd.read_csv(f"{CLEAN}/fact_transporte_ductos.csv", encoding="utf-8-sig")
transp["fecha"] = pd.to_datetime(transp["fecha"])


def prod_bbl_dia(df):
    """Replica SUM(prod_pet_bbl) / SUMX(VALUES(fecha), AVERAGE(dias_mes))."""
    por_mes = df.groupby("fecha").agg(bbl=("prod_pet_bbl", "sum"), dias=("dias_mes", "mean"))
    num = por_mes["bbl"].sum()
    den = por_mes["dias"].sum()
    return num / den if den else np.nan


def monthly_bbl_dia_series(df):
    """Serie mensual de bbl/dia -- un valor por fecha, sin ambiguedad de agrupamiento anidado."""
    por_mes = df.groupby("fecha").agg(bbl=("prod_pet_bbl", "sum"), dias=("dias_mes", "mean"))
    return (por_mes["bbl"] / por_mes["dias"]).sort_index()


def volumen_exportado(df):
    return df.loc[df["tipo_operacion"] == "Exportacion", "volumen"].sum()


# ---------------------------------------------------------------------------
# 1. resumen_kpis.json
# ---------------------------------------------------------------------------
ultimo_mes_prod = prod_yac["fecha"].max()
mismo_mes_anio_anterior = ultimo_mes_prod - pd.DateOffset(years=1)

df_ultimo = prod_yac[prod_yac["fecha"] == ultimo_mes_prod]
df_anterior = prod_yac[prod_yac["fecha"] == mismo_mes_anio_anterior]

bbl_dia_ultimo = prod_bbl_dia(df_ultimo)
bbl_dia_anterior = prod_bbl_dia(df_anterior)
var_interanual = (bbl_dia_ultimo - bbl_dia_anterior) / bbl_dia_anterior

pct_no_conv_historico = (
    prod_yac.loc[prod_yac["tipo_de_recurso"] == "NO CONVENCIONAL", "prod_pet_bbl"].sum()
    / prod_yac["prod_pet_bbl"].sum()
)

exp_filtrado = exp[exp["tipo_operacion"] == "Exportacion"]
ultimo_mes_exp = exp_filtrado["fecha"].max()
vol_exportado_ultimo_mes = volumen_exportado(exp[exp["fecha"] == ultimo_mes_exp])

# Volatilidad 2020-2025 (ya verificada en el chat: ~76.8% vs ~5.2%)
exp_2020_2025 = exp[(exp["tipo_operacion"] == "Exportacion") & (exp["anio"].between(2020, 2025))]
prod_2020_2025 = prod_yac[prod_yac["anio"].between(2020, 2025)]

vol_mensual_exp = exp_2020_2025.groupby("fecha")["volumen"].sum().sort_index()
vol_mensual_prod = monthly_bbl_dia_series(prod_2020_2025)

std_exp = vol_mensual_exp.pct_change().dropna().std() * 100
std_prod = vol_mensual_prod.pct_change().dropna().std() * 100

# Concentracion por empresa 2020-2025 (ya verificada: ~94.2% top 3)
por_empresa = exp_2020_2025.groupby("empresa")["volumen"].sum().sort_values(ascending=False)
top3_pct = por_empresa.head(3).sum() / por_empresa.sum() * 100

print("=== VALIDACION resumen_kpis ===")
print(f"Ultimo mes produccion: {ultimo_mes_prod.date()}  bbl/dia={bbl_dia_ultimo:,.1f}")
print(f"Mismo mes anio anterior: {mismo_mes_anio_anterior.date()}  bbl/dia={bbl_dia_anterior:,.1f}")
print(f"Variacion interanual: {var_interanual*100:.2f}%")
print(f"% No Convencional (historico, base bbl): {pct_no_conv_historico*100:.2f}%  (referencia hipotetica del usuario: 99.8%)")
print(f"Ultimo mes exportacion: {ultimo_mes_exp.date()}  volumen={vol_exportado_ultimo_mes:,.1f} m3")
print(f"Std var mensual exportacion 2020-2025: {std_exp:.2f}%  (ya validado: ~76.8%)")
print(f"Std var mensual produccion 2020-2025: {std_prod:.2f}%  (ya validado: ~5.2%)")
print(f"Concentracion top3 empresas 2020-2025: {top3_pct:.2f}%  (ya validado: ~94.2%)")

kpis = {
    "fecha_ultimo_mes_produccion": ultimo_mes_prod.strftime("%Y-%m-%d"),
    "produccion_ultimo_mes_bbl_dia": round(bbl_dia_ultimo, 1),
    "variacion_interanual_produccion_pct": round(var_interanual * 100, 2),
    "pct_no_convencional_historico": round(pct_no_conv_historico * 100, 2),
    "fecha_ultimo_mes_exportacion": ultimo_mes_exp.strftime("%Y-%m-%d"),
    "volumen_exportado_ultimo_mes_m3": round(vol_exportado_ultimo_mes, 1),
    "volatilidad_std_var_mensual_exportacion_pct_2020_2025": round(std_exp, 2),
    "volatilidad_std_var_mensual_produccion_pct_2020_2025": round(std_prod, 2),
    "concentracion_top3_empresas_pct_2020_2025": round(top3_pct, 2),
}
with open(f"{WEB}/resumen_kpis.json", "w", encoding="utf-8") as f:
    json.dump(kpis, f, ensure_ascii=False, indent=2)

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
# 4. indices_mensuales.csv
# ---------------------------------------------------------------------------
serie_prod = monthly_bbl_dia_series(prod_yac)
serie_exp = exp_filtrado.groupby("fecha")["volumen"].sum().sort_index()

base_prod_2019 = serie_prod[serie_prod.index.year == 2019]
base_exp_2019 = serie_exp[serie_exp.index.year == 2019]
assert len(base_prod_2019) == 12, f"esperaba 12 meses de produccion en 2019, hay {len(base_prod_2019)}"
assert len(base_exp_2019) == 12, f"esperaba 12 meses de exportacion en 2019, hay {len(base_exp_2019)}"
base_prod = base_prod_2019.mean()
base_exp = base_exp_2019.mean()
print(f"\nBase indice produccion (promedio 2019): {base_prod:,.1f} bbl/dia")
print(f"Base indice exportacion (promedio 2019): {base_exp:,.1f} m3")

fecha_max = max(serie_prod.index.max(), serie_exp.index.max())
rango = pd.date_range("2018-01-01", fecha_max, freq="MS")
idx = pd.DataFrame({"fecha": rango})
idx["indice_produccion"] = idx["fecha"].map(serie_prod) / base_prod * 100
idx["indice_exportacion"] = idx["fecha"].map(serie_exp) / base_exp * 100
idx["anio_mes"] = idx["fecha"].dt.strftime("%Y-%m")
idx = idx[["anio_mes", "indice_produccion", "indice_exportacion"]].round(2)
idx.to_csv(f"{WEB}/indices_mensuales.csv", index=False)
print(f"indices_mensuales.csv: {len(idx)} meses ({idx['anio_mes'].iloc[0]} a {idx['anio_mes'].iloc[-1]})")

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

# ---------------------------------------------------------------------------
# 6. exportacion_por_pais_anual.csv
# ---------------------------------------------------------------------------
exp_pais = exp_filtrado[exp_filtrado["pais"].notna() & (exp_filtrado["pais"] != "")]
por_pais = exp_pais.groupby(["anio", "pais"])["volumen"].sum().reset_index()
por_pais.columns = ["anio", "pais", "volumen_m3"]
por_pais.to_csv(f"{WEB}/exportacion_por_pais_anual.csv", index=False)
print(f"exportacion_por_pais_anual.csv: {len(por_pais)} filas, {por_pais['pais'].nunique()} paises")

# ---------------------------------------------------------------------------
# 7. exportacion_por_empresa.csv (concentracion 2020-2025, ya validada)
# ---------------------------------------------------------------------------
total_empresas = por_empresa.sum()
top3_empresas = por_empresa.head(3)
otras_vol = por_empresa.iloc[3:].sum()

filas_empresa = [
    {"empresa": emp, "volumen_2020_2025_m3": round(vol, 1), "porcentaje_del_total": round(vol / total_empresas * 100, 2)}
    for emp, vol in top3_empresas.items()
]
filas_empresa.append({
    "empresa": "Otras",
    "volumen_2020_2025_m3": round(otras_vol, 1),
    "porcentaje_del_total": round(otras_vol / total_empresas * 100, 2),
})
exportacion_por_empresa = pd.DataFrame(filas_empresa)
exportacion_por_empresa.to_csv(f"{WEB}/exportacion_por_empresa.csv", index=False)
print(f"exportacion_por_empresa.csv: {len(exportacion_por_empresa)} filas, suma % = {exportacion_por_empresa['porcentaje_del_total'].sum():.2f}%")

# ---------------------------------------------------------------------------
# 8. capacidad_ductos.csv
# ---------------------------------------------------------------------------
cap_sin_sospechosos = cap[~cap["idducto"].isin(DUCTOS_SOSPECHOSOS)]
cap_validos = cap_sin_sospechosos[cap_sin_sospechosos["capacidad_valida"] == True]  # noqa: E712

por_ducto_anio_valido = cap_validos.groupby(["idducto", "denominacion_ducto", "anio"]).agg(
    volumen=("volumen_transportado", "sum"), capacidad=("capacidad_mensual_m3", "sum")
).reset_index()
por_ducto_anio_valido["utilizacion_pct"] = por_ducto_anio_valido["volumen"] / por_ducto_anio_valido["capacidad"] * 100

cubiertos = set(zip(por_ducto_anio_valido["idducto"], por_ducto_anio_valido["anio"]))

transp_petroleo = transp[transp["tipo_producto"] == "Petroleo"]
por_ducto_anio_transp = transp_petroleo.groupby(["idducto", "denominacion_ducto", "anio"])["volumen"].sum().reset_index()
por_ducto_anio_transp["cubierto"] = list(
    zip(por_ducto_anio_transp["idducto"], por_ducto_anio_transp["anio"])
)
por_ducto_anio_transp["cubierto"] = por_ducto_anio_transp["cubierto"].isin(cubiertos)

respaldo = por_ducto_anio_transp[~por_ducto_anio_transp["cubierto"]].rename(columns={"volumen": "volumen_transportado_respaldo"})

tabla_valida = por_ducto_anio_valido[["denominacion_ducto", "anio", "utilizacion_pct"]].copy()
tabla_valida["volumen_transportado_respaldo"] = np.nan
tabla_respaldo = respaldo[["denominacion_ducto", "anio", "volumen_transportado_respaldo"]].copy()
tabla_respaldo["utilizacion_pct"] = np.nan

capacidad_ductos = pd.concat([tabla_valida, tabla_respaldo], ignore_index=True)
capacidad_ductos = capacidad_ductos[["denominacion_ducto", "anio", "utilizacion_pct", "volumen_transportado_respaldo"]]
capacidad_ductos = capacidad_ductos.round({"utilizacion_pct": 2, "volumen_transportado_respaldo": 1})
capacidad_ductos.to_csv(f"{WEB}/capacidad_ductos.csv", index=False)
print(f"capacidad_ductos.csv: {len(capacidad_ductos)} filas ({len(tabla_valida)} con utilizacion valida, {len(tabla_respaldo)} respaldo)")

# ---------------------------------------------------------------------------
# Tamano total
# ---------------------------------------------------------------------------
print("\n=== TAMANO DE ARCHIVOS ===")
total_bytes = 0
for fname in sorted(os.listdir(WEB)):
    path = os.path.join(WEB, fname)
    size = os.path.getsize(path)
    total_bytes += size
    print(f"{fname}: {size/1024:.1f} KB")
print(f"TOTAL: {total_bytes/1024:.1f} KB ({total_bytes/1024/1024:.3f} MB)")
