# Cambios a aplicar en el reporte de Power BI

Este documento lista, página por página, qué títulos, textos, filtros y medidas cambian en `ProyectoShale.pbix` para que coincida con las correcciones de la auditoría y con la serie principal de exportación (comercio exterior). Los valores esperados salen de `data/web/registro_cifras.json` (el mismo registro que usan el README y el dashboard web).

**Qué no se pudo verificar.** Estos cambios no se ejecutaron en Power BI Desktop ni se contrastaron con el modelo real: no hay un `.pbit` para leer las medidas y relaciones. Cada medida nueva figura como NO VERIFICADO hasta que el valor que muestre Power BI coincida con el valor esperado de esta guía. Si un valor no coincide, no sigas: avisá cuál fue y qué mostró.

**Por qué las tarjetas de producción cierran en diciembre de 2025.** El modelo se alimenta de las tablas limpias de producción por pozo, que llegan hasta diciembre de 2025. La versión web suma además junio de 2026 (solo no convencional) leído directo de los datos crudos. Las dos versiones comparten el registro de cifras; cada tarjeta declara su fecha.

## Paso 0. Preparación (una sola vez)

1. En **Inicio > Transformar datos > Administrar parámetros**, apuntar `RutaClean` a la carpeta de las tablas limpias corregidas (`clean_corregido` del proyecto, o la carpeta que indique `VM_CLEAN_DIR`), con la barra final (por ejemplo `D:\datos\clean_corregido\`). Antes hay que correr el script 16 (`scripts/16_comercio_exterior.py`), que crea `fact_exportacion_crudo_comex.csv` y `produccion_cuenca_oficial_mensual.csv` en esa carpeta.
2. **Inicio > Nueva fuente > Consulta en blanco** (dos veces) y pegar, en el **Editor avanzado**, los bloques 13 y 14 de `powerbi/power_query_m.md`; nombrarlas `Fact_ExportacionComex` y `Fact_ProduccionCuenca`.
3. **Inicio > Actualizar**. Control: la suma de `prod_pet_bbl` en `Fact_Produccion` tiene que dar 722.439.535. En `Fact_ExportacionComex` tienen que figurar 125.532 filas. Si algo da otro valor, parar y avisar.
4. **Vista de modelo**: crear dos relaciones, `Fact_ExportacionComex[fecha]` con `Dim_Fecha[fecha]` y `Fact_ProduccionCuenca[fecha]` con `Dim_Fecha[fecha]`, de muchos a uno, dirección única. Después, en **Inicio > Transformar datos**, abrir la consulta `Dim_Fecha` > **Editor avanzado** y reemplazar su código por el bloque 10 actualizado de `powerbi/power_query_m.md` (ahora incluye las dos tablas nuevas en el rango de fechas); **Cerrar y aplicar**. Confirmar que `Dim_Ducto[idducto]` sigue relacionada con `Fact_CapacidadDuctos[idducto]` y con `Fact_TransporteDuctos[idducto]`.
5. En **Modelado > Nueva medida**, agregar las medidas del Grupo E de `powerbi/dax_measures.md`: `Dias del Periodo`, `Volumen Exportado Cuenca`, `Monto Exportado Cuenca (USD)`, `Precio Implicito (USD-bbl)`, `Exportacion Cuenca (bbl-dia)`, `Produccion Cuenca (bbl-dia)`, `% Exportado de la Cuenca`, los índices base 2022 y de media móvil, `% Exportado por Empresa Exportadora`, `Volumen Terminales Neuquinos (contraste)` y `Utilizacion % (anio mas reciente valido)`.
6. Agregar también esta medida:

```dax
% Produccion No Convencional 2022-2025 =
VAR NC = CALCULATE([Prod Petroleo (bbl-dia)], Fact_Produccion[tipo_de_recurso] = "NO CONVENCIONAL", Dim_Fecha[anio] >= 2022, Dim_Fecha[anio] <= 2025)
VAR Total = CALCULATE([Prod Petroleo (bbl-dia)], Dim_Fecha[anio] >= 2022, Dim_Fecha[anio] <= 2025)
RETURN DIVIDE(NC, Total)
```

7. **Control de las medidas nuevas** antes de tocar las páginas: en una tabla temporal con `Dim_Fecha[anio]` en filas, `Volumen Exportado Cuenca` tiene que dar 4.195.638 (2022) y 11.113.169 (2025), y `Monto Exportado Cuenca (USD)` USD 4.536 millones en 2025. Si no coinciden, parar.

## Página 1 — Vaca Muerta: de la cuenca al mundo (resumen)

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Tarjeta `% Produccion No Convencional` | título "% Produccion No Convencional", medida histórica | título "Incidencia no convencional, 2022–2025"; medida `% Produccion No Convencional 2022-2025` | 99,88% |
| Tarjeta `Prod Petroleo (bbl-dia) - Ultimo Mes` | título igual al nombre de la medida | título "Producción de petróleo, dic-2025 (bbl/día)" | 590.754,6 |
| Tarjeta `Var Interanual Prod - Ultimo Mes` | título igual al nombre de la medida | título "Variación interanual, dic-2025 vs dic-2024" | 31,92% |
| Tarjeta `Volumen Exportado - Ultimo Mes` (m³ del último mes, todas las terminales) | volumen nacional del último mes | reemplazar por la medida `Exportacion Cuenca (bbl-dia)` con filtro del objeto visual `Dim_Fecha[anio]` = 2025; título "Exportación de crudo de la cuenca, 2025 (bbl/día, comercio exterior)" | 191.506 |
| Cuadro de texto nuevo (debajo de las tarjetas) | — | "El modelo de producción cierra en diciembre de 2025. La versión web suma junio de 2026 (solo no convencional): 633.371 bbl/día, +33,0% interanual." | — |

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
| Título de la página y cuadro de texto superior | "Producción vs. exportación: la brecha se sostiene y crece desde 2023" | "Producción y exportación: índices base 2022" |
| Gráfico de líneas | "Índice de producción vs. exportación (base 100 = promedio 2019)", medidas `Indice Produccion (base 100)` e `Indice Exportacion (base 100)` | título "Índices de producción de la cuenca, de Vaca Muerta y de exportación de crudo de la cuenca (media móvil de 12 meses, base 2022 = 100)"; medidas `Indice Exportacion Cuenca MA12 (base 2022)`, `Indice Produccion Cuenca MA12 (base 2022)` e `Indice Produccion VM MA12 (base 2022)`; sin filtro de año en el gráfico |
| Cuadro de texto "Metodología / El hallazgo / Una limitación" | base 2019, "brecha ≥ 120 puntos desde 2023", +1.660% | ver texto de abajo |
| Tabla nueva (matriz) | — | `Dim_Fecha[anio]` en filas (2022 a 2025), medidas `Indice Exportacion Cuenca (base 2022)`, `Indice Produccion Cuenca (base 2022)` e `Indice Produccion VM (base 2022)` |

Valores esperados de la matriz (promedios anuales, base 2022 = 100), en el orden exportación / producción de la cuenca / producción de Vaca Muerta: 2022 → 100,0 / 100,0 / 100,0; 2023 → 125,3 / 116,6 / 125,8; 2024 → 165,5 / 138,9 / 159,2; 2025 → 264,9 / 168,1 / 206,4.

Valores esperados del gráfico a diciembre de cada año (media móvil de 12 meses): exportación 125,2 (2023), 165,7 (2024), 264,6 (2025); producción de la cuenca 116,6, 138,9 y 168,0; producción de Vaca Muerta 125,8, 159,1 y 206,2.

**Texto nuevo del cuadro:**

> **Metodología.** Los índices parten de 100 = promedio de 2022, el primer año con exportación en 12 de 12 meses y con exportación igual o mayor al 10% de la producción de la cuenca. La exportación es la de crudo de la cuenca Neuquina según comercio exterior declarado, y la producción de la cuenca es la serie oficial. La curva usa media móvil de 12 meses y empieza cuando hay 12 meses de datos.
> **Qué se puede afirmar.** Con las bases 2021, 2022 y 2023, y con las dos fuentes (comercio exterior; terminales marítimos más oleoducto a Chile), la exportación de la cuenca crece más que la producción de la cuenca en cada año posterior a la base. Lo que difiere entre las fuentes es el nivel, no la dirección.
> **Una limitación.** Antes de 2022 hay meses sin exportación declarada (cuentan como cero), y en septiembre de 2024 la producción de Vaca Muerta por pozo queda por debajo del agregado oficial; la producción de la cuenca usa la serie oficial.

## Página 4 — Acto II · Transporte (versión nueva)

**Cambio de diseño posterior a la primera versión de esta guía.** El ranking de utilización pasa de ser el protagonista a ser un detalle, porque las capacidades de las distintas fuentes no coinciden. La página 4 nueva muestra el petróleo transportado (dato directo), la capacidad por fuente y los proyectos anunciados. **Si ya armaste la página 4 con la versión anterior, no la rehagas:** hacé clic derecho sobre la pestaña de la página 4 > **Duplicar página**, dejá la original como página **7** con el nombre "Detalle: utilización informada (con advertencias)" y aplicale solo lo que figura abajo en "Página 7"; después convertí la copia en la página 4 nueva siguiendo esta tabla.

| Elemento | Después | Valor esperado |
|---|---|---|
| Título de la página (cuadro de texto) | "Acto II · Transporte: cuánto petróleo se mueve y qué se anuncia" | — |
| Gráfico de columnas apiladas (nuevo) | eje `Dim_Fecha[anio]` con filtro 2020 a 2025; leyenda `Dim_Ducto[denominacion]`; valores `Volumen Transportado (respaldo)`; filtro del objeto visual `Dim_Ducto[idducto]` en 216 y 511; título "Petróleo transportado por el corredor Allen–Puerto Rosales (m³ por año)" | 2020: 9.100.851; 2021: 11.113.147; 2022: 14.062.391; 2023: 15.478.545; 2024: 16.510.040; 2025: 13.589.825 (línea original) más 9.178.499 (línea Duplicar), total 22.768.324; crecimiento 2025 vs 2024: 37,9% |
| Cuadro de texto "capacidad por fuente" (nuevo) | texto de abajo | — |
| Cuadro de texto "Por qué no se publica un porcentaje" (nuevo) | texto de abajo | — |
| Cuadro de texto "Proyectos anunciados" (reemplaza al cuadro de hitos de VMOS) | texto de abajo, con el aviso de que es información externa | — |
| Tarjetas, gráficos de utilización y de respaldo, y cuadro inferior de la versión anterior | se quitan de esta página (pasan a la página 7) | — |

Nota sobre el valor del gráfico: para los ductos 216 y 511 la suma de tramos de `Volumen Transportado (respaldo)` coincide con el volumen del tramo más cargado de la web (un solo tramo); por eso este gráfico no necesita una medida nueva. No usar esa misma medida para ductos con varios tramos en serie (por ejemplo VMOC): contaría dos veces el mismo barril.

**Texto "capacidad por fuente":**

> Capacidad del corredor Allen–Puerto Rosales (m³/día). Anexo 2A: 46.384 (2022), 50.052 (2023) y 36.000 (2024). Secretaría de Energía, septiembre de 2022: 36.000 (capacidad actual de Oldelval). Nota del sector (Econojournal), abril de 2022: 42.000. Oldelval, proyecto Duplicar: 55.000 en la primera fase y 86.000 como objetivo. Las fuentes no coinciden.

**Texto "Por qué no se publica un porcentaje":**

> La capacidad del Anexo 2A para 2024 (36.000 m³/día) coincide con la que la Secretaría de Energía dio en septiembre de 2022, pero el petróleo transportado en 2024 fue de 45.109 m³/día: más que esa capacidad. La cifra no funciona como límite físico, y con otra capacidad creíble la utilización de 2024 pasa de 129,7% a 111,2% o 93,3%. El ranking de utilización, con sus advertencias, está en la página 7.

**Texto "Proyectos anunciados":**

> Información externa, no verificada con los datos de este proyecto; son anuncios de empresas y del Estado y las fechas pueden cambiar. VMOS: oleoducto de 437 km entre Allen y Punta Colorada con terminal de monoboyas; YPF informa hasta 550.000 bbl/día, ampliable a 700.000; la aprobación en el RIGI cita una capacidad base de 377.400 bbl/día; Más Energía (enero de 2026) citaba una operación inicial de 180.000 bbl/día y puesta en marcha prevista para enero de 2027. Duplicar Norte (Oldelval, 8 de septiembre de 2026): oleoducto de 207 km y 24 pulgadas, 220.000 bbl/día adicionales, avance global de 50% y puesta en marcha prevista para el primer trimestre de 2027. Fuentes: energia-argentina.ypf.com/vmos.html, argentina.gob.ar (resolución del Ministerio de Economía de marzo de 2025), mase.lmneuquen.com (27 de enero de 2026) y oldelval.com (8 de septiembre de 2026).

## Página 5 — Acto III · Exportación: adónde va

Esta página pasa a usar `Fact_ExportacionComex` (crudo de la cuenca Neuquina) en lugar de la planilla 21 (todas las terminales del país).

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Gráfico "Principales países de destino (m³)" | `Dim_Pais[pais]` y `Volumen Exportado` | eje `Fact_ExportacionComex[pais]`, medida `Volumen Exportado Cuenca`, Top N = 10 excluyendo "no aplica"; título "Principales países de destino (m³): crudo de la cuenca Neuquina, 2020 – agosto 2026" | primero Estados Unidos (45,9% del volumen) y segundo Chile (27,0%) |
| Tarjeta "Exportación con país de destino registrado" | 72,01% (planilla 21) | cambiar por una tarjeta con la medida nueva `% Exportacion sin Pais (no aplica)` (Grupo E de `powerbi/dax_measures.md`); título "Volumen sin destino informado"; formato de la medida: Porcentaje con 1 decimal | 5,9% |
| Cuadro de texto junto a la tarjeta | — | "Porcentaje del volumen exportado de crudo de la cuenca Neuquina cuyo país de destino figura como 'no aplica' en el comercio exterior (2020 – agosto 2026). El resto tiene destino declarado." | — |
| Gráfico de líneas "Evolución anual de exportación, top 5 países" | incluye 2018 y 2026 (planilla 21) | eje `Dim_Fecha[anio]`, leyenda `Fact_ExportacionComex[pais]`, medida `Volumen Exportado Cuenca`, filtro `Dim_Fecha[anio]` entre 2020 y 2025; título "Evolución anual de exportación, top 5 países, 2020–2025 (en 2020 hay exportación en 6 de 12 meses)" | — |
| Tabla nueva | — | `Dim_Fecha[anio]` en filas (2020 a 2025), medidas `Volumen Exportado Cuenca`, `Monto Exportado Cuenca (USD)` y `Precio Implicito (USD-bbl)`; título "Valor de la exportación (USD, monto FOB declarado)" | 2025: USD 4.536 millones y 64,9 USD/bbl; 2022: USD 2.441 millones y 92,5 USD/bbl |

## Página 6 — "Concentración por empresa" pasa a "Acto III · Exportación: quién la despacha"

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Título (cuadro de texto) | "Acto III · Exportación: quién la despacha y por qué es tan irregular" | "Acto III · Exportación: quién la despacha" | — |
| Cuadro "~94% del volumen exportado…" | "~94% del volumen exportado 2020-2025 pasa por solo 3 empresas/terminales" | "Las 3 mayores empresas exportadoras de crudo de la cuenca concentran 58,6% del volumen 2020–2025 (agrupando las variantes de razón social de una misma empresa). Por operador de terminal de todo el país (planilla 21), los 3 mayores concentran 94,25%. Son medidas distintas." | — |
| Gráfico de barras de participación | "Participación en el volumen exportado, 2020–2025" por operador de terminal | eje `Fact_ExportacionComex[empresa]`, medida `% Exportado por Empresa Exportadora`, filtro `Dim_Fecha[anio]` entre 2020 y 2025, Top N = 6; título "Participación por empresa exportadora en el volumen de crudo de la cuenca, 2020–2025" | primera empresa (agrupada): 28,6%; sin agrupar, las 3 primeras suman 54,9% |
| Cuadro "~15× más volátil…" | "~15× … 2020-2025" | "17,0×: la exportación de crudo de la cuenca varía más mes a mes que la producción de la cuenca (desvío estándar de la variación mensual 2022–2025: 29,2% frente a 1,7%)" | — |
| Cuadro "Esta volatilidad es consistente con la fuerte concentración…" | sugiere asociación con la concentración | "Es una descripción de la diferencia, sin causa atribuida. El cociente cambia con la ventana elegida." | — |
| Gráfico de líneas "Volumen exportado por mes (m³)" | todas las terminales, planilla 21 | medida `Volumen Exportado Cuenca` por mes; título "Volumen exportado por mes (m³), crudo de la cuenca (comercio exterior)" | — |
| Cuadro de texto nuevo (contraste) | — | "Las fuentes oficiales de exportación no concilian desde 2023: el comercio exterior queda entre 0,75 y 0,88 veces los terminales marítimos más el oleoducto a Chile. Ver el panel de contraste de la versión web." | — |

## Página 7 — Detalle: utilización informada (con advertencias)

Es la página 4 de la versión anterior de esta guía, con estos cambios:

| Elemento | Antes | Después | Valor esperado |
|---|---|---|---|
| Título de la página | "Acto II · Transporte: ductos que superan el 100% de su capacidad informada" | "Detalle: utilización informada de los ductos (con advertencias)" | — |
| Gráfico de barras de utilización | medida `Utilizacion %`, ejes sin Top N | medida `Utilizacion % (anio mas reciente valido)`; eje `Dim_Ducto[denominacion_logica]`; filtro del objeto visual `Tiene Capacidad No Dudosa` = 1; Top N = 20 por esa medida; título "Utilización del tramo más cargado (año más reciente válido; 100% = capacidad operativa informada)" | 3 barras sobre 100%: Allen - Puerto Rosales (2024, 12 meses; a revisar) con 129,7%; LINDERO ATRAVESADO- CENTENARIO (2023, 2 meses; a revisar) con 111,1%; Centenario - Allen L14 (2024, 12 meses) con 106,9% |
| Gráfico de respaldo | título "Ductos sin capacidad confiable — volumen transportado (m³)" | título "Ductos sin capacidad utilizable — volumen de petróleo transportado (m³)"; filtro `Tiene Capacidad No Dudosa` = 0 | 39 ductos en total (los que no figuran en el Anexo 2A y los de capacidad dudosa todos los años) |
| Cuadro de texto inferior | "…57 tienen un dato de capacidad operativa confiable… Los otros 85…" | texto de abajo | — |

**Texto nuevo del cuadro inferior de la página 7:**

> De 83 ductos que mueven petróleo, 44 tienen capacidad válida y entran al ranking; 5 tienen capacidad dudosa en todos los años y 34 no figuran en el Anexo 2A. Se excluyen 36 ducto-años de 18 ductos por reglas explícitas (en `data/web/ductos_capacidad_dudosa.csv`). La utilización es el volumen del tramo más cargado (solo líquidos) sobre la capacidad operativa informada; superar el 100% no permite decidir si el volumen excede la capacidad o si la capacidad informada no corresponde al tramo, y las capacidades de distintas fuentes no coinciden. 2 de los 3 ductos sobre 100% tienen la capacidad marcada "a revisar" (se identifican en la versión web).

## Paso final

1. **Archivo > Guardar como** `ProyectoShale.pbix` (el mismo nombre).
2. **Archivo > Exportar > Plantilla de Power BI** y guardar `ProyectoShale.pbit`. Con ese archivo se pueden verificar las medidas DAX reales y relaciones.
3. Devolver: (a) los valores que mostró cada tarjeta y la matriz de la página 3, (b) los valores del gráfico de la página 4, (c) los valores de la tabla de USD de la página 5, (d) cuántas barras hay sobre 100% en la página 7 y sus valores, (e) el `.pbit`.
