# Cambios a aplicar en el reporte de Power BI

Este documento lista, página por página, qué títulos, textos, filtros y medidas cambian en `ProyectoShale.pbix` para que coincida con las correcciones de la auditoría. Los valores esperados salen de `data/web/registro_cifras.json` (el mismo registro que usan el README y el dashboard web).

**Qué no se pudo verificar.** Estos cambios no se ejecutaron en Power BI Desktop ni se contrastaron con el modelo real: no hay un `.pbit` para leer las medidas y relaciones. Cada medida nueva figura como NO VERIFICADO hasta que el valor que muestre Power BI coincida con el valor esperado de esta guía. Si un valor no coincide, no sigas: avisá cuál fue y qué mostró.

**Por qué las tarjetas de Power BI cierran en diciembre de 2025.** El modelo se alimenta de las tablas limpias, que llegan hasta diciembre de 2025. La versión web suma además junio de 2026 (solo no convencional) leído directo de los datos crudos. Las dos versiones comparten el registro de cifras; cada tarjeta declara su fecha.

## Paso 0. Preparación (una sola vez)

1. En **Inicio > Transformar datos > Administrar parámetros**, apuntar `RutaClean` a la carpeta de las tablas limpias corregidas (`clean_corregido` del proyecto, o la carpeta que indique `VM_CLEAN_DIR`).
2. **Inicio > Actualizar**. Control: la suma de `prod_pet_bbl` en `Fact_Produccion` tiene que dar 722.439.535. Si da otro valor, parar y avisar.
3. Si Power Query avisa de columnas nuevas o faltantes, revisar el bloque correspondiente de `powerbi/power_query_m.md` (ya trae `idducto_logico`, `denominacion_logica`, `capacidad_dudosa`, `a_revisar_capacidad`, `volumen_liquidos`, `volumen_segmento_mas_cargado`, `pais_original` y `pais_estado`).
4. **Vista de modelo**: confirmar que `Dim_Ducto[idducto]` sigue relacionada con `Fact_CapacidadDuctos[idducto]` y con `Fact_TransporteDuctos[idducto]`.
5. En **Modelado > Nueva medida**, agregar las medidas del Grupo E de `powerbi/dax_measures.md` (`Volumen Exportado Neuquino`, `Exportacion Neuquina (bbl-dia)`, `Indice Produccion VM (base 2022)`, `Indice Exportacion Neuquina (base 2022)`, `Indice Produccion VM MA12 (base 2022)`, `Indice Exportacion Neuquina MA12 (base 2022)`, `Utilizacion % (anio mas reciente valido)`) y, en la tabla de medidas, esta nueva:

```dax
% Produccion No Convencional 2022-2025 =
VAR NC = CALCULATE([Prod Petroleo (bbl-dia)], Fact_Produccion[tipo_de_recurso] = "NO CONVENCIONAL", Dim_Fecha[anio] >= 2022, Dim_Fecha[anio] <= 2025)
VAR Total = CALCULATE([Prod Petroleo (bbl-dia)], Dim_Fecha[anio] >= 2022, Dim_Fecha[anio] <= 2025)
RETURN DIVIDE(NC, Total)
```

## Página 1 — Vaca Muerta: de la cuenca al mundo (resumen)

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Tarjeta `% Produccion No Convencional` | título "% Produccion No Convencional", medida histórica | título "Incidencia no convencional, 2022–2025"; medida `% Produccion No Convencional 2022-2025` | 99,88% |
| Tarjeta `Prod Petroleo (bbl-dia) - Ultimo Mes` | título igual al nombre de la medida | título "Producción de petróleo, dic-2025 (bbl/día)" | 590.754,6 |
| Tarjeta `Var Interanual Prod - Ultimo Mes` | título igual al nombre de la medida | título "Variación interanual, dic-2025 vs dic-2024" | 31,92% |
| Tarjeta `Volumen Exportado - Ultimo Mes` (m³ del último mes, todas las terminales) | volumen nacional del último mes | reemplazar por la medida `Exportacion Neuquina (bbl-dia)` con filtro del objeto visual `Dim_Fecha[anio]` = 2025; título "Exportación de crudo neuquino, 2025 (bbl/día, terminales neuquinos)" | 166.161 |
| Cuadro de texto nuevo (debajo de las tarjetas) | — | "El modelo cierra en diciembre de 2025. La versión web suma junio de 2026 (solo no convencional): 633.371 bbl/día, +33,0% interanual." | — |

## Página 2 — Acto I · Producción: de dónde sale el petróleo

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Mapa (ArcGIS) | todos los pozos con coordenadas | filtro del objeto visual en `Dim_PozoCoordenadas[idpozo]`: excluir los pozos 153751 y 159086 (coordenada a más de 30 km de la mediana de su yacimiento) | 3.060 pozos dibujados |
| Cuadro de texto del mapa | "Mapa limitado a pozos no convencionales. Los pozos convencionales de Vaca Muerta no tienen coordenadas en la fuente" | "Mapa limitado a pozos no convencionales (3.060 de 3.062). Se omiten 2 pozos con coordenadas dudosas, que juntos suman 0,066% de la producción acumulada. Los convencionales no tienen coordenadas en la fuente." | — |
| Tabla de yacimientos | sin título | título "bbl/día, promedio de los meses con datos de cada yacimiento" | primero: 31.386,5 (Bajada del Palo Oeste) |

<!--SIN_CIFRAS-->
Los identificadores de pozo a excluir son 153751 y 159086 (`data/web/pozos_coordenadas_dudosas.csv`).
<!--/SIN_CIFRAS-->

## Página 3 — "Producción vs. exportación: la brecha se sostiene y crece desde 2023" pasa a "Producción y exportación: índices base 2022"

| Elemento | Antes | Después |
|---|---|---|
| Título de la página y cuadro de texto superior | "Producción vs. exportación: la brecha se sostiene y crece desde 2023" | "Producción y exportación: índices base 2.022" |
| Gráfico de líneas | "Índice de producción vs. exportación (base 100 = promedio 2019)", medidas `Indice Produccion (base 100)` e `Indice Exportacion (base 100)` | título "Índices de producción de Vaca Muerta y exportación neuquina por terminales (media móvil de 12 meses, base 2.022 = 100)"; medidas `Indice Produccion VM MA12 (base 2022)` e `Indice Exportacion Neuquina MA12 (base 2022)`; sin filtro de año en el gráfico |
| Cuadro de texto "Metodología / El hallazgo / Una limitación" | base 2019, "brecha ≥ 120 puntos desde 2023", +1.660% | ver texto de abajo |
| Tabla nueva (matriz) | — | `Dim_Fecha[anio]` en filas (2022 a 2025), medidas `Indice Exportacion Neuquina (base 2022)` e `Indice Produccion VM (base 2022)` |

Valores esperados de la matriz (promedios anuales, base 2.022 = 100): 2022 → 100,0 y 100,0; 2023 → 108,7 (exportación) y 125,8 (producción); 2024 → 121,3 y 159,2; 2025 → 227,0 y 206,4.

Valores esperados del gráfico a diciembre de cada año (media móvil de 12 meses): exportación 108,8 (2023), 121,4 (2024), 226,5 (2025); producción de Vaca Muerta 125,8, 159,1 y 206,2.

**Texto nuevo del cuadro:**

> **Metodología.** Los índices parten de 100 = promedio de 2.022, el primer año con exportación neuquina en 12 de 12 meses y con exportación igual o mayor al 10% de la producción de Vaca Muerta. La exportación es la de los terminales neuquinos (Oiltanking y Refinería Bahía Blanca), no la de todo el país. La curva usa media móvil de 12 meses y empieza cuando hay 12 meses de datos.
> **Qué se puede afirmar.** En 2025 la exportación neuquina queda por encima de la producción de Vaca Muerta con las bases 2021, 2022 y 2023. En 2024 la dirección cambia según la base elegida, por eso no se afirma una tendencia sostenida.
> **Una limitación.** Antes de 2022 el índice de exportación se apoya en meses con cobertura irregular; los meses sin dato no se grafican como cero.

## Página 4 — Acto II · Transporte

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Título de la página | "Acto II · Transporte: ductos que superan el 100% de su capacidad informada" | "Acto II · Transporte: capacidad informada de los ductos" | — |
| Gráfico de barras de utilización | medida `Utilizacion %`, ejes sin Top N | medida `Utilizacion % (anio mas reciente valido)`; eje `Dim_Ducto[denominacion_logica]`; filtro del objeto visual `Tiene Capacidad No Dudosa` = 1; Top N = 20 por esa medida; título "Utilización del tramo más cargado (año más reciente válido; 100% = capacidad operativa informada)" | 3 barras sobre 100%: Allen - Puerto Rosales (2024, 12 meses; a revisar) con 129,7%; LINDERO ATRAVESADO- CENTENARIO (2023, 2 meses; a revisar) con 111,1%; Centenario - Allen L14 (2024, 12 meses) con 106,9% |
| Gráfico de respaldo | título "Ductos sin capacidad confiable — volumen transportado (m³)" | título "Ductos sin capacidad utilizable — volumen de petróleo transportado (m³)"; filtro `Tiene Capacidad No Dudosa` = 0 | 39 ductos en total (los que no figuran en el Anexo 2A y los de capacidad dudosa todos los años) |
| Cuadro de texto inferior | "…57 tienen un dato de capacidad operativa confiable… Los otros 85…" | texto de abajo | — |
| Cuadro "Hitos de infraestructura — VMOS" | fechas y capacidades sin fuente en el proyecto | **eliminar el cuadro** (los datos no incluyen esa información y no hay fuente citada) | — |

**Texto nuevo del cuadro inferior:**

> De 83 ductos que mueven petróleo, 44 tienen capacidad válida y entran al ranking; 5 tienen capacidad dudosa en todos los años y 34 no figuran en el Anexo 2A. Se excluyen 36 ducto-años de 18 ductos por reglas explícitas (en `data/web/ductos_capacidad_dudosa.csv`). La utilización es el volumen del tramo más cargado (solo líquidos) sobre la capacidad operativa informada; superar el 100% no permite decidir si el volumen excede la capacidad o si la capacidad informada no corresponde al tramo. Los ductos con pocos meses de datos o marcados "a revisar" se identifican en la versión web.

## Página 5 — Acto III · Exportación: adónde va

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Gráfico "Principales países de destino (m³)" | sin alcance | título "Principales países de destino (m³): terminales de todo el país, solo volumen con país identificado" | primero: Estados Unidos |
| Tarjeta "Exportación con país de destino registrado" | 72,01% | sin cambio de medida | 72,01% |
| Cuadro de texto nuevo (junto a la tarjeta) | — | "El 28,0% del volumen figura como NO IDENTIFICADO y es todo de TERMAP (Golfo San Jorge): fue el 79% del volumen de 2019 y el 4% del de 2026. Solo el 62,2% del volumen total es crudo neuquino." | — |
| Gráfico de líneas "Evolución anual de exportación, top 5 países" | incluye 2018 y 2026 | filtro `Dim_Fecha[anio]` entre 2019 y 2025; título "Evolución anual de exportación, top 5 países, 2019–2025" | — |

## Página 6 — "Concentración por empresa" pasa a "Acto III · Exportación: quién la despacha"

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Título (cuadro de texto) | "Acto III · Exportación: quién la despacha y por qué es tan irregular" | "Acto III · Exportación: quién la despacha" | — |
| Cuadro "~94% del volumen exportado…" | "~94% del volumen exportado 2020-2025 pasa por solo 3 empresas/terminales" | "Por operador de terminal, los 3 mayores concentran 94,25% del volumen 2020–2025. Por cargador (quien exporta), los 3 mayores concentran 47,02%. Son medidas distintas." | — |
| Gráfico de barras de participación | "Participación en el volumen exportado, 2020–2025" | título "Participación por operador de terminal en el volumen exportado, 2020–2025" | 61,08% · 27,94% · 5,23% (Oiltanking, TERMAP, CGC) |
| Cuadro "~15× más volátil…" | "~15× … 2020-2025" | "13,3× : la exportación neuquina por terminales varía más mes a mes que la producción de Vaca Muerta (desvío estándar de la variación mensual 2022–2025: 34,0% frente a 2,5%)" | — |
| Cuadro "Esta volatilidad es consistente con la fuerte concentración…" | sugiere asociación con la concentración | "Es una descripción de la diferencia, sin causa atribuida. El cociente cambia con la ventana elegida." | — |
| Gráfico de líneas "Volumen exportado por mes (m³)" | sin alcance | título "Volumen exportado por mes (m³), terminales de todo el país" | — |

## Paso final

1. **Archivo > Guardar como** `ProyectoShale.pbix` (el mismo nombre).
2. **Archivo > Exportar > Plantilla de Power BI** y guardar `ProyectoShale.pbit`. Con ese archivo se pueden verificar las medidas DAX reales y relaciones.
3. Devolver: (a) los valores que mostró cada tarjeta y la matriz de la página 3, (b) cuántas barras hay sobre 100% en la página 4 y sus valores, (c) el `.pbit`.
