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

# ------------------------------------------------------------------ produccion de la cuenca y exportacion
for y in range(2022, 2026):
    reg(f"prod_cuenca_{y}_bbl_dia", an.loc[y, "prod_cuenca_bbl_dia"], "bbl/dia", f"{y}, {ALC_CUENCA}")
    reg(f"prod_vm_{y}_bbl_dia", an.loc[y, "prod_vm_bbl_dia"], "bbl/dia", f"{y}, Vaca Muerta")
    reg(f"exp_neu_{y}_bbl_dia", an.loc[y, "exportacion_terminales_bbl_dia"], "bbl/dia", f"{y}, promedio de 12 meses, {ALC_TERM}")
    reg(f"pct_exp_cuenca_{y}", an.loc[y, "pct_exportado_cuenca"], "%", f"{y}: exportacion de terminales neuquinos / {ALC_CUENCA}")
    reg(f"pct_exp_vm_{y}", an.loc[y, "pct_exportado_vm"], "%", f"{y}: exportacion de terminales neuquinos / produccion de Vaca Muerta")
    reg(f"vm_sobre_cuenca_{y}", an.loc[y, "vm_sobre_cuenca_pct"], "%", f"{y}: Vaca Muerta / cuenca Neuquina")
    for b in (2021, 2022, 2023):
        for serie, col in (("exp", "idx_exportacion_terminales"), ("vm", "idx_produccion_vm"), ("cuenca", "idx_produccion_cuenca")):
            v = an.loc[y, f"{col}_base{b}"]
            if pd.notna(v):
                reg(f"idx_{serie}_{y}_base{b}", v, "indice", f"promedio anual {y}, base {b} = 100 ({'exportacion neuquina por terminales' if serie == 'exp' else 'produccion ' + ('de Vaca Muerta' if serie == 'vm' else 'de la cuenca')})")
reg("anio_base_indice", k["indice_anio_base"], "anio", "primer anio con 12 de 12 meses de exportacion neuquina y exportacion >= 10% de la produccion de Vaca Muerta")
for y in (2023, 2024, 2025):
    f = pd.Timestamp(f"{y}-12-01")
    reg(f"ma12_exp_dic{y}", mens.loc[f, "idx_exportacion_terminales_ma12_base2022"], "indice", f"media movil 12m a dic-{y}, base 2022, exportacion neuquina por terminales")
    reg(f"ma12_vm_dic{y}", mens.loc[f, "idx_produccion_vm_ma12_base2022"], "indice", f"media movil 12m a dic-{y}, base 2022, produccion de Vaca Muerta")
    reg(f"ma12_cuenca_dic{y}", mens.loc[f, "idx_produccion_cuenca_ma12_base2022"], "indice", f"media movil 12m a dic-{y}, base 2022, produccion de la cuenca")
# oleoducto a Chile: serie aparte
for y in (2023, 2024, 2025):
    reg(f"chile_{y}_bbl_dia", an.loc[y, "exportacion_oleoducto_chile_bbl_dia"], "bbl/dia",
        f"{y}: oleoducto Puesto Hernandez - Buta Mallin (planilla 20), promedio de los {int(an.loc[y, 'meses_oleoducto_chile_con_dato'])} meses con dato; serie aparte")
    reg(f"chile_{y}_meses", int(an.loc[y, "meses_oleoducto_chile_con_dato"]), "meses", f"{y}: meses con dato del oleoducto a Chile")
for y in (2024, 2025):
    reg(f"pct_exp_cuenca_con_chile_{y}", 100 * (an.loc[y, "exportacion_terminales_bbl_dia"] + an.loc[y, "exportacion_oleoducto_chile_bbl_dia"]) / an.loc[y, "prod_cuenca_bbl_dia"],
        "%", f"{y}: (terminales neuquinos + oleoducto a Chile) / produccion de la cuenca; solo como referencia")
reg("exp_neu_ultimo_mes_bbl_dia", k["exportacion_terminales_neuquinos_ultimo_mes_bbl_dia"], "bbl/dia", f"jun-2026, {ALC_TERM}")
reg("exp_neu_ultimo_mes_m3", k["exportacion_terminales_neuquinos_ultimo_mes_m3"], "m3", f"jun-2026, {ALC_TERM}")

# ------------------------------------------------------------------ exportacion nacional por terminales (planilla 21)
tt = term[term["operador_terminal"] != "TOTAL"]
tot_nac = tt["volumen_total_m3"].sum()
neu = tt[tt["origen_crudo_proxy"].str.startswith("Cuenca Neuquina")]["volumen_total_m3"].sum()
reg("exp_nacional_total_m3", tot_nac, "m3", "2018-jun 2026, 6 operadores de terminal de todo el pais (planilla 21)")
reg("exp_neuquina_total_m3", neu, "m3", "2018-jun 2026, Oiltanking + Refineria Bahia Blanca")
reg("exp_neuquina_pct_del_nacional", 100 * neu / tot_nac, "%", "volumen neuquino / volumen de los 6 operadores, 2018-jun 2026")
reg("sin_pais_pct", k["pct_no_identificado"], "%", "volumen con pais NO IDENTIFICADO / volumen de los 6 operadores, 2018-jun 2026 (100% TERMAP)")
reg("con_pais_pct", k["pct_con_pais_identificado"], "%", "volumen con pais identificado / volumen de los 6 operadores, 2018-jun 2026")
reg("sin_pais_m3", k["volumen_no_identificado_m3"], "m3", "2018-jun 2026, 6 operadores")
termap = tt[tt["operador_terminal"].str.startswith("TERMAP")]
reg("termap_pct_2019", 100 * termap.loc[termap["anio"] == 2019, "volumen_total_m3"].sum() / tt.loc[tt["anio"] == 2019, "volumen_total_m3"].sum(), "%", "TERMAP / total de los 6 operadores, 2019")
reg("termap_pct_2026", 100 * termap.loc[termap["anio"] == 2026, "volumen_total_m3"].sum() / tt.loc[tt["anio"] == 2026, "volumen_total_m3"].sum(), "%", "TERMAP / total de los 6 operadores, ene-jun 2026")
reg("conc_top3_operadores_pct", k["concentracion_top3_operadores_terminal_pct_2020_2025"], "%", "2020-2025, 3 mayores operadores de terminal / 6 operadores (no es concentracion de exportadores)")
reg("conc_top3_cargadores_pct", k["concentracion_top3_cargadores_pct_2020_2025"], "%", "2020-2025, 3 mayores cargadores (quien exporta, agrupando variantes de nombre) / total de los 6 operadores")
reg("vol_mensual_exp_neu_pct", k["volatilidad_mensual_2022_2025_exportacion_terminales_pct"], "%", "desvio estandar de la variacion mensual, 2022-2025, exportacion neuquina por terminales")
reg("vol_mensual_prod_vm_pct", k["volatilidad_mensual_2022_2025_produccion_vm_pct"], "%", "desvio estandar de la variacion mensual, 2022-2025, produccion de Vaca Muerta")
reg("vol_ratio", k["volatilidad_mensual_2022_2025_exportacion_terminales_pct"] / k["volatilidad_mensual_2022_2025_produccion_vm_pct"], "veces", "cociente de los dos desvios anteriores")
reg("vol_mensual_exp_nac_pct", k["volatilidad_mensual_2020_2025_exportacion_nacional_terminales_pct"], "%", "2020-2025, exportacion de los 6 operadores de todo el pais (contexto)")

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

# ------------------------------------------------------------------ parametros metodologicos (definidos en los scripts 11 y 13)
reg("bbl_por_m3", 6.2898, "bbl/m3", "factor de conversion usado en todo el proyecto")
reg("umbral_km", 30, "km", "script 13: distancia a la mediana de las coordenadas de su yacimiento a partir de la cual se omite un pozo del mapa")
reg("umbral_exp_pct", 10, "%", "script 11: exportacion / produccion de Vaca Muerta minima para elegir el anio base del indice")
reg("operadores_n", int(tt["operador_terminal"].nunique()), "operadores", "operadores de terminal en la planilla 21")

os.makedirs(WEB, exist_ok=True)
with open(os.path.join(WEB, "registro_cifras.json"), "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=1)
print(f"registro_cifras.json: {len(R)} cifras")
