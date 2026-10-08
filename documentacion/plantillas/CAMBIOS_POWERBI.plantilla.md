# Cambios a aplicar en el reporte de Power BI

Este documento lista, página por página, qué títulos, textos, filtros y medidas cambian en `ProyectoShale.pbix` para que coincida con las correcciones de la auditoría y con la serie principal de exportación (comercio exterior). Los valores esperados salen de `data/web/registro_cifras.json` (el mismo registro que usan el README y el dashboard web).

**Qué no se pudo verificar.** Estos cambios no se ejecutaron en Power BI Desktop ni se contrastaron con el modelo real: no hay un `.pbit` para leer las medidas y relaciones. Cada medida nueva figura como NO VERIFICADO hasta que el valor que muestre Power BI coincida con el valor esperado de esta guía. Si un valor no coincide, no sigas: avisá cuál fue y qué mostró.

**Por qué las tarjetas de producción cierran en diciembre de 2025.** El modelo se alimenta de las tablas limpias de producción por pozo, que llegan hasta diciembre de 2025. La versión web suma además junio de 2026 (solo no convencional) leído directo de los datos crudos. Las dos versiones comparten el registro de cifras; cada tarjeta declara su fecha.

## Paso 0. Preparación (una sola vez)

1. En **Inicio > Transformar datos > Administrar parámetros**, apuntar `RutaClean` a la carpeta de las tablas limpias corregidas (`clean_corregido` del proyecto, o la carpeta que indique `VM_CLEAN_DIR`), con la barra final (por ejemplo `D:\datos\clean_corregido\`). Antes hay que correr el script 16 (`scripts/16_comercio_exterior.py`), que crea `fact_exportacion_crudo_comex.csv` y `produccion_cuenca_oficial_mensual.csv` en esa carpeta.
2. **Inicio > Nueva fuente > Consulta en blanco** (dos veces) y pegar, en el **Editor avanzado**, los bloques 13 y 14 de `powerbi/power_query_m.md`; nombrarlas `Fact_ExportacionComex` y `Fact_ProduccionCuenca`.
3. **Inicio > Actualizar**. Control: la suma de `prod_pet_bbl` en `Fact_Produccion` tiene que dar {{prod_acum_2006_2025_bbl:0}}. En `Fact_ExportacionComex` tienen que figurar {{comex_registros_n:0}} filas. Si algo da otro valor, parar y avisar.
4. **Vista de modelo**: crear dos relaciones, `Fact_ExportacionComex[fecha]` con `Dim_Fecha[fecha]` y `Fact_ProduccionCuenca[fecha]` con `Dim_Fecha[fecha]`, de muchos a uno, dirección única. Después, en **Inicio > Transformar datos**, abrir la consulta `Dim_Fecha` > **Editor avanzado** y reemplazar su código por el bloque 10 actualizado de `powerbi/power_query_m.md` (ahora incluye las dos tablas nuevas en el rango de fechas); **Cerrar y aplicar**. Confirmar que `Dim_Ducto[idducto]` sigue relacionada con `Fact_CapacidadDuctos[idducto]` y con `Fact_TransporteDuctos[idducto]`.
5. En **Modelado > Nueva medida**, agregar las medidas del Grupo E de `powerbi/dax_measures.md`: `Dias del Periodo`, `Volumen Exportado Cuenca`, `Monto Exportado Cuenca (USD)`, `Precio Implicito (USD-bbl)`, `Exportacion Cuenca (bbl-dia)`, `Produccion Cuenca (bbl-dia)`, `% Exportado de la Cuenca`, los índices base 2022 y de media móvil, `% Exportado por Empresa Exportadora`, `Volumen Terminales Neuquinos (contraste)` y `Utilizacion % (anio mas reciente valido)`.
6. Agregar también esta medida:

```dax
% Produccion No Convencional 2022-2025 =
VAR NC = CALCULATE([Prod Petroleo (bbl-dia)], Fact_Produccion[tipo_de_recurso] = "NO CONVENCIONAL", Dim_Fecha[anio] >= 2022, Dim_Fecha[anio] <= 2025)
VAR Total = CALCULATE([Prod Petroleo (bbl-dia)], Dim_Fecha[anio] >= 2022, Dim_Fecha[anio] <= 2025)
RETURN DIVIDE(NC, Total)
```

7. **Control de las medidas nuevas** antes de tocar las páginas: en una tabla temporal con `Dim_Fecha[anio]` en filas, `Volumen Exportado Cuenca` tiene que dar {{exp_2022_m3:0}} (2022) y {{exp_2025_m3:0}} (2025), y `Monto Exportado Cuenca (USD)` USD {{exp_2025_usd_millones:0}} millones en 2025. Si no coinciden, parar.

## Página 1 — Vaca Muerta: de la cuenca al mundo (resumen)

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Tarjeta `% Produccion No Convencional` | título "% Produccion No Convencional", medida histórica | título "Incidencia no convencional, 2022–2025"; medida `% Produccion No Convencional 2022-2025` | {{pct_nc_2022_2025:2}}% |
| Tarjeta `Prod Petroleo (bbl-dia) - Ultimo Mes` | título igual al nombre de la medida | título "Producción de petróleo, dic-2025 (bbl/día)" | {{prod_vm_dic2025_bbl_dia:1}} |
| Tarjeta `Var Interanual Prod - Ultimo Mes` | título igual al nombre de la medida | título "Variación interanual, dic-2025 vs dic-2024" | {{prod_var_dic2025_pct:2}}% |
| Tarjeta `Volumen Exportado - Ultimo Mes` (m³ del último mes, todas las terminales) | volumen nacional del último mes | reemplazar por la medida `Exportacion Cuenca (bbl-dia)` con filtro del objeto visual `Dim_Fecha[anio]` = 2025; título "Exportación de crudo de la cuenca, 2025 (bbl/día, comercio exterior)" | {{exp_2025_bbl_dia:0}} |
| Cuadro de texto nuevo (debajo de las tarjetas) | — | "El modelo de producción cierra en diciembre de 2025. La versión web suma junio de 2026 (solo no convencional): {{prod_ultimo_mes_bbl_dia:0}} bbl/día, +{{prod_var_interanual_pct:1}}% interanual." | — |

## Página 2 — Acto I · Producción: de dónde sale el petróleo

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Mapa (ArcGIS) | todos los pozos con coordenadas | filtro del objeto visual en `Dim_PozoCoordenadas[idpozo]`: excluir los pozos 153751 y 159086 (coordenada a más de {{umbral_km:0}} km de la mediana de su yacimiento) | {{pozos_mapa:0}} pozos dibujados |
| Cuadro de texto del mapa | "Mapa limitado a pozos no convencionales. Los pozos convencionales de Vaca Muerta no tienen coordenadas en la fuente" | "Mapa limitado a pozos no convencionales ({{pozos_mapa:0}} de {{pozos_nc_con_coordenadas:0}}). Se omiten {{pozos_mapa_omitidos:0}} pozos con coordenadas dudosas, que juntos suman {{pozos_omitidos_pct_prod:3}}% de la producción acumulada. Los convencionales no tienen coordenadas en la fuente." | — |
| Tabla de yacimientos | sin título | título "bbl/día, promedio de los meses con datos de cada yacimiento" | primero: {{yac_top1_bbl_dia:1}} (Bajada del Palo Oeste) |

<!--SIN_CIFRAS-->
Los identificadores de pozo a excluir son 153751 y 159086 (`data/web/pozos_coordenadas_dudosas.csv`).
<!--/SIN_CIFRAS-->

## Página 3 — "Producción vs. exportación: la brecha se sostiene y crece desde 2023" pasa a "Producción y exportación: índices base 2022"

| Elemento | Antes | Después |
|---|---|---|
| Título de la página y cuadro de texto superior | "Producción vs. exportación: la brecha se sostiene y crece desde 2023" | "Producción y exportación: índices base {{anio_base_indice:y}}" |
| Gráfico de líneas | "Índice de producción vs. exportación (base 100 = promedio 2019)", medidas `Indice Produccion (base 100)` e `Indice Exportacion (base 100)` | título "Índices de producción de la cuenca, de Vaca Muerta y de exportación de crudo de la cuenca (media móvil de 12 meses, base {{anio_base_indice:y}} = 100)"; medidas `Indice Exportacion Cuenca MA12 (base 2022)`, `Indice Produccion Cuenca MA12 (base 2022)` e `Indice Produccion VM MA12 (base 2022)`; sin filtro de año en el gráfico |
| Cuadro de texto "Metodología / El hallazgo / Una limitación" | base 2019, "brecha ≥ 120 puntos desde 2023", +1.660% | ver texto de abajo |
| Tabla nueva (matriz) | — | `Dim_Fecha[anio]` en filas (2022 a 2025), medidas `Indice Exportacion Cuenca (base 2022)`, `Indice Produccion Cuenca (base 2022)` e `Indice Produccion VM (base 2022)` |

Valores esperados de la matriz (promedios anuales, base {{anio_base_indice:y}} = 100), en el orden exportación / producción de la cuenca / producción de Vaca Muerta: 2022 → 100,0 / 100,0 / 100,0; 2023 → {{idx_exp_2023_base2022:1}} / {{idx_cuenca_2023_base2022:1}} / {{idx_vm_2023_base2022:1}}; 2024 → {{idx_exp_2024_base2022:1}} / {{idx_cuenca_2024_base2022:1}} / {{idx_vm_2024_base2022:1}}; 2025 → {{idx_exp_2025_base2022:1}} / {{idx_cuenca_2025_base2022:1}} / {{idx_vm_2025_base2022:1}}.

Valores esperados del gráfico a diciembre de cada año (media móvil de 12 meses): exportación {{ma12_exp_dic2023:1}} (2023), {{ma12_exp_dic2024:1}} (2024), {{ma12_exp_dic2025:1}} (2025); producción de la cuenca {{ma12_cuenca_dic2023:1}}, {{ma12_cuenca_dic2024:1}} y {{ma12_cuenca_dic2025:1}}; producción de Vaca Muerta {{ma12_vm_dic2023:1}}, {{ma12_vm_dic2024:1}} y {{ma12_vm_dic2025:1}}.

**Texto nuevo del cuadro:**

> **Metodología.** Los índices parten de 100 = promedio de {{anio_base_indice:y}}, el primer año con exportación en 12 de 12 meses y con exportación igual o mayor al {{umbral_exp_pct:0}}% de la producción de la cuenca. La exportación es la de crudo de la cuenca Neuquina según comercio exterior declarado, y la producción de la cuenca es la serie oficial. La curva usa media móvil de 12 meses y empieza cuando hay 12 meses de datos.
> **Qué se puede afirmar.** Con las bases 2021, 2022 y 2023, la exportación de la cuenca crece más que la producción de la cuenca en cada año posterior a la base. Esa lectura es de la serie de comercio exterior: con la de terminales marítimos, la dirección en 2024 cambia según la base.
> **Una limitación.** Antes de 2022 hay meses sin exportación declarada (cuentan como cero), y en septiembre de 2024 la producción de Vaca Muerta por pozo queda por debajo del agregado oficial; la producción de la cuenca usa la serie oficial.

## Página 4 — Acto II · Transporte

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Título de la página | "Acto II · Transporte: ductos que superan el 100% de su capacidad informada" | "Acto II · Transporte: capacidad informada de los ductos" | — |
| Gráfico de barras de utilización | medida `Utilizacion %`, ejes sin Top N | medida `Utilizacion % (anio mas reciente valido)`; eje `Dim_Ducto[denominacion_logica]`; filtro del objeto visual `Tiene Capacidad No Dudosa` = 1; Top N = 20 por esa medida; título "Utilización del tramo más cargado (año más reciente válido; 100% = capacidad operativa informada)" | {{ductos_sobre_100_n:0}} barras sobre 100%: {{LISTA_SOBRE_100}} |
| Gráfico de respaldo | título "Ductos sin capacidad confiable — volumen transportado (m³)" | título "Ductos sin capacidad utilizable — volumen de petróleo transportado (m³)"; filtro `Tiene Capacidad No Dudosa` = 0 | {{ductos_sin_cap_utilizable_n:0}} ductos en total (los que no figuran en el Anexo 2A y los de capacidad dudosa todos los años) |
| Cuadro de texto inferior | "…57 tienen un dato de capacidad operativa confiable… Los otros 85…" | texto de abajo | — |
| Cuadro "Hitos de infraestructura — VMOS" | fechas y capacidades sin fuente en el proyecto | **eliminar el cuadro** (los datos no incluyen esa información y no hay fuente citada) | — |

**Texto nuevo del cuadro inferior:**

> De {{ductos_petroleo_n:0}} ductos que mueven petróleo, {{ductos_ranking_n:0}} tienen capacidad válida y entran al ranking; {{ductos_cap_dudosa_todos_n:0}} tienen capacidad dudosa en todos los años y {{ductos_sin_capacidad_n:0}} no figuran en el Anexo 2A. Se excluyen {{ducto_anios_excluidos_n:0}} ducto-años de {{ductos_con_anio_excluido_n:0}} ductos por reglas explícitas (en `data/web/ductos_capacidad_dudosa.csv`). La utilización es el volumen del tramo más cargado (solo líquidos) sobre la capacidad operativa informada; superar el 100% no permite decidir si el volumen excede la capacidad o si la capacidad informada no corresponde al tramo. {{ductos_sobre_100_a_revisar_n:0}} de los {{ductos_sobre_100_n:0}} ductos sobre 100% tienen la capacidad marcada "a revisar" (se identifican en la versión web).

## Página 5 — Acto III · Exportación: adónde va

Esta página pasa a usar `Fact_ExportacionComex` (crudo de la cuenca Neuquina) en lugar de la planilla 21 (todas las terminales del país).

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Gráfico "Principales países de destino (m³)" | `Dim_Pais[pais]` y `Volumen Exportado` | eje `Fact_ExportacionComex[pais]`, medida `Volumen Exportado Cuenca`, Top N = 10 excluyendo "no aplica"; título "Principales países de destino (m³): crudo de la cuenca Neuquina, 2020 – agosto 2026" | primero Estados Unidos ({{comex_eeuu_pct:1}}% del volumen) y segundo Chile ({{comex_chile_pct:1}}%) |
| Tarjeta "Exportación con país de destino registrado" | 72,01% (planilla 21) | cambiar por una tarjeta con el % de volumen sin país ("no aplica") de `Fact_ExportacionComex`; título "Exportación sin país de destino ('no aplica')" | {{comex_sin_pais_pct:1}}% |
| Cuadro de texto junto a la tarjeta | — | "El comercio exterior declara el destino de casi todo el volumen; el {{comex_sin_pais_pct:1}}% figura como 'no aplica'." | — |
| Gráfico de líneas "Evolución anual de exportación, top 5 países" | incluye 2018 y 2026 (planilla 21) | eje `Dim_Fecha[anio]`, leyenda `Fact_ExportacionComex[pais]`, medida `Volumen Exportado Cuenca`, filtro `Dim_Fecha[anio]` entre 2020 y 2025; título "Evolución anual de exportación, top 5 países, 2020–2025 (en 2020 hay exportación en {{exp_2020_meses:0}} de 12 meses)" | — |
| Tabla nueva | — | `Dim_Fecha[anio]` en filas (2020 a 2025), medidas `Volumen Exportado Cuenca`, `Monto Exportado Cuenca (USD)` y `Precio Implicito (USD-bbl)`; título "Valor de la exportación (USD, monto FOB declarado)" | 2025: USD {{exp_2025_usd_millones:0}} millones y {{exp_2025_usd_bbl:1}} USD/bbl; 2022: USD {{exp_2022_usd_millones:0}} millones y {{exp_2022_usd_bbl:1}} USD/bbl |

## Página 6 — "Concentración por empresa" pasa a "Acto III · Exportación: quién la despacha"

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Título (cuadro de texto) | "Acto III · Exportación: quién la despacha y por qué es tan irregular" | "Acto III · Exportación: quién la despacha" | — |
| Cuadro "~94% del volumen exportado…" | "~94% del volumen exportado 2020-2025 pasa por solo 3 empresas/terminales" | "Las 3 mayores empresas exportadoras de crudo de la cuenca concentran {{conc_exp_top3_pct:1}}% del volumen 2020–2025 (agrupando las variantes de razón social de una misma empresa). Por operador de terminal de todo el país (planilla 21), los 3 mayores concentran {{conc_top3_operadores_pct:2}}%. Son medidas distintas." | — |
| Gráfico de barras de participación | "Participación en el volumen exportado, 2020–2025" por operador de terminal | eje `Fact_ExportacionComex[empresa]`, medida `% Exportado por Empresa Exportadora`, filtro `Dim_Fecha[anio]` entre 2020 y 2025, Top N = 6; título "Participación por empresa exportadora en el volumen de crudo de la cuenca, 2020–2025" | primera empresa (agrupada): {{conc_exp_top1_pct:1}}%; sin agrupar, las 3 primeras suman {{conc_exp_top3_sin_agrupar_pct:1}}% |
| Cuadro "~15× más volátil…" | "~15× … 2020-2025" | "{{vol_ratio:1}}×: la exportación de crudo de la cuenca varía más mes a mes que la producción de la cuenca (desvío estándar de la variación mensual 2022–2025: {{vol_exp_pct:1}}% frente a {{vol_cuenca_pct:1}}%)" | — |
| Cuadro "Esta volatilidad es consistente con la fuerte concentración…" | sugiere asociación con la concentración | "Es una descripción de la diferencia, sin causa atribuida. El cociente cambia con la ventana elegida." | — |
| Gráfico de líneas "Volumen exportado por mes (m³)" | todas las terminales, planilla 21 | medida `Volumen Exportado Cuenca` por mes; título "Volumen exportado por mes (m³), crudo de la cuenca (comercio exterior)" | — |
| Cuadro de texto nuevo (contraste) | — | "Las fuentes oficiales de exportación no concilian desde 2023: el comercio exterior queda entre {{contr_comex_sobre_term_mas_oleo_2024:2}} y {{contr_comex_sobre_term_mas_oleo_2023:2}} veces los terminales marítimos más el oleoducto a Chile. Ver el panel de contraste de la versión web." | — |

## Paso final

1. **Archivo > Guardar como** `ProyectoShale.pbix` (el mismo nombre).
2. **Archivo > Exportar > Plantilla de Power BI** y guardar `ProyectoShale.pbit`. Con ese archivo se pueden verificar las medidas DAX reales y relaciones.
3. Devolver: (a) los valores que mostró cada tarjeta y la matriz de la página 3, (b) los valores de la tabla de USD de la página 5, (c) cuántas barras hay sobre 100% en la página 4 y sus valores, (d) el `.pbit`.
