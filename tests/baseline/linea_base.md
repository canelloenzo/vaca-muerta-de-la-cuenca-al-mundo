# Línea de base: pruebas ANTES de corregir (estado auditado + tests)

- Fecha: 2026-10-05 · commit base de la corrida: `f177d88` · Python 3.14.3
- Pruebas: 100 → PASS 76 · FAIL 24 · SKIP 0
- De las FAIL, pruebas de estado objetivo (esperadas en rojo antes de corregir): 24

| módulo | prueba | estado |
|---|---|---|
| test_01_raw_vs_clean | test_filas_por_etapa | PASS |
| test_01_raw_vs_clean | test_unica_variante_de_formacion | PASS |
| test_01_raw_vs_clean | test_solape_nc_2022_2025_identico_a_anuales | PASS |
| test_01_raw_vs_clean | test_no_hay_duplicados_de_clave | PASS |
| test_01_raw_vs_clean | test_total_bbl_raw_igual_clean | PASS |
| test_01_raw_vs_clean | test_pozo_mes_fila_a_fila | PASS |
| test_01_raw_vs_clean | test_sin_produccion_negativa | PASS |
| test_01_raw_vs_clean | test_yacimiento_mes_igual_agregacion_desde_raw | PASS |
| test_01_raw_vs_clean | test_dias_mes_es_calendario | PASS |
| test_01_raw_vs_clean | test_el_nc_trae_2026_no_usado | PASS |
| test_02_claves | test_clean_grano_unico[fact_produccion_pozo_mes_vaca_muerta.csv-key0] | PASS |
| test_02_claves | test_clean_grano_unico[fact_produccion_yacimiento_mes_vaca_muerta.csv-key1] | PASS |
| test_02_claves | test_clean_grano_unico[fact_capacidad_ductos.csv-key2] | PASS |
| test_02_claves | test_clean_grano_unico[dim_ducto.csv-key3] | PASS |
| test_02_claves | test_clean_grano_unico[dim_pozo_coordenadas_no_convencional.csv-key4] | PASS |
| test_02_claves | test_clean_grano_unico[dim_precio_exportacion_crudo.csv-key5] | PASS |
| test_02_claves | test_clean_grano_unico[dim_tipo_crudo_cuenca.csv-key6] | PASS |
| test_02_claves | test_clean_grano_unico[fact_balance_energetico_nacional.csv-key7] | PASS |
| test_02_claves | test_clean_sin_filas_exactas_duplicadas[fact_transporte_ductos.csv] | PASS |
| test_02_claves | test_clean_sin_filas_exactas_duplicadas[fact_movimientos_exportacion_ductos.csv] | PASS |
| test_02_claves | test_web_grano_unico[produccion_mapa.csv-key0] | PASS |
| test_02_claves | test_web_grano_unico[produccion_anual.csv-key1] | PASS |
| test_02_claves | test_web_grano_unico[top_yacimientos.csv-key2] | PASS |
| test_02_claves | test_web_grano_unico[exportacion_por_empresa.csv-key3] | PASS |
| test_02_claves | test_web_indices_una_fila_por_mes | PASS |
| test_02_claves | test_web_pais_anio_unico | PASS |
| test_02_claves | test_idducto_determina_la_denominacion | PASS |
| test_02_claves | test_denominacion_normalizada_apunta_a_un_ducto_logico | FAIL |
| test_03_exportacion | test_duplicados_exactos_raw_y_clean | PASS |
| test_03_exportacion | test_exportacion_igual_mercado_externo | PASS |
| test_03_exportacion | test_volumen_total_exportado | PASS |
| test_03_exportacion | test_web_por_pais_igual_recalculo | PASS |
| test_03_exportacion | test_sin_pais_es_no_identificado_de_termap | PASS |
| test_03_exportacion | test_concentracion_operadores_2020_2025 | PASS |
| test_03_exportacion | test_empresas_de_terminal_sin_variantes_de_nombre | PASS |
| test_03_exportacion | test_operador_neuquino_por_anio | PASS |
| test_03_exportacion | test_orden_de_magnitud_contra_balance[2023] | PASS |
| test_03_exportacion | test_orden_de_magnitud_contra_balance[2024] | PASS |
| test_03_exportacion | test_orden_de_magnitud_contra_balance[2025] | PASS |
| test_04_ductos | test_planilla20_raw_igual_clean | PASS |
| test_04_ductos | test_universo_de_ductos | PASS |
| test_04_ductos | test_fact_capacidad_reconciliada | PASS |
| test_04_ductos | test_capacidad_valida_es_operativa_positiva | PASS |
| test_04_ductos | test_utilizacion_absurda_era_mezcla_de_gas[329-2022] | PASS |
| test_04_ductos | test_utilizacion_absurda_era_mezcla_de_gas[329-2023] | PASS |
| test_04_ductos | test_utilizacion_absurda_era_mezcla_de_gas[329-2024] | PASS |
| test_04_ductos | test_utilizacion_absurda_era_mezcla_de_gas[171-2023] | PASS |
| test_04_ductos | test_utilizacion_absurda_era_mezcla_de_gas[97-2022] | PASS |
| test_04_ductos | test_vmoc_segmento_unico | PASS |
| test_04_ductos | test_conteo_de_ductos_sobre_100_segun_definicion | PASS |
| test_04_ductos | test_capacidades_sospechosas_documentadas | PASS |
| test_04_ductos | test_universo_petrolero_y_capacidad | PASS |
| test_05_metricas | test_bbl_dia_dic_2025_y_variacion | PASS |
| test_05_metricas | test_dias_se_cuentan_una_vez_por_mes | PASS |
| test_05_metricas | test_top_yacimientos_igual_recalculo | PASS |
| test_05_metricas | test_indices_base_2019_identicos_a_web | PASS |
| test_05_metricas | test_volatilidad_mensual_2020_2025 | PASS |
| test_05_metricas | test_pct_no_convencional | PASS |
| test_05_metricas | test_convencional_solo_observable_desde_2022 | PASS |
| test_05_metricas | test_produccion_nc_junio_2026_es_dato_disponible | PASS |
| test_05_metricas | test_coordenadas_pozos | PASS |
| test_06_cifras_publicadas | test_kpis_html_igual_web | PASS |
| test_06_cifras_publicadas | test_indices_html_igual_web | PASS |
| test_06_cifras_publicadas | test_top_yacimientos_html_igual_web | PASS |
| test_06_cifras_publicadas | test_mapa_html_igual_web | PASS |
| test_06_cifras_publicadas | test_prod_anual_html_igual_recalculo | PASS |
| test_06_cifras_publicadas | test_paises_html_igual_recalculo | PASS |
| test_06_cifras_publicadas | test_empresas_html_igual_recalculo | PASS |
| test_06_cifras_publicadas | test_s4_produccion | PASS |
| test_06_cifras_publicadas | test_s4_pozos_y_coordenadas | PASS |
| test_06_cifras_publicadas | test_s4_exportacion | PASS |
| test_06_cifras_publicadas | test_s4_exportacion_neuquina_sobre_produccion_vm | PASS |
| test_06_cifras_publicadas | test_s4_precios_2019_2021 | PASS |
| test_06_cifras_publicadas | test_s4_cobertura_de_capacidad | PASS |
| test_06_cifras_publicadas | test_s4_locale_en_power_query | PASS |
| test_07_estado_objetivo | test_f1_serie_exportacion_cuenca_neuquina_existe | FAIL |
| test_07_estado_objetivo | test_f1_comparacion_cierra_en_dic_2025 | FAIL |
| test_07_estado_objetivo | test_f1_indice_con_base_documentada_y_sensibilidad | FAIL |
| test_07_estado_objetivo | test_f6_tarjeta_produccion_jun_2026_rotulada | FAIL |
| test_07_estado_objetivo | test_f7_serie_nacional_muestra_no_identificado | FAIL |
| test_07_estado_objetivo | test_f8_concentracion_por_cargador_publicada | FAIL |
| test_07_estado_objetivo | test_f2_no_se_publica_171_de_vmoc | FAIL |
| test_07_estado_objetivo | test_f4_html_no_dice_85_sin_capacidad | FAIL |
| test_07_estado_objetivo | test_f2_utilizacion_usa_solo_liquidos | FAIL |
| test_07_estado_objetivo | test_f3_exclusion_por_ducto_anio | FAIL |
| test_07_estado_objetivo | test_html_tiene_seccion_limitaciones | FAIL |
| test_07_estado_objetivo | test_readme_tiene_limitaciones_y_cobertura_por_serie | PASS |
| test_07_estado_objetivo | test_readme_explica_como_conseguir_raw_y_correr_pruebas | FAIL |
| test_07_estado_objetivo | test_f7_html_rotula_volumen_sin_pais | FAIL |
| test_07_estado_objetivo | test_f10_sin_lenguaje_causal_sin_evidencia[explica buena parte] | FAIL |
| test_07_estado_objetivo | test_f10_sin_lenguaje_causal_sin_evidencia[capacidad real] | FAIL |
| test_07_estado_objetivo | test_f10_sin_lenguaje_causal_sin_evidencia[replican exactamente] | FAIL |
| test_07_estado_objetivo | test_f10_sin_lenguaje_causal_sin_evidencia[capacidad nominal] | FAIL |
| test_07_estado_objetivo | test_f10_sin_lenguaje_causal_sin_evidencia[por encima de su capacidad de dise\xf1o] | FAIL |
| test_07_estado_objetivo | test_f10_sin_lenguaje_causal_sin_evidencia[cuello de botella] | FAIL |
| test_07_estado_objetivo | test_f17_no_dice_238_convencionales | FAIL |
| test_07_estado_objetivo | test_f12_dax_sin_allexcept_con_tabla | FAIL |
| test_07_estado_objetivo | test_f12_dax_balance_corrige_el_signo | FAIL |
| test_07_estado_objetivo | test_f16_dax_no_cita_1660 | FAIL |
| test_07_estado_objetivo | test_f19_sin_cifras_de_vmos_sin_fuente | PASS |
