"""
Registro de cifras: UNICA fuente de los numeros que aparecen en README.md, docs/index.html y HANDOFF_CHAT.md.

Lee solo las tablas ya publicadas en data/web/ (generadas por los scripts 10-13) y, para la cobertura de capacidad,
las tablas limpias. Escribe data/web/registro_cifras.json con, para cada cifra: valor, unidad y alcance.
Ningun texto lleva numeros escritos a mano: `15_render_textos.py` los toma de aca y una prueba compara cada texto
contra este registro.
"""
import json
import os

import numpy as np
import pandas as pd

from _rutas import CLEAN, WEB

R = {}


def reg(clave, valor, unidad, alcance):
    if isinstance(valor, (np.integer,)):
        valor = int(valor)
    elif isinstance(valor, (np.floating,)):
        valor = float(valor)
    R[clave] = {"valor": valor, "unidad": unidad, "alcance": alcance}


def leer(nombre, **kw):
    return pd.read_csv(os.path.join(WEB, nombre), **kw)


k = json.load(open(os.path.join(WEB, "kpis_resumen.json"), encoding="utf-8"))
an = leer("comparacion_anual.csv").set_index("anio")
mens = leer("comparacion_produccion_exportacion.csv")
mens["fecha"] = pd.to_datetime(mens["fecha"])
mens = mens.set_index("fecha")
sens = leer("indices_sensibilidad.csv")
pa = leer("produccion_anual.csv")
mapa = leer("produccion_mapa.csv")
dud = leer("pozos_coordenadas_dudosas.csv")
rank = leer("utilizacion_ductos_ranking.csv")
clasif = leer("clasificacion_ductos_petroleo.csv")
excl = leer("ductos_capacidad_dudosa.csv")
rd = json.load(open(os.path.join(WEB, "resumen_ductos.json"), encoding="utf-8"))
term = leer("exportacion_nacional_por_terminal_anual.csv")
conc = leer("concentracion_exportacion_2020_2025.csv")
top = leer("top_yacimientos.csv")

ALC_NC = "solo no convencional (el convencional de 2026 no esta en las fuentes cargadas)"
ALC_TERM = "crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile"
ALC_CUENCA = "produccion total de petroleo de la cuenca Neuquina, solo 2022-2025 (archivos anuales + no convencional historico)"

# ------------------------------------------------------------------ produccion
reg("prod_ultimo_mes_bbl_dia", k["produccion_ultimo_mes_bbl_dia"], "bbl/dia", f"jun-2026, {ALC_NC}")
reg("prod_var_interanual_pct", k["variacion_interanual_produccion_pct"], "%", "jun-2026 vs jun-2025, ambos solo no convencional")
reg("prod_vm_dic2025_bbl_dia", k["produccion_vm_dic_2025_bbl_dia"], "bbl/dia", "dic-2025, Vaca Muerta convencional + no convencional")
reg("prod_var_dic2025_pct", k["variacion_interanual_vm_dic_2025_pct"], "%", "dic-2025 vs dic-2024, Vaca Muerta")
reg("pct_nc_2022_2025", k["pct_no_convencional_2022_2025"], "%", "volumen de petroleo de Vaca Muerta 2022-2025 (unico periodo con convencional observable)")
reg("prod_acum_2006_2025_bbl", pa["prod_pet_bbl"].sum(), "bbl", "Vaca Muerta, 2006-2025, fuentes cargadas")
reg("yacimientos_n", len(top), "yacimientos", "Vaca Muerta, fuentes cargadas")
reg("yac_top1_bbl_dia", top.iloc[0]["produccion_bbl_dia"], "bbl/dia", f"{top.iloc[0]['areayacimiento']}, promedio de los meses con dato del yacimiento")
conv = pa[pa["tipo_de_recurso"] == "CONVENCIONAL"].set_index("anio")["prod_pet_bbl"]
tot = pa.groupby("anio")["prod_pet_bbl"].sum()
pct_conv = (100 * conv / tot.loc[conv.index])
reg("pct_conv_min_2022_2025", pct_conv.min(), "%", "convencional / total de Vaca Muerta, anual 2022-2025")
reg("pct_conv_max_2022_2025", pct_conv.max(), "%", "convencional / total de Vaca Muerta, anual 2022-2025")
reg("conv_2022_bbl", conv.loc[2022], "bbl", "produccion convencional de Vaca Muerta, 2022")
reg("pozos_nc_con_coordenadas", len(mapa), "pozos", "pozos no convencionales con coordenadas en la fuente")
ids_dud = set(dud["idpozo"])
reg("pozos_mapa_omitidos", len(dud), "pozos", "coordenada a mas de 30 km de la mediana de su yacimiento")
reg("pozos_mapa", int((~mapa["idpozo"].isin(ids_dud)).sum()), "pozos", "pozos dibujados en el mapa")
reg("pozos_omitidos_pct_prod", 100 * dud["produccion_acumulada_bbl"].sum() / pa["prod_pet_bbl"].sum(), "%", "produccion acumulada de los pozos omitidos / total")

# ------------------------------------------------------------------ serie principal: comercio exterior (script 16) y produccion oficial de la cuenca
ca = leer("comex_anual.csv").set_index("anio")
cm = leer("comex_comparacion_mensual.csv")
cm["fecha"] = pd.to_datetime(cm["fecha"])
cm = cm.set_index("fecha")
cmx = json.load(open(os.path.join(WEB, "comex_meta.json"), encoding="utf-8"))
cpais = leer("comex_neuquina_por_pais_anual.csv")
cconc = leer("comex_neuquina_concentracion_2020_2025.csv")
cval = leer("comex_validacion_precios.csv")
ALC_COMEX = "crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional"
ALC_CUENCA = "produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias)"

for y in range(2020, 2026):
    reg(f"prod_cuenca_{y}_bbl_dia", ca.loc[y, "prod_cuenca_bbl_dia"], "bbl/dia", f"{y}, {ALC_CUENCA}")
    reg(f"exp_{y}_bbl_dia", ca.loc[y, "exportacion_bbl_dia"], "bbl/dia", f"{y}, promedio diario del anio, {ALC_COMEX}")
    reg(f"exp_{y}_m3", ca.loc[y, "exportacion_m3"], "m3", f"{y}, {ALC_COMEX}")
    reg(f"exp_{y}_usd_millones", ca.loc[y, "exportacion_usd"] / 1e6, "millones de USD", f"{y}, monto FOB declarado, {ALC_COMEX}")
    reg(f"exp_{y}_usd_bbl", ca.loc[y, "usd_por_bbl"], "USD/bbl", f"{y}, monto declarado / volumen, {ALC_COMEX}")
    reg(f"exp_{y}_meses", int(ca.loc[y, "meses_con_exportacion"]), "meses", f"{y}: meses con exportacion declarada de crudo de la cuenca Neuquina")
    reg(f"pct_exp_cuenca_{y}", ca.loc[y, "pct_exportado_cuenca"], "%", f"{y}: exportacion de crudo de la cuenca (comercio exterior) / {ALC_CUENCA}")
    reg(f"chile_pct_exp_{y}", ca.loc[y, "chile_pct_de_exportacion"], "%", f"{y}: parte de la exportacion declarada con destino Chile")
for y in range(2022, 2026):
    reg(f"prod_vm_{y}_bbl_dia", ca.loc[y, "prod_vm_bbl_dia"], "bbl/dia", f"{y}, Vaca Muerta (por pozo)")
    reg(f"vm_sobre_cuenca_{y}", 100 * ca.loc[y, "prod_vm_bbl_dia"] / ca.loc[y, "prod_cuenca_bbl_dia"], "%", f"{y}: Vaca Muerta (por pozo) / cuenca Neuquina (serie oficial)")
for y in range(2022, 2026):
    for b in (2021, 2022, 2023):
        for serie, col, desc in (("exp", "idx_exportacion", "exportacion de crudo de la cuenca (comercio exterior)"), ("vm", "idx_produccion_vm", "produccion de Vaca Muerta"),
                                 ("cuenca", "idx_produccion_cuenca", "produccion de la cuenca")):
            reg(f"idx_{serie}_{y}_base{b}", ca.loc[y, f"{col}_base{b}"], "indice", f"promedio anual {y}, base {b} = 100, {desc}")
reg("anio_base_indice", cmx["anio_base"], "anio", "primer anio con exportacion en 12 de 12 meses y exportacion >= 10% de la produccion de la cuenca")
for y in (2023, 2024, 2025):
    f = pd.Timestamp(f"{y}-12-01")
    reg(f"ma12_exp_dic{y}", cm.loc[f, "idx_exportacion_ma12_base2022"], "indice", f"media movil 12m a dic-{y}, base 2022, exportacion de crudo de la cuenca")
    reg(f"ma12_vm_dic{y}", cm.loc[f, "idx_produccion_vm_ma12_base2022"], "indice", f"media movil 12m a dic-{y}, base 2022, produccion de Vaca Muerta")
    reg(f"ma12_cuenca_dic{y}", cm.loc[f, "idx_produccion_cuenca_ma12_base2022"], "indice", f"media movil 12m a dic-{y}, base 2022, produccion de la cuenca")
# 2026 parcial (enero-agosto), solo para USD
reg("exp_2026_usd_millones", ca.loc[2026, "exportacion_usd"] / 1e6, "millones de USD", "enero-agosto de 2026 (anio parcial), monto FOB declarado")
reg("exp_2026_meses", int(ca.loc[2026, "meses_del_anio_con_dato"]), "meses", "meses de 2026 con datos de comercio exterior")
reg("exp_2026_usd_bbl", ca.loc[2026, "usd_por_bbl"], "USD/bbl", "enero-agosto de 2026, monto declarado / volumen")
reg("exp_usd_total_2020_2025_millones", ca.loc[2020:2025, "exportacion_usd"].sum() / 1e6, "millones de USD", "2020-2025, monto FOB declarado de crudo de la cuenca Neuquina")
# contraste con otras fuentes (terminales maritimos y oleoducto a Chile)
for y in range(2020, 2026):
    reg(f"contr_comex_sobre_terminales_{y}", ca.loc[y, "razon_comex_sobre_terminales"], "razon", f"{y}: exportacion de comercio exterior / exportacion de Oiltanking + Refineria Bahia Blanca (planilla 21)")
    reg(f"contr_comex_sobre_term_mas_oleo_{y}", ca.loc[y, "razon_comex_sobre_terminales_mas_oleoducto"], "razon", f"{y}: comercio exterior / (terminales + oleoducto a Chile de la planilla 20)")
for y in range(2020, 2026):
    reg(f"contr_term_{y}_m3", ca.loc[y, "terminales_m3"], "m3", f"{y}: Oiltanking + Refineria Bahia Blanca (planilla 21)")
    reg(f"contr_oleo_{y}_m3", ca.loc[y, "oleoducto_chile_planilla20_m3"], "m3", f"{y}: oleoducto a Chile, planilla 20 (sin dato antes de mayo de 2023)")
reg("contr_acum_comex_sobre_term_mas_oleo_2020_2025", ca.loc[2020:2025, "exportacion_m3"].sum() / (ca.loc[2020:2025, "terminales_m3"].sum() + ca.loc[2020:2025, "oleoducto_chile_planilla20_m3"].sum()), "razon", "2020-2025 acumulado: comercio exterior / (terminales + oleoducto a Chile)")
for y in (2023, 2024, 2025):
    reg(f"contr_chile_comex_sobre_p20_{y}", ca.loc[y, "razon_chile_comex_sobre_planilla20"], "razon", f"{y}: exportacion a Chile de comercio exterior / oleoducto a Chile de la planilla 20")
reg("val_precios_meses", cmx["validacion_precios"]["meses"], "meses", "meses 2020-2021 con precio implicito y precio FOB oficial")
reg("val_precios_corr", cmx["validacion_precios"]["correlacion"], "correlacion", "precio implicito (monto / volumen) vs precio FOB oficial Medanito, 2020-2021")
reg("val_precios_dif_pct", cmx["validacion_precios"]["diferencia_media_pct"], "%", "diferencia media del precio implicito frente al FOB oficial, 2020-2021")
reg("comex_registros_n", cmx["registros_exportacion_crudo"], "registros", "registros de exportacion de crudo por cuenca (comercio exterior, 2020-agosto 2026)")
# destinos y concentracion (crudo de la cuenca Neuquina, 2020-agosto 2026)
tp = cpais.groupby("pais")["volumen_m3"].sum().sort_values(ascending=False)
reg("comex_pais_total_m3", tp.sum(), "m3", "2020-agosto 2026, exportacion de crudo de la cuenca (comercio exterior)")
reg("comex_eeuu_pct", 100 * tp.get("ESTADOS UNIDOS", 0) / tp.sum(), "%", "2020-agosto 2026, destino Estados Unidos / exportacion de crudo de la cuenca")
reg("comex_chile_pct", 100 * tp.get("CHILE", 0) / tp.sum(), "%", "2020-agosto 2026, destino Chile / exportacion de crudo de la cuenca")
reg("comex_sin_pais_pct", 100 * tp.get("SIN PAIS (no aplica)", 0) / tp.sum(), "%", "2020-agosto 2026, volumen sin pais de destino ('no aplica') / exportacion de crudo de la cuenca")
ag = cconc[cconc["nivel"] == "empresa_agrupada"].reset_index(drop=True)
reg("conc_exp_top3_pct", ag["pct"].head(3).sum(), "%", "2020-2025, 3 mayores empresas exportadoras de crudo de la cuenca (agrupando variantes de razon social) / total")
reg("conc_exp_top1_pct", ag.loc[0, "pct"], "%", f"2020-2025, mayor empresa exportadora ({ag.loc[0, 'nombre']})")
sa = cconc[cconc["nivel"] == "empresa_sin_agrupar"].reset_index(drop=True)
reg("conc_exp_top3_sin_agrupar_pct", sa["pct"].head(3).sum(), "%", "2020-2025, 3 mayores razones sociales exportadoras sin agrupar variantes")
# volatilidad (2022-2025, mismo alcance: exportacion de la cuenca vs produccion de la cuenca)
x = cm.loc["2022-01-01":"2025-12-01"]
ve, vc = (100 * x[c].pct_change().dropna().std() for c in ("exportacion_bbl_dia", "prod_cuenca_bbl_dia"))
reg("vol_exp_pct", ve, "%", "desvio estandar de la variacion mensual, 2022-2025, exportacion de crudo de la cuenca")
reg("vol_cuenca_pct", vc, "%", "desvio estandar de la variacion mensual, 2022-2025, produccion de la cuenca")
reg("vol_ratio", ve / vc, "veces", "cociente de los dos desvios anteriores")
# control de la produccion por pozo frente a la serie oficial
reg("sep24_shale_sobre_vm_pct", cmx["control_produccion"]["shale_oficial_sobre_vm_por_pozo_pct"], "%", "septiembre de 2024: serie oficial 'shale' sobre Vaca Muerta por pozo (unico mes 2022-2025 con diferencia relevante)")
reg("sep24_dif_cuenca_m3", cmx["control_produccion"]["dif_cuenca_sep2024_m3"], "m3", "septiembre de 2024: produccion oficial de la cuenca menos la suma por pozo")
reg("sep24_dif_vm_anual_pct", 100 * cmx["control_produccion"]["dif_cuenca_sep2024_m3"] / (ca.loc[2024, "prod_vm_bbl_dia"] * 366 / 6.2898), "%", "efecto de esa diferencia sobre la produccion anual 2024 de Vaca Muerta")

# ------------------------------------------------------------------ contraste: terminales maritimos (planilla 21) y oleoducto a Chile (planilla 20)
for y in (2022, 2023, 2024, 2025):
    reg(f"exp_neu_{y}_bbl_dia", an.loc[y, "exportacion_terminales_bbl_dia"], "bbl/dia", f"{y}, promedio de 12 meses, {ALC_TERM}")
for y in (2023, 2024, 2025):
    reg(f"chile_{y}_bbl_dia", an.loc[y, "exportacion_oleoducto_chile_bbl_dia"], "bbl/dia",
        f"{y}: oleoducto Puesto Hernandez - Buta Mallin (planilla 20), promedio de los {int(an.loc[y, 'meses_oleoducto_chile_con_dato'])} meses con dato")
    reg(f"chile_{y}_meses", int(an.loc[y, "meses_oleoducto_chile_con_dato"]), "meses", f"{y}: meses con dato del oleoducto a Chile (planilla 20)")
reg("exp_neu_ultimo_mes_bbl_dia", k["exportacion_terminales_neuquinos_ultimo_mes_bbl_dia"], "bbl/dia", f"jun-2026, {ALC_TERM}")
reg("exp_neu_ultimo_mes_m3", k["exportacion_terminales_neuquinos_ultimo_mes_m3"], "m3", f"jun-2026, {ALC_TERM}")

# ------------------------------------------------------------------ planilla 21 completa (terminales de todo el pais): contexto
tt = term[term["operador_terminal"] != "TOTAL"]
tot_nac = tt["volumen_total_m3"].sum()
neu = tt[tt["origen_crudo_proxy"].str.startswith("Cuenca Neuquina")]["volumen_total_m3"].sum()
reg("exp_nacional_total_m3", tot_nac, "m3", "2018-jun 2026, 6 operadores de terminal de todo el pais (planilla 21)")
reg("exp_neuquina_total_m3", neu, "m3", "2018-jun 2026, Oiltanking + Refineria Bahia Blanca")
reg("exp_neuquina_pct_del_nacional", 100 * neu / tot_nac, "%", "volumen neuquino / volumen de los 6 operadores, 2018-jun 2026")
reg("conc_top3_operadores_pct", k["concentracion_top3_operadores_terminal_pct_2020_2025"], "%", "2020-2025, 3 mayores operadores de terminal / 6 operadores (planilla 21; mide quien opera el puerto, no quien exporta)")
_op = conc[conc["nivel"] == "operador_terminal"].head(3)
for _i, _r in enumerate(_op.itertuples(), 1):
    reg(f"conc_op{_i}_pct", _r.pct, "%", f"2020-2025, operador de terminal n.{_i} ({_r.nombre}) / total de los operadores")


# ------------------------------------------------------------------ ductos
reg("ductos_petroleo_n", rd["ductos_logicos_que_mueven_petroleo"], "ductos", "ductos logicos con volumen de petroleo > 0 en la planilla 20 (los dos id del mismo ducto cuentan una vez)")
reg("ductos_ranking_n", rd["ranking_n_ductos"], "ductos", "ductos de petroleo con capacidad informada valida tras las reglas R1, R3, R4, R5 y D2")
reg("ductos_sin_capacidad_n", rd["categorias"]["SIN_CAPACIDAD_EN_ANEXO_2A"], "ductos", "ductos de petroleo sin fila en el Anexo 2A")
reg("ductos_cap_dudosa_todos_n", rd["categorias"]["CAPACIDAD_DUDOSA_TODOS_LOS_ANIOS"], "ductos", "ductos de petroleo con capacidad dudosa en todos los anios")
reg("ductos_sin_cap_utilizable_n", rd["categorias"]["SIN_CAPACIDAD_EN_ANEXO_2A"] + rd["categorias"]["CAPACIDAD_DUDOSA_TODOS_LOS_ANIOS"], "ductos", "ductos de petroleo sin capacidad utilizable (sin Anexo 2A o dudosa en todos los anios)")
reg("ductos_sobre_100_n", rd["ranking_sobre_100"], "ductos", "ductos del ranking con utilizacion del segmento mas cargado > 100% en su anio mas reciente valido")
reg("ductos_ranking_parcial_n", rd["ranking_con_anio_parcial"], "ductos", "ductos del ranking cuyo anio mas reciente tiene menos de 12 meses")
reg("ductos_ranking_a_revisar_n", rd["ranking_a_revisar"], "ductos", "ductos del ranking marcados a revisar (R2 o R6)")
reg("ducto_anios_excluidos_n", rd["duct_anios_con_capacidad_dudosa"], "ducto-anios", "ducto-anios con capacidad dudosa presentes en el modelo")
reg("ductos_con_anio_excluido_n", rd["ductos_con_algun_anio_dudoso"], "ductos", "ductos con al menos un anio excluido")
reg("regla_r1_veces", rd["reglas"]["R1_umbral_veces"], "veces", "R1: salto de la capacidad operativa entre anios consecutivos")
reg("regla_r3_veces", rd["reglas"]["R3_umbral_veces"], "veces", "R3: caudal liquido observado / capacidad empleada informada")
reg("regla_r5_dias", rd["reglas"]["R5_dias"], "dias", "R5: dias operativos informados en el Anexo 2A")
for i, r in rank[rank["sobre_100_pct"]].reset_index(drop=True).iterrows():
    reg(f"ducto_sobre100_{i + 1}_pct", r["utilizacion_segmento_mas_cargado_pct"], "%", f"{r['denominacion_ducto']} {int(r['anio'])} ({int(r['meses_con_dato'])} meses), segmento mas cargado de liquidos / capacidad operativa informada")
cap = pd.read_csv(os.path.join(CLEAN, "fact_capacidad_ductos.csv"), encoding="utf-8-sig", usecols=["idducto", "anio", "mes", "capacidad_valida"])
tr = pd.read_csv(os.path.join(CLEAN, "fact_transporte_ductos.csv"), encoding="utf-8-sig", usecols=["idducto", "anio", "mes"])
dm = tr.drop_duplicates()
reg("cobertura_capacidad_ducto_mes_pct", 100 * len(cap) / len(dm), "%", "ducto-mes con fila en el Anexo 2A / ducto-mes con transporte (todos los productos)")
da_tr = tr[["idducto", "anio"]].drop_duplicates()
da_cap = cap[cap["capacidad_valida"]][["idducto", "anio"]].drop_duplicates()
reg("cobertura_capacidad_ducto_anio_pct", 100 * len(da_cap) / len(da_tr), "%", "ducto-anio con capacidad operativa > 0 / ducto-anio con transporte (todos los productos)")

# ------------------------------------------------------------------ evidencia del proxy y de la cobertura (verificaciones posteriores a la auditoria)
mov = pd.read_csv(os.path.join(CLEAN, "fact_movimientos_exportacion_ductos.csv"), encoding="utf-8-sig", low_memory=False,
                  usecols=["empresa", "anio", "tipo_operacion", "producto", "volumen"])
ex_neu = mov[(mov["tipo_operacion"] == "Exportacion") & mov["empresa"].isin(["Oiltanking EBYTEM S.A.", "Refineria Bahia Blanca SAU"])]
es_neu = ex_neu["producto"].str.contains("neuqu|medanito", case=False, regex=True, na=False)
reg("proxy_pct_producto_neuquino", 100 * ex_neu.loc[es_neu, "volumen"].sum() / ex_neu["volumen"].sum(), "%",
    "2018-jun 2026: volumen exportado por Oiltanking y Refineria Bahia Blanca cuyo producto se rotula Neuquen / Rio Negro (Medanito) / Neuquino")
rbb = ex_neu[ex_neu["empresa"].str.startswith("Refineria")].groupby("anio")["volumen"].sum()
tot_neu = ex_neu.groupby("anio")["volumen"].sum()
for y in (2024, 2025):
    reg(f"rbb_pct_{y}", 100 * rbb.get(y, 0) / tot_neu[y], "%", f"{y}: Refineria Bahia Blanca / exportacion de los terminales neuquinos (no informa desde febrero de 2026)")
capf = pd.read_csv(os.path.join(CLEAN, "fact_capacidad_ductos.csv"), encoding="utf-8-sig", low_memory=False,
                   usecols=["idducto", "idducto_logico", "anio", "capacidad_operativa_maxima_m3_dia", "capacidad_dudosa"])
vig = capf[(~capf["capacidad_dudosa"].astype(bool)) & (capf["capacidad_operativa_maxima_m3_dia"] > 0) & capf["idducto_logico"].isin(rank["idducto_logico"])]
vig = vig.drop_duplicates(["idducto", "anio"])
n_op = vig.groupby("idducto_logico")["capacidad_operativa_maxima_m3_dia"].agg(["nunique", "count"])
reg("ductos_ranking_cap_constante_n", int(((n_op["nunique"] == 1) & (n_op["count"] >= 3)).sum()), "ductos",
    "ductos del ranking con la misma capacidad operativa en todos sus anios validos (3 o mas anios)")
reg("ductos_ranking_un_anio_n", int((n_op["count"] == 1).sum()), "ductos", "ductos del ranking con un solo anio de capacidad valida")
reg("ductos_sobre_100_a_revisar_n", int(rank.loc[rank["sobre_100_pct"], "a_revisar_capacidad"].sum()), "ductos",
    "ductos sobre 100% con capacidad marcada a revisar (R2 o R6)")

# ------------------------------------------------------------------ parametros metodologicos (definidos en los scripts 11 y 13)
reg("hallazgos_n", 19, "hallazgos", "auditoria de 2026-10-05, F1 a F19")
reg("bbl_por_m3", 6.2898, "bbl/m3", "factor de conversion usado en todo el proyecto")
reg("umbral_km", 30, "km", "script 13: distancia a la mediana de las coordenadas de su yacimiento a partir de la cual se omite un pozo del mapa")
reg("umbral_exp_pct", 10, "%", "script 11: exportacion / produccion de Vaca Muerta minima para elegir el anio base del indice")
reg("operadores_n", int(tt["operador_terminal"].nunique()), "operadores", "operadores de terminal en la planilla 21")

os.makedirs(WEB, exist_ok=True)
with open(os.path.join(WEB, "registro_cifras.json"), "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=1)
print(f"registro_cifras.json: {len(R)} cifras")
