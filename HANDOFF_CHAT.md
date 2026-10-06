# Traspaso: Vaca Muerta, de la cuenca al mundo

Insumo para escribir, en otra conversación, el posteo de LinkedIn, la entrada del CV y la preparación de entrevista. Este archivo no contiene el posteo ni el CV. Todas las cifras salen de `data/web/registro_cifras.json`; no hay que recalcular nada ni usar una cifra que no esté acá con su alcance.

## 1. Enlaces públicos

- Repositorio: <https://github.com/canelloenzo/vaca-muerta-de-la-cuenca-al-mundo>
- Dashboard web (GitHub Pages): <https://canelloenzo.github.io/vaca-muerta-de-la-cuenca-al-mundo/>
- Release con el `.pbix`: <https://github.com/canelloenzo/vaca-muerta-de-la-cuenca-al-mundo/releases/latest>
- LinkedIn del autor: <https://www.linkedin.com/in/enzocanello>

## 2. Qué es el proyecto, en cuatro líneas

Pipeline en Python (pandas) que limpia datos públicos de la Secretaría de Energía y ENARGAS, un modelo y reporte de Power BI de 6 páginas, y un dashboard web con Chart.js. Cuenta la historia en tres actos: producción, transporte y exportación de petróleo de la cuenca Neuquina. Una auditoría completa encontró 19 hallazgos que se corrigieron antes de publicar. Cada cifra publicada declara su alcance y una prueba automática compara los textos con el registro de cifras.

## 3. Mensajes que los datos sostienen

- La producción de petróleo de Vaca Muerta fue de 633.371 bbl/día en junio de 2026 (solo no convencional), 33,0% más que un año antes.
- Casi todo el petróleo de Vaca Muerta es no convencional: 99,88% del volumen de 2022–2025.
- Los terminales neuquinos exportaron en 2025 un promedio de 166.161 bbl/día, el 28,1% de la producción de la cuenca; en 2022 era el 20,8%. El oleoducto a Chile se mide aparte.
- En 2025 la exportación neuquina queda por encima de la producción de Vaca Muerta con las tres bases del índice; en 2024 la dirección depende de la base, por eso no se afirma una tendencia.
- La concentración depende de cómo se mida: 94,25% por operador de terminal y 47,0% por cargador (2020–2025).
- Solo 44 de 83 ductos que mueven petróleo tienen capacidad utilizable; 3 superan el 100% en su tramo más cargado, sin que los datos permitan decidir si es sobrecarga o capacidad mal informada.

## 4. Lo que NO se puede decir

- Que la exportación de la planilla 21 sea "de Vaca Muerta": solo el 62,2% del volumen total es crudo neuquino.
- Cualquier cifra de utilización de VMOC: se retiró (decisión D2).
- Una tendencia entre exportación y producción en 2023–2024: cambia de signo con la base.
- Una causa para la volatilidad de la exportación.
- Valores en USD, producción de la cuenca antes de 2022 o producción convencional de 2026.

## 5. Hallazgos de la auditoría (F1–F19), una línea cada uno

- **F1.** La exportación de la planilla 21 incluía terminales de todo el país; se pasó a terminales neuquinos y el índice a base 2022 con sensibilidad.
- **F2.** La utilización de ductos sumaba gas y segmentos en serie; ahora usa líquidos y el tramo más cargado. Se retiró la cifra de VMOC.
- **F3.** Se excluían 6 ductos completos por un supuesto error de carga que en 3 casos era gas en el numerador; ahora se excluye por ducto-año con reglas explícitas.
- **F4.** El conteo "con capacidad / sin capacidad" mezclaba universos; ahora se parte de los 83 ductos que mueven petróleo.
- **F5.** El rótulo de capacidad válida solo exigía un valor mayor a cero; se agregaron reglas de capacidad dudosa y se cambió el rótulo.
- **F6.** Había producción de 2026 en los datos crudos sin usar; se incorporó la de junio como no convencional y se rotuló su alcance.
- **F7.** El volumen sin país identificado (28,0%) no figuraba en el HTML; ahora se muestra y se conserva la etiqueta original.
- **F8.** La concentración por operador de terminal se presentaba como concentración de exportadores; se publican ambas medidas.
- **F9.** "Convencional desde 2022" era un artefacto de los archivos cargados; ahora figura como "sin dato" antes de 2022.
- **F10.** Frases que afirmaban más de lo que muestran los datos; se reescribieron y una prueba vigila las palabras prohibidas.
- **F11.** Años parciales sin rotular; 2018 y 2026 quedan marcados y fuera de los gráficos anuales.
- **F12.** Medidas DAX con defectos (signo del Balance, filtros sobre tablas); corregidas o retiradas.
- **F13.** Volumen repetido por tramo en la planilla 20; se eliminó el doble conteo. En la planilla 21 no hay evidencia suficiente y no se tocó.
- **F14.** Cobertura de exportación irregular; se eligió un año base con 12 de 12 meses y se avisa del último mes.
- **F15.** Un mismo ducto con dos identificadores; se agregó un identificador lógico sin tocar los originales.
- **F16.** Un salto citado con otro valor al recalcularlo; se corrigió.
- **F17.** Imprecisiones en documentos (conteos de pozos y ductos); corregidas.
- **F18.** Dos pozos con coordenadas dudosas; se omiten del mapa con nota al pie.
- **F19.** Cuadro de hitos de VMOS sin fuente; se elimina del reporte.

## 6. Capturas sugeridas

1. Dashboard web, encabezado y tarjetas: muestra la cifra principal con su alcance y las cuatro tarjetas.
2. Dashboard web, índices base 2022 con las dos tablas (promedios anuales y sensibilidad): muestra que la dirección cambia con la base y cómo se evita una conclusión.
3. Dashboard web, ranking de utilización de ductos con la nota de cobertura: muestra el criterio de exclusión.
4. Dashboard web, concentración por operador de terminal frente a cargador: muestra por qué una misma cifra puede leerse de dos maneras.
5. Power BI, página 3 (índices base 2022) y página 4 (capacidad informada): muestra el modelo corregido.
6. Salida de la suite de pruebas pasando: muestra el control automático de cifras y textos.

## 7. Preguntas que puede hacer un entrevistador

- Por qué la exportación se mide por terminales y no por país o por empresa (alcance, proxy y limitación).
- Por qué el año base es 2022 y qué cambia con 2021 o 2023.
- Por qué no se publica la utilización de VMOC.
- Cómo se evita que un texto contenga una cifra equivocada (registro de cifras y pruebas).
- Qué quedó fuera: producción de la cuenca antes de 2022, USD, convencional de 2026.

## 8. Registro de cifras finales

| Clave | Valor | Unidad | Alcance |
|---|---|---|---|
| `prod_ultimo_mes_bbl_dia` | 633.371 | bbl/dia | jun-2026, solo no convencional (el convencional de 2026 no esta en las fuentes cargadas) |
| `prod_var_interanual_pct` | 33,00 | % | jun-2026 vs jun-2025, ambos solo no convencional |
| `prod_vm_dic2025_bbl_dia` | 590.755 | bbl/dia | dic-2025, Vaca Muerta convencional + no convencional |
| `prod_var_dic2025_pct` | 31,92 | % | dic-2025 vs dic-2024, Vaca Muerta |
| `pct_nc_2022_2025` | 99,88 | % | volumen de petroleo de Vaca Muerta 2022-2025 (unico periodo con convencional observable) |
| `prod_acum_2006_2025_bbl` | 722.439.535 | bbl | Vaca Muerta, 2006-2025, fuentes cargadas |
| `yacimientos_n` | 146 | yacimientos | Vaca Muerta, fuentes cargadas |
| `yac_top1_bbl_dia` | 31.386 | bbl/dia | BAJADA DEL PALO OESTE, promedio de los meses con dato del yacimiento |
| `pct_conv_min_2022_2025` | 0,08 | % | convencional / total de Vaca Muerta, anual 2022-2025 |
| `pct_conv_max_2022_2025` | 0,20 | % | convencional / total de Vaca Muerta, anual 2022-2025 |
| `conv_2022_bbl` | 173.590 | bbl | produccion convencional de Vaca Muerta, 2022 |
| `pozos_nc_con_coordenadas` | 3.062 | pozos | pozos no convencionales con coordenadas en la fuente |
| `pozos_mapa_omitidos` | 2 | pozos | coordenada a mas de 30 km de la mediana de su yacimiento |
| `pozos_mapa` | 3.060 | pozos | pozos dibujados en el mapa |
| `pozos_omitidos_pct_prod` | 0,07 | % | produccion acumulada de los pozos omitidos / total |
| `prod_cuenca_2022_bbl_dia` | 352.235 | bbl/dia | 2022, produccion total de petroleo de la cuenca Neuquina, solo 2022-2025 (archivos anuales + no convencional historico) |
| `prod_vm_2022_bbl_dia` | 243.237 | bbl/dia | 2022, Vaca Muerta |
| `exp_neu_2022_bbl_dia` | 73.201 | bbl/dia | 2022, promedio de 12 meses, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `pct_exp_cuenca_2022` | 20,78 | % | 2022: exportacion de terminales neuquinos / produccion total de petroleo de la cuenca Neuquina, solo 2022-2025 (archivos anuales + no convencional historico) |
| `pct_exp_vm_2022` | 30,09 | % | 2022: exportacion de terminales neuquinos / produccion de Vaca Muerta |
| `vm_sobre_cuenca_2022` | 69,06 | % | 2022: Vaca Muerta / cuenca Neuquina |
| `idx_exp_2022_base2021` | 258,18 | indice | promedio anual 2022, base 2021 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2022_base2021` | 149,58 | indice | promedio anual 2022, base 2021 = 100 (produccion de Vaca Muerta) |
| `idx_exp_2022_base2022` | 100,00 | indice | promedio anual 2022, base 2022 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2022_base2022` | 100,00 | indice | promedio anual 2022, base 2022 = 100 (produccion de Vaca Muerta) |
| `idx_cuenca_2022_base2022` | 100,00 | indice | promedio anual 2022, base 2022 = 100 (produccion de la cuenca) |
| `idx_exp_2022_base2023` | 92,03 | indice | promedio anual 2022, base 2023 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2022_base2023` | 79,48 | indice | promedio anual 2022, base 2023 = 100 (produccion de Vaca Muerta) |
| `idx_cuenca_2022_base2023` | 85,78 | indice | promedio anual 2022, base 2023 = 100 (produccion de la cuenca) |
| `prod_cuenca_2023_bbl_dia` | 410.640 | bbl/dia | 2023, produccion total de petroleo de la cuenca Neuquina, solo 2022-2025 (archivos anuales + no convencional historico) |
| `prod_vm_2023_bbl_dia` | 306.023 | bbl/dia | 2023, Vaca Muerta |
| `exp_neu_2023_bbl_dia` | 79.536 | bbl/dia | 2023, promedio de 12 meses, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `pct_exp_cuenca_2023` | 19,37 | % | 2023: exportacion de terminales neuquinos / produccion total de petroleo de la cuenca Neuquina, solo 2022-2025 (archivos anuales + no convencional historico) |
| `pct_exp_vm_2023` | 25,99 | % | 2023: exportacion de terminales neuquinos / produccion de Vaca Muerta |
| `vm_sobre_cuenca_2023` | 74,52 | % | 2023: Vaca Muerta / cuenca Neuquina |
| `idx_exp_2023_base2021` | 280,52 | indice | promedio anual 2023, base 2021 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2023_base2021` | 188,19 | indice | promedio anual 2023, base 2021 = 100 (produccion de Vaca Muerta) |
| `idx_exp_2023_base2022` | 108,65 | indice | promedio anual 2023, base 2022 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2023_base2022` | 125,81 | indice | promedio anual 2023, base 2022 = 100 (produccion de Vaca Muerta) |
| `idx_cuenca_2023_base2022` | 116,58 | indice | promedio anual 2023, base 2022 = 100 (produccion de la cuenca) |
| `idx_exp_2023_base2023` | 100,00 | indice | promedio anual 2023, base 2023 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2023_base2023` | 100,00 | indice | promedio anual 2023, base 2023 = 100 (produccion de Vaca Muerta) |
| `idx_cuenca_2023_base2023` | 100,00 | indice | promedio anual 2023, base 2023 = 100 (produccion de la cuenca) |
| `prod_cuenca_2024_bbl_dia` | 486.549 | bbl/dia | 2024, produccion total de petroleo de la cuenca Neuquina, solo 2022-2025 (archivos anuales + no convencional historico) |
| `prod_vm_2024_bbl_dia` | 387.221 | bbl/dia | 2024, Vaca Muerta |
| `exp_neu_2024_bbl_dia` | 88.782 | bbl/dia | 2024, promedio de 12 meses, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `pct_exp_cuenca_2024` | 18,25 | % | 2024: exportacion de terminales neuquinos / produccion total de petroleo de la cuenca Neuquina, solo 2022-2025 (archivos anuales + no convencional historico) |
| `pct_exp_vm_2024` | 22,93 | % | 2024: exportacion de terminales neuquinos / produccion de Vaca Muerta |
| `vm_sobre_cuenca_2024` | 79,58 | % | 2024: Vaca Muerta / cuenca Neuquina |
| `idx_exp_2024_base2021` | 313,13 | indice | promedio anual 2024, base 2021 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2024_base2021` | 238,13 | indice | promedio anual 2024, base 2021 = 100 (produccion de Vaca Muerta) |
| `idx_exp_2024_base2022` | 121,28 | indice | promedio anual 2024, base 2022 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2024_base2022` | 159,19 | indice | promedio anual 2024, base 2022 = 100 (produccion de Vaca Muerta) |
| `idx_cuenca_2024_base2022` | 138,13 | indice | promedio anual 2024, base 2022 = 100 (produccion de la cuenca) |
| `idx_exp_2024_base2023` | 111,62 | indice | promedio anual 2024, base 2023 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2024_base2023` | 126,53 | indice | promedio anual 2024, base 2023 = 100 (produccion de Vaca Muerta) |
| `idx_cuenca_2024_base2023` | 118,49 | indice | promedio anual 2024, base 2023 = 100 (produccion de la cuenca) |
| `prod_cuenca_2025_bbl_dia` | 592.113 | bbl/dia | 2025, produccion total de petroleo de la cuenca Neuquina, solo 2022-2025 (archivos anuales + no convencional historico) |
| `prod_vm_2025_bbl_dia` | 501.956 | bbl/dia | 2025, Vaca Muerta |
| `exp_neu_2025_bbl_dia` | 166.161 | bbl/dia | 2025, promedio de 12 meses, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `pct_exp_cuenca_2025` | 28,06 | % | 2025: exportacion de terminales neuquinos / produccion total de petroleo de la cuenca Neuquina, solo 2022-2025 (archivos anuales + no convencional historico) |
| `pct_exp_vm_2025` | 33,10 | % | 2025: exportacion de terminales neuquinos / produccion de Vaca Muerta |
| `vm_sobre_cuenca_2025` | 84,77 | % | 2025: Vaca Muerta / cuenca Neuquina |
| `idx_exp_2025_base2021` | 586,04 | indice | promedio anual 2025, base 2021 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2025_base2021` | 308,68 | indice | promedio anual 2025, base 2021 = 100 (produccion de Vaca Muerta) |
| `idx_exp_2025_base2022` | 226,99 | indice | promedio anual 2025, base 2022 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2025_base2022` | 206,37 | indice | promedio anual 2025, base 2022 = 100 (produccion de Vaca Muerta) |
| `idx_cuenca_2025_base2022` | 168,10 | indice | promedio anual 2025, base 2022 = 100 (produccion de la cuenca) |
| `idx_exp_2025_base2023` | 208,91 | indice | promedio anual 2025, base 2023 = 100 (exportacion neuquina por terminales) |
| `idx_vm_2025_base2023` | 164,03 | indice | promedio anual 2025, base 2023 = 100 (produccion de Vaca Muerta) |
| `idx_cuenca_2025_base2023` | 144,19 | indice | promedio anual 2025, base 2023 = 100 (produccion de la cuenca) |
| `anio_base_indice` | 2.022 | anio | primer anio con 12 de 12 meses de exportacion neuquina y exportacion >= 10% de la produccion de Vaca Muerta |
| `ma12_exp_dic2023` | 108,82 | indice | media movil 12m a dic-2023, base 2022, exportacion neuquina por terminales |
| `ma12_vm_dic2023` | 125,78 | indice | media movil 12m a dic-2023, base 2022, produccion de Vaca Muerta |
| `ma12_cuenca_dic2023` | 116,56 | indice | media movil 12m a dic-2023, base 2022, produccion de la cuenca |
| `ma12_exp_dic2024` | 121,42 | indice | media movil 12m a dic-2024, base 2022, exportacion neuquina por terminales |
| `ma12_vm_dic2024` | 159,13 | indice | media movil 12m a dic-2024, base 2022, produccion de Vaca Muerta |
| `ma12_cuenca_dic2024` | 138,09 | indice | media movil 12m a dic-2024, base 2022, produccion de la cuenca |
| `ma12_exp_dic2025` | 226,53 | indice | media movil 12m a dic-2025, base 2022, exportacion neuquina por terminales |
| `ma12_vm_dic2025` | 206,21 | indice | media movil 12m a dic-2025, base 2022, produccion de Vaca Muerta |
| `ma12_cuenca_dic2025` | 168,00 | indice | media movil 12m a dic-2025, base 2022, produccion de la cuenca |
| `chile_2023_bbl_dia` | 35.039 | bbl/dia | 2023: oleoducto Puesto Hernandez - Buta Mallin (planilla 20), promedio de los 8 meses con dato; serie aparte |
| `chile_2023_meses` | 8 | meses | 2023: meses con dato del oleoducto a Chile |
| `chile_2024_bbl_dia` | 71.020 | bbl/dia | 2024: oleoducto Puesto Hernandez - Buta Mallin (planilla 20), promedio de los 12 meses con dato; serie aparte |
| `chile_2024_meses` | 12 | meses | 2024: meses con dato del oleoducto a Chile |
| `chile_2025_bbl_dia` | 79.998 | bbl/dia | 2025: oleoducto Puesto Hernandez - Buta Mallin (planilla 20), promedio de los 12 meses con dato; serie aparte |
| `chile_2025_meses` | 12 | meses | 2025: meses con dato del oleoducto a Chile |
| `pct_exp_cuenca_con_chile_2024` | 32,84 | % | 2024: (terminales neuquinos + oleoducto a Chile) / produccion de la cuenca; solo como referencia |
| `pct_exp_cuenca_con_chile_2025` | 41,57 | % | 2025: (terminales neuquinos + oleoducto a Chile) / produccion de la cuenca; solo como referencia |
| `exp_neu_ultimo_mes_bbl_dia` | 258.874 | bbl/dia | jun-2026, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `exp_neu_ultimo_mes_m3` | 1.234.735 | m3 | jun-2026, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `exp_nacional_total_m3` | 53.755.750 | m3 | 2018-jun 2026, 6 operadores de terminal de todo el pais (planilla 21) |
| `exp_neuquina_total_m3` | 33.414.168 | m3 | 2018-jun 2026, Oiltanking + Refineria Bahia Blanca |
| `exp_neuquina_pct_del_nacional` | 62,16 | % | volumen neuquino / volumen de los 6 operadores, 2018-jun 2026 |
| `sin_pais_pct` | 27,99 | % | volumen con pais NO IDENTIFICADO / volumen de los 6 operadores, 2018-jun 2026 (100% TERMAP) |
| `con_pais_pct` | 72,01 | % | volumen con pais identificado / volumen de los 6 operadores, 2018-jun 2026 |
| `sin_pais_m3` | 15.044.986 | m3 | 2018-jun 2026, 6 operadores |
| `termap_pct_2019` | 78,87 | % | TERMAP / total de los 6 operadores, 2019 |
| `termap_pct_2026` | 3,73 | % | TERMAP / total de los 6 operadores, ene-jun 2026 |
| `conc_top3_operadores_pct` | 94,25 | % | 2020-2025, 3 mayores operadores de terminal / 6 operadores (no es concentracion de exportadores) |
| `conc_op1_pct` | 61,08 | % | 2020-2025, operador de terminal n.1 (Oiltanking EBYTEM S.A.) / total de los operadores |
| `conc_op2_pct` | 27,94 | % | 2020-2025, operador de terminal n.2 (TERMAP S.A.) / total de los operadores |
| `conc_op3_pct` | 5,23 | % | 2020-2025, operador de terminal n.3 (COMPAÑÍA GENERAL DE COMBUSTIBLES S.A.) / total de los operadores |
| `conc_top3_cargadores_pct` | 47,02 | % | 2020-2025, 3 mayores cargadores (quien exporta, agrupando variantes de nombre) / total de los 6 operadores |
| `vol_mensual_exp_neu_pct` | 34,02 | % | desvio estandar de la variacion mensual, 2022-2025, exportacion neuquina por terminales |
| `vol_mensual_prod_vm_pct` | 2,55 | % | desvio estandar de la variacion mensual, 2022-2025, produccion de Vaca Muerta |
| `vol_ratio` | 13,34 | veces | cociente de los dos desvios anteriores |
| `vol_mensual_exp_nac_pct` | 76,85 | % | 2020-2025, exportacion de los 6 operadores de todo el pais (contexto) |
| `ductos_petroleo_n` | 83 | ductos | ductos logicos con volumen de petroleo > 0 en la planilla 20 (los dos id del mismo ducto cuentan una vez) |
| `ductos_ranking_n` | 44 | ductos | ductos de petroleo con capacidad informada valida tras las reglas R1, R3, R4, R5 y D2 |
| `ductos_sin_capacidad_n` | 34 | ductos | ductos de petroleo sin fila en el Anexo 2A |
| `ductos_cap_dudosa_todos_n` | 5 | ductos | ductos de petroleo con capacidad dudosa en todos los anios |
| `ductos_sin_cap_utilizable_n` | 39 | ductos | ductos de petroleo sin capacidad utilizable (sin Anexo 2A o dudosa en todos los anios) |
| `ductos_sobre_100_n` | 3 | ductos | ductos del ranking con utilizacion del segmento mas cargado > 100% en su anio mas reciente valido |
| `ductos_ranking_parcial_n` | 7 | ductos | ductos del ranking cuyo anio mas reciente tiene menos de 12 meses |
| `ductos_ranking_a_revisar_n` | 4 | ductos | ductos del ranking marcados a revisar (R2 o R6) |
| `ducto_anios_excluidos_n` | 36 | ducto-anios | ducto-anios con capacidad dudosa presentes en el modelo |
| `ductos_con_anio_excluido_n` | 18 | ductos | ductos con al menos un anio excluido |
| `regla_r1_veces` | 5,00 | veces | R1: salto de la capacidad operativa entre anios consecutivos |
| `regla_r3_veces` | 2,00 | veces | R3: caudal liquido observado / capacidad empleada informada |
| `regla_r5_dias` | 90 | dias | R5: dias operativos informados en el Anexo 2A |
| `ducto_sobre100_1_pct` | 129,70 | % | Allen - Puerto Rosales 2024 (12 meses), segmento mas cargado de liquidos / capacidad operativa informada |
| `ducto_sobre100_2_pct` | 111,10 | % | LINDERO ATRAVESADO- CENTENARIO 2023 (2 meses), segmento mas cargado de liquidos / capacidad operativa informada |
| `ducto_sobre100_3_pct` | 106,90 | % | Centenario - Allen L14 2024 (12 meses), segmento mas cargado de liquidos / capacidad operativa informada |
| `cobertura_capacidad_ducto_mes_pct` | 45,38 | % | ducto-mes con fila en el Anexo 2A / ducto-mes con transporte (todos los productos) |
| `cobertura_capacidad_ducto_anio_pct` | 39,81 | % | ducto-anio con capacidad operativa > 0 / ducto-anio con transporte (todos los productos) |
| `hallazgos_n` | 19 | hallazgos | auditoria de 2026-10-05, F1 a F19 |
| `bbl_por_m3` | 6,29 | bbl/m3 | factor de conversion usado en todo el proyecto |
| `umbral_km` | 30 | km | script 13: distancia a la mediana de las coordenadas de su yacimiento a partir de la cual se omite un pozo del mapa |
| `umbral_exp_pct` | 10 | % | script 11: exportacion / produccion de Vaca Muerta minima para elegir el anio base del indice |
| `operadores_n` | 6 | operadores | operadores de terminal en la planilla 21 |
