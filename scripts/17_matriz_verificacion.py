"""
Matriz de verificacion: para cada grupo de afirmaciones publicadas, que pruebas la sostienen y su resultado actual.

Corre la suite (pytest) con salida JUnit, relaciona cada afirmacion con sus pruebas por nombre y escribe MATRIZ_VERIFICACION.md.
Un grupo figura como VERIFICADO solo si todas sus pruebas pasaron (sin omitidas ni fallidas). Lo que los datos no permiten comprobar
figura aparte, como LIMITE DECLARADO, con la evidencia que lo acota y el lugar del informe donde se declara.
Uso: python scripts/17_matriz_verificacion.py
"""
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

GRUPOS = [
    ("Producción", [
        ("P1", "Producción de Vaca Muerta 2006–2025 (acumulado, filas, diciembre de 2025, variación interanual)",
         ["test_total_bbl_raw_igual_clean", "test_filas_por_etapa", "test_s4_produccion", "test_bbl_dia_dic_2025_y_variacion", "test_pozo_mes_fila_a_fila", "test_yacimiento_mes_igual_agregacion_desde_raw", "test_dias_se_cuentan_una_vez_por_mes"]),
        ("P2", "Producción de junio de 2026, solo no convencional, y su variación interanual",
         ["test_produccion_nc_junio_2026_es_dato_disponible", "test_tarjeta_produccion_jun_2026_solo_no_convencional", "test_f6_tarjeta_produccion_jun_2026_rotulada", "test_el_nc_trae_2026_no_usado"]),
        ("P3", "% no convencional 2022–2025 y rango del convencional",
         ["test_pct_no_convencional", "test_convencional_solo_observable_desde_2022"]),
        ("P4", "Producción de la cuenca (serie oficial) y coincidencia con la suma por pozo, salvo septiembre de 2024 (Shell no figura)",
         ["test_produccion_oficial_de_la_cuenca", "test_septiembre_2024_unica_diferencia_de_produccion_por_pozo", "test_acumulado_no_converge_y_septiembre_2024_es_shell", "test_produccion_total_de_la_cuenca"]),
        ("P5", "Mapa (pozos y omitidos), yacimientos y producción anual",
         ["test_mapa_html_igual_web", "test_s4_pozos_y_coordenadas", "test_pozos_con_coordenadas_dudosas", "test_top_yacimientos_igual_recalculo", "test_top_yacimientos_html_igual_web", "test_prod_anual_html_igual_recalculo", "test_coordenadas_pozos"]),
    ]),
    ("Exportación", [
        ("E1", "Serie principal de exportación (comercio exterior): registros, volumen y USD por año",
         ["test_registros_totales_y_de_exportacion_de_crudo", "test_exportacion_anual_igual_recalculo", "test_precio_implicito_anual"]),
        ("E2", "Valor en USD: precio implícito validado contra la tabla oficial de precios FOB (2020–2021) y contra el Brent mensual de la EIA (2020–2025)",
         ["test_validacion_contra_precio_fob_oficial", "test_validacion_del_valor_en_usd_contra_el_brent", "test_s4_precios_2019_2021"]),
        ("E3", "% exportado de la producción de la cuenca y elección del año base",
         ["test_porcentaje_exportado_de_la_cuenca", "test_anio_base_2022_cumple_el_criterio", "test_anio_base_por_criterio_explicito"]),
        ("E4", "Conclusión: con las dos fuentes y las tres bases, la exportación crece más que la producción y el % exportado sube cada año",
         ["test_afirmacion_vale_con_las_dos_fuentes_y_las_tres_bases", "test_afirmacion_exportacion_crece_mas_que_produccion_de_la_cuenca", "test_indices_anuales_y_sensibilidad", "test_ma12_de_diciembre_2025_recalculado_desde_raw", "test_comparacion_cierra_en_dic_2025_y_ma12_es_media_de_12_meses"]),
        ("E5", "Contraste entre fuentes: difieren menos del 3% hasta 2022, distinto nivel desde 2023, no es calendario y aparece en los destinos citados",
         ["test_comercio_exterior_vs_terminales_menos_de_3pct_hasta_2022", "test_terminales_informan_mas_que_comercio_exterior_en_los_destinos_citados", "test_acumulado_no_converge_y_septiembre_2024_es_shell", "test_exportacion_terminales_igual_recalculo", "test_oleoducto_a_chile_va_aparte_y_no_se_suma", "test_volumen_total_exportado", "test_duplicados_exactos_raw_y_clean"]),
        ("E6", "Destinos y concentración por empresa exportadora (y por operador de terminal como contexto)",
         ["test_destinos_y_concentracion_publicados", "test_html_igual_a_las_tablas_comex", "test_concentracion_operadores_2020_2025", "test_concentracion_por_operador_y_por_cargador"]),
        ("E7", "Volatilidad mensual de la exportación frente a la producción",
         ["test_volatilidad_publicada", "test_volatilidad_mensual_2020_2025"]),
    ]),
    ("Transporte", [
        ("D1", "Petróleo transportado por Allen–Puerto Rosales y la línea Duplicar (inicio en marzo de 2025)",
         ["test_allen_puerto_rosales_y_duplicar_igual_recalculo", "test_duplicar_aparece_en_marzo_de_2025", "test_planilla20_raw_igual_clean"]),
        ("D2", "Capacidades: reglas de exclusión, ranking y contraste (el flujo de 2024 supera la capacidad que informa el Anexo)",
         ["test_el_flujo_de_2024_supera_la_capacidad_que_informa_el_anexo", "test_ranking_igual_recalculo_independiente", "test_reglas_de_capacidad_dudosa_igual_implementacion_independiente", "test_clasificacion_de_ductos_que_mueven_petroleo", "test_columnas_nuevas_de_fact_capacidad_igual_recalculo", "test_universo_de_ductos", "test_el_ranking_no_cambia_con_r1_10x"]),
        ("D3", "No se publica una utilización para VMOC",
         ["test_f2_no_se_publica_171_de_vmoc", "test_ningun_archivo_nuevo_publica_171_de_vmoc", "test_ranking_no_incluye_ducto_anios_dudosos_ni_publica_su_utilizacion"]),
    ]),
    ("Fuentes externas", [
        ("X1", "Cifras y fechas de la caja de proyectos y de las capacidades externas: cada una está en el texto de la fuente citada y el enlace responde",
         ["test_el_registro_tiene_los_valores_externos_citados", "test_las_cifras_estan_en_el_texto_de_la_fuente", "test_los_enlaces_responden", "test_los_enlaces_externos_son_de_fuentes_permitidas", "test_la_caja_de_proyectos_declara_que_es_informacion_externa"]),
    ]),
    ("Forma y publicación", [
        ("T1", "Toda cifra de README, HTML y traspaso sale del registro; sin palabras que el dato no respalda, rutas, correos ni marcadores",
         ["test_toda_cifra_del_texto_sale_del_registro", "test_sin_palabras_prohibidas", "test_sin_marcadores_ni_rutas_ni_correos", "test_los_archivos_publicados_son_la_salida_de_las_plantillas", "test_anios_sin_separador_de_miles_y_nombres_bien_escritos", "test_f10_sin_lenguaje_causal_sin_evidencia"]),
        ("T2", "El dashboard abre sin errores de consola en un navegador (escritorio y celular)",
         ["test_html_sin_errores_de_consola"]),
    ]),
]

LIMITES = [
    ("L1", "Cuál de las dos fuentes de exportación (comercio exterior; terminales más oleoducto) es la correcta",
     "No hay un tercer dato público. Se acotó: no es calendario, aparece en todos los destinos y la dirección coincide. Por eso el informe solo afirma la dirección y muestra el nivel como rango.",
     "Sección de exportación (contraste) y Limitaciones del dashboard; README."),
    ("L2", "Exportación de Vaca Muerta aislada del resto de la cuenca",
     "El comercio exterior rotula por cuenca, no por formación; Vaca Muerta es una parte de la producción de la cuenca. La serie se rotula como crudo de la cuenca Neuquina.",
     "Limitaciones del dashboard; README."),
    ("L3", "Capacidad física de cada ducto",
     "Las fuentes (Anexo 2A, Secretaría de Energía, Oldelval, nota del sector, Tramos de Integridad) no coinciden. Se publica el petróleo transportado y las capacidades por fuente, sin porcentaje de utilización como resultado.",
     "Acto II del dashboard; Limitaciones."),
    ("L4", "Fechas y capacidades futuras de VMOS y Duplicar Norte",
     "Son anuncios. Cada cifra figura en el texto crudo de su fuente (prueba X1), con fecha, fuera de gráficos e indicadores.",
     "Caja \"Proyectos anunciados\" del dashboard."),
    ("L5", "Contraste con la Secretaría de Energía o con las operadoras",
     "Requiere una consulta externa; el análisis es descriptivo sobre datos públicos.",
     "Limitaciones."),
    ("L6", "Unidad del campo caudal_nominal de la tabla de Tramos de Integridad",
     "Inferida (m³/h) por coincidencia exacta con la capacidad del Anexo en varios ductos; se declara como inferencia y no sostiene ninguna conclusión.",
     "Limitaciones (capacidades contrastadas)."),
    ("L7", "Medidas DAX y páginas del reporte de Power BI",
     "No se pudieron ejecutar sin el archivo de plantilla (.pbit). Los valores esperados salen de las mismas tablas verificadas arriba.",
     "CAMBIOS_POWERBI.md."),
]


def main():
    with tempfile.TemporaryDirectory() as d:
        xml = Path(d) / "junit.xml"
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", f"--junitxml={xml}", "-p", "no:cacheprovider"], cwd=REPO, capture_output=True, text=True)
        resumen = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        res = {}
        for tc in ET.parse(xml).getroot().iter("testcase"):
            nombre = tc.get("name").split("[")[0]
            estado = "fallo" if (tc.find("failure") is not None or tc.find("error") is not None) else ("omitida" if tc.find("skipped") is not None else "pasa")
            res.setdefault(nombre, []).append(estado)
    L = ["# Matriz de verificación", "",
         "Qué afirma el informe, qué pruebas lo sostienen y su resultado actual. Se genera con `python scripts/17_matriz_verificacion.py` (corre toda la suite). "
         "Un grupo figura como **VERIFICADO** solo si todas sus pruebas pasaron, sin omitidas. Lo que los datos no permiten comprobar figura aparte como **LÍMITE DECLARADO**, con la evidencia que lo acota y el lugar del informe donde se declara.", "",
         f"Resultado de la suite en esta corrida: `{resumen}`.", ""]
    total_ok = total = 0
    for sec, filas in GRUPOS:
        L += [f"## {sec}", "", "| Id | Afirmación publicada | Pruebas | Estado |", "|---|---|---|---|"]
        for id_, texto, tests in filas:
            estados = [e for t in tests for e in res.get(t, ["no existe"])]
            ok = bool(estados) and all(e == "pasa" for e in estados)
            total += 1
            total_ok += ok
            malos = sorted({e for e in estados if e != "pasa"})
            L.append(f"| {id_} | {texto} | {len(estados)} | {'VERIFICADO' if ok else 'REVISAR (' + ', '.join(malos) + ')'} |")
        L.append("")
    L += ["## Límites declarados (no verificables con los datos disponibles)", "", "| Id | Qué no se puede comprobar | Evidencia que lo acota | Dónde se declara |", "|---|---|---|---|"]
    for id_, que, evid, donde in LIMITES:
        L.append(f"| {id_} | {que} | {evid} | {donde} |")
    L += ["", f"**Grupos de afirmaciones verificados: {total_ok} de {total}.** Límites declarados: {len(LIMITES)}.", ""]
    (REPO / "MATRIZ_VERIFICACION.md").write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(f"MATRIZ_VERIFICACION.md: {total_ok}/{total} grupos verificados; suite: {resumen}")
    sys.exit(0 if total_ok == total else 1)


if __name__ == "__main__":
    main()
