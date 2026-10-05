# Medidas DAX — listas para pegar

Cómo usar: creá una tabla de medidas vacía (Modelado > Nueva tabla > `Medidas = {}` o similar) para no mezclarlas
con las tablas de datos, y pegá cada bloque como **Nueva medida** (clic derecho en la tabla > Nueva medida),
reemplazando todo el contenido del editor de fórmulas.

Corregí dos cosas respecto a lo que decía la guía original y el plan (`plan_powerbi.md` sección 4), porque al
escribir el DAX real aparecen bugs que no se ven en la fórmula "de papel":

1. **`Prod Petroleo`**: el plan proponía `DIVIDE(SUM(prod_pet_bbl), SUM(dias_mes))`. Sumar `dias_mes` es
   incorrecto en cuanto el contexto de filtro incluye más de un yacimiento en el mismo mes (que es el caso
   normal): `dias_mes` es el mismo valor repetido por fila, así que `SUM` lo infla tantas veces como
   yacimientos haya.
2. **`Top Yacimientos`**: `TOPN(...)` devuelve una tabla, no un escalar — no se puede usar directo como medida.
   Reemplazado por una medida de ranking (`RANKX`) + instrucción de usar el filtro visual "Top N", que es como
   Power BI realmente maneja este caso.

### Bug de granularidad temporal en Grupo A (detectado en Power BI, 2026-09-16 — el segundo más grave hasta ahora)

Se probó en Power BI con slicers de año (2022 y 2025) y aparecieron dos bugs reales, más un tercero encontrado
al corregir estos dos por la misma causa raíz: **`Fact_Produccion` tiene grano mensual (una fila por
yacimiento-mes, con `fecha` siempre en el día 1 del mes), pero `Dim_Fecha` tiene grano diario** (una fila por
cada día calendario). Cualquier medida que mezcle las dos sin cuidado se rompe.

**Bug 1 — `Prod Petroleo (bbl-dia)` con `AVERAGE(dias_mes))`:** correcto para un solo mes (todas las filas de
ese mes comparten el mismo `dias_mes`, así que `AVERAGE` da el valor correcto sin importar cuántos yacimientos
haya). Pero si el filtro externo abarca **más de un mes** (un año completo, o todo el histórico), `AVERAGE`
sigue devolviendo el promedio de días de un solo mes (~30,4), no la suma real de días del período — infla el
"bbl/día" en la misma proporción que meses haya en el filtro (~12x con un año completo). Verificado con los
datos reales: con el año 2022 filtrado, la fórmula vieja da un número ~12 veces más alto que el real.

**La corrección NO es simplemente `COUNTROWS(Dim_Fecha)`** (la primera opción que se evaluó): funciona bien
para un año completo o para todo el histórico, pero se rompe exactamente en el caso del Bug 2 de abajo, porque
la relación `Dim_Fecha` (1) → `Fact_Produccion` (muchos) filtra en un solo sentido — un filtro puesto
directamente sobre `Fact_Produccion[fecha]` (como hace `LASTDATE(Fact_Produccion[fecha])` en la medida de
variación interanual) **no se propaga hacia atrás para restringir `Dim_Fecha`**, así que `COUNTROWS(Dim_Fecha)`
ahí adentro devolvería el conteo de días de todo el modelo (miles de días) en vez de los ~31 del mes puntual —
cambiaría el bug visible (-100%, fácil de detectar) por uno silencioso (un número que parece plausible pero es
absurdamente bajo, mucho más difícil de notar en una revisión rápida).

**Corrección real, verificada contra los datos** (`SUM(prod_pet_bbl)` / suma de días distintos del período,
sin depender de `Dim_Fecha` en absoluto):

```dax
Prod Petroleo (bbl-dia) =
DIVIDE(
    SUM(Fact_Produccion[prod_pet_bbl]),
    SUMX(VALUES(Fact_Produccion[fecha]), CALCULATE(AVERAGE(Fact_Produccion[dias_mes])))
)
```

`VALUES(Fact_Produccion[fecha])` da la lista de meses distintos que caen en el contexto de filtro actual (uno
si es un solo mes, doce si es un año, todos los que tengan datos si no hay filtro), y por cada uno se suma su
`dias_mes` real (vía `AVERAGE`, seguro porque dentro de un solo mes el valor es constante) — funciona
correctamente para cualquier granularidad, y como no toca `Dim_Fecha`, es inmune al problema de dirección de la
relación. Verificado: 31 días para un mes puntual, 365 para 2022 y para 2025, 7.305 para todo 2006-2025 (bbl/día
resultante: 243.237 en 2022, 501.956 en 2025 — consistente con el año récord que cuenta la historia del
proyecto).

**Bug 2 — `Var Interanual Prod` con `LASTDATE(Dim_Fecha[fecha])`:** bajo un filtro de año, `LASTDATE(Dim_Fecha[fecha])`
devuelve el 31 de diciembre CALENDARIO — pero `Fact_Produccion` nunca tiene una fila con `fecha` = día 31 (solo
día 1 de cada mes), así que ahí la producción siempre da 0 → variación interanual = -100% sin importar el año
(confirmado con 2022 y 2025).

**Corrección:** en vez de perseguir "el último día calendario" con `LASTDATE`/`SAMEPERIODLASTYEAR` (que
requieren que el dato exista exactamente en ese día), se usa `DATEADD`, que desplaza hacia atrás **el período ya
seleccionado** (sea un mes, un año completo, o lo que el slicer tenga activo) en vez de buscar un día puntual:

```dax
Var Interanual Prod =
VAR Anterior = CALCULATE([Prod Petroleo (bbl-dia)], DATEADD(Dim_Fecha[fecha], -1, YEAR))
RETURN
    DIVIDE([Prod Petroleo (bbl-dia)] - Anterior, Anterior)
```

Con esto, si el slicer tiene 2025 seleccionado, `Anterior` recalcula sobre 2024 completo (no sobre un día
puntual) — funciona igual de bien con un mes seleccionado, un año, o un rango arbitrario.

**Bug 3 (mismo origen, no probado por el usuario pero mismo patrón — corregido por las dudas):**
`Var Interanual Exportacion`, en Grupo C, usaba el mismo patrón `LASTDATE(Dim_Fecha[fecha])` /
`SAMEPERIODLASTYEAR(Dim_Fecha[fecha])` sobre `Fact_MovimientosExportacion`, que también tiene grano mensual
(fecha siempre día 1 del mes) — el mismo bug aplicaría ahí. Corregida con el mismo enfoque `DATEADD` (ver
Grupo C más abajo).

**Medida nueva para la Página 1 (resumen ejecutivo):** para que las tarjetas de arriba muestren siempre el
último mes con datos sin que el usuario tenga que aplicar un slicer, se agrega una medida separada que se
autofiltra, dejando la medida general (`Prod Petroleo (bbl-dia)`) libre para reaccionar a slicers en el resto
de las páginas:

```dax
Prod Petroleo (bbl-dia) - Ultimo Mes =
VAR UltimaFecha = CALCULATE(MAX(Fact_Produccion[fecha]), ALL(Fact_Produccion))
RETURN
    CALCULATE([Prod Petroleo (bbl-dia)], Dim_Fecha[fecha] = UltimaFecha)
```

`ALL(Fact_Produccion)` dentro del cálculo de `UltimaFecha` ignora cualquier filtro externo (yacimiento,
provincia, etc.) para encontrar el mes más reciente del dataset completo, sin importar qué esté filtrado en la
página. El `CALCULATE` final sí puede fijar el filtro sobre `Dim_Fecha[fecha]` con seguridad porque va en el
sentido correcto de la relación (de `Dim_Fecha` hacia `Fact_Produccion`) y porque el denominador ya no depende
de `COUNTROWS(Dim_Fecha)` — el mismo patrón se puede replicar para `Prod Gas` o `Volumen Exportado` si más
adelante querés esas tarjetas también ancladas al último mes.

---

## Grupo A — Producción

```dax
Prod Petroleo (bbl-dia) =
DIVIDE(
    SUM(Fact_Produccion[prod_pet_bbl]),
    SUMX(VALUES(Fact_Produccion[fecha]), CALCULATE(AVERAGE(Fact_Produccion[dias_mes])))
)
```

```dax
Prod Petroleo (bbl-dia) - Ultimo Mes =
VAR UltimaFecha = CALCULATE(MAX(Fact_Produccion[fecha]), ALL(Fact_Produccion))
RETURN
    CALCULATE([Prod Petroleo (bbl-dia)], Dim_Fecha[fecha] = UltimaFecha)
```
> Uso: tarjetas de la Página 1 (resumen ejecutivo) — siempre muestra el último mes con datos, sin depender de
> que haya un slicer de fecha aplicado. Para el resto de las páginas (donde sí querés que reaccione a slicers
> de año/mes), usar la medida general `Prod Petroleo (bbl-dia)`.

```dax
Prod Gas (miles m3) =
SUM(Fact_Produccion[prod_gas_miles_m3])
```

```dax
Var Interanual Prod =
VAR Anterior = CALCULATE([Prod Petroleo (bbl-dia)], DATEADD(Dim_Fecha[fecha], -1, YEAR))
RETURN
    DIVIDE([Prod Petroleo (bbl-dia)] - Anterior, Anterior)
```

```dax
Rank Yacimiento =
RANKX(
    ALLSELECTED(Dim_Yacimiento[areayacimiento]),
    CALCULATE([Prod Petroleo (bbl-dia)])
)
```
> Uso: en la tabla/gráfico de yacimientos, agregá `Rank Yacimiento` como campo y aplicá el filtro visual
> **Top N = 5** sobre `Prod Petroleo (bbl-dia)` — así se obtiene el "Top 5 yacimientos" sin depender de `TOPN`
> como medida escalar.

```dax
% Produccion No Convencional =
DIVIDE(
    CALCULATE([Prod Petroleo (bbl-dia)], Fact_Produccion[tipo_de_recurso] = "NO CONVENCIONAL"),
    [Prod Petroleo (bbl-dia)]
)
```
> KPI nuevo sugerido en el plan ("Vaca Muerta no es solo shale") — usa el campo agregado
> `Fact_Produccion[tipo_de_recurso]`, no hace falta ir a nivel pozo.

---

## Grupo B — Transporte

```dax
Utilizacion % =
CALCULATE(
    DIVIDE(
        SUM(Fact_CapacidadDuctos[volumen_transportado]),
        SUM(Fact_CapacidadDuctos[capacidad_mensual_m3])
    ),
    Fact_CapacidadDuctos[capacidad_valida] = TRUE
)
```
> Los 6 ductos con utilización sospechosa (42, 97, 149, 171, 221, 329) ya se excluyeron en la consulta de Power
> Query (`Fact_CapacidadDuctos`, ver `power_query_m.md`) — esta medida no necesita filtrarlos de nuevo. El
> filtro `capacidad_valida = TRUE` cubre el otro caso (120 filas con capacidad reportada en cero).

```dax
Volumen Transportado (respaldo) =
CALCULATE(
    SUM(Fact_TransporteDuctos[volumen]),
    Fact_TransporteDuctos[tipo_producto] = "Petroleo"
)
```
> Complemento para ductos sin cobertura en el Anexo 2A (~55% de los ducto-mes) — mostrar como serie de
> "volumen transportado" en vez de forzar un % de utilización sin denominador confiable.

```dax
% Ductos con Capacidad Reportada =
DIVIDE(
    CALCULATE(DISTINCTCOUNT(Fact_CapacidadDuctos[idducto]), Fact_CapacidadDuctos[capacidad_valida] = TRUE),
    DISTINCTCOUNT(Fact_TransporteDuctos[idducto])
)
```
> Útil como nota al pie visible en la página de infraestructura ("el % de utilización cubre solo el X% de los
> ductos") — transparencia sobre la limitación de cobertura del Anexo 2A.

---

## Grupo C — Exportación

```dax
Volumen Exportado =
CALCULATE(
    SUM(Fact_MovimientosExportacion[volumen]),
    Fact_MovimientosExportacion[tipo_operacion] = "Exportacion"
)
```
> Valor exacto de la categoría en los datos limpios: `"Exportacion"` (sin tilde) — confirmado contra
> `fact_movimientos_exportacion_ductos.csv`. Alternativa equivalente si preferís filtrar por mercado en vez de
> operación: `Fact_MovimientosExportacion[tipo_mercado] = "Externo"`.

```dax
% Pais =
DIVIDE(
    CALCULATE([Volumen Exportado], ALLEXCEPT(Fact_MovimientosExportacion, Dim_Pais)),
    CALCULATE([Volumen Exportado], ALL(Dim_Pais))
)
```

```dax
Var Interanual Exportacion =
VAR Anterior = CALCULATE([Volumen Exportado], DATEADD(Dim_Fecha[fecha], -1, YEAR))
RETURN
    DIVIDE([Volumen Exportado] - Anterior, Anterior)
```
> Corregida por el mismo motivo que `Var Interanual Prod` (ver Grupo A): `Fact_MovimientosExportacion` también
> tiene grano mensual (fecha = día 1 del mes), así que `LASTDATE(Dim_Fecha[fecha])` bajo un filtro de año
> apuntaba al 31 de diciembre calendario, que nunca tiene datos — siempre daba -100%. No se llegó a probar esto
> en Power BI (el bug reportado fue solo en Grupo A), pero el patrón es idéntico, así que se corrigió
> preventivamente.

```dax
Ratio Exportado (vol) =
DIVIDE([Volumen Exportado], SUM(Fact_Produccion[prod_pet_m3]))
```
> En volumen (m³), no en USD — `Fact_Produccion[prod_pet_m3]` ya está en m³ igual que
> `Fact_MovimientosExportacion[volumen]`, así que no hace falta convertir unidades acá (a diferencia de
> `prod_pet_bbl`, que está en barriles).

### Valor USD Estimado — opcional, con dos caveats importantes (uno de ellos grave)

**Caveat grave: la tabla de precios solo cubre enero 2019 - junio 2021** (verificado contra el Excel
original — no es un recorte de la limpieza). No hay ningún precio para 2022 en adelante, que es el período
central de la historia del proyecto (boom de exportación, VMOS). Esta medida va a devolver blanco/0 para todo
2022-2026 sin importar qué tan bien se resuelva el mapeo de producto de abajo — antes de invertir tiempo en el
mapeo, confirmá si realmente vale la pena para el rango de fechas que te interesa mostrar.

El cruce `producto` (exportación) → `tipo_de_crudo` (dimensión) → `tipo_crudo` (precio) **no calza 1:1**: son
grafías de texto libre distintas en cada tabla (ej. `"Crudo Mezcla(Escalante/Cañadon Seco)"` en exportación no
tiene equivalente directo en la tabla de precios, que solo trae `ESCALANTE`, `CAÑADON SECO`, `MEDANITO`,
`SAN SEBASTIAN`, `MARIA INES`). Un `LOOKUPVALUE` directo va a devolver blanco en una parte importante de las
filas. Antes de usar esta medida:

1. Creá una tabla puente manual en Power Query (`Mapeo_ProductoCrudo`, dos columnas: `producto` →
   `tipo_crudo_normalizado`), mapeando a mano los ~24 valores de `producto` a los 5 tipos de crudo con precio
   disponible (dejando en blanco los que no tengan un mapeo razonable, ej. `"Otro(Aclarar en observaciones)"`).
2. Recién ahí esta medida tiene sentido:

```dax
Valor USD Estimado =
SUMX(
    Fact_MovimientosExportacion,
    VAR CrudoNormalizado = LOOKUPVALUE(Mapeo_ProductoCrudo[tipo_crudo_normalizado], Mapeo_ProductoCrudo[producto], Fact_MovimientosExportacion[producto])
    VAR Precio = LOOKUPVALUE(
        Fact_PrecioCrudo[precio_usd_bbl],
        Fact_PrecioCrudo[tipo_crudo], CrudoNormalizado,
        Fact_PrecioCrudo[fecha], Fact_MovimientosExportacion[fecha],
        Fact_PrecioCrudo[tipo_precio], "Precio FOB exportación (fuente SESCO)"
    )
    RETURN
        Fact_MovimientosExportacion[volumen] * 6.2898 * Precio
)
```

Etiquetar siempre en el dashboard como **"estimación"**, nunca como cifra oficial — y mostrar junto al KPI el
`% Ductos con Capacidad Reportada`-equivalente para exportación (qué % del volumen tiene precio asignable),
para que quede claro cuánta cobertura real tiene la estimación.

---

## Grupo D — Contexto (Balance Energético)

```dax
% Exportado sobre Produccion (anual, contexto) =
VAR Exportado = CALCULATE(SUM(Fact_BalanceEnergetico[valor_miles_tep]), Fact_BalanceEnergetico[subcategoria] = "EXPORTACION Y BUNKER", SEARCH("petr", Fact_BalanceEnergetico[producto], 1, 0) = 1)
VAR Producido = CALCULATE(SUM(Fact_BalanceEnergetico[valor_miles_tep]), Fact_BalanceEnergetico[subcategoria] = "PRODUCCION", SEARCH("petr", Fact_BalanceEnergetico[producto], 1, 0) = 1)
RETURN
    DIVIDE(Exportado, Producido)
```
> Solo tiene sentido a nivel **año** (no hay mes en esta tabla) y es a nivel **nacional**, no específico de
> Vaca Muerta — usar como cifra de contexto/validación cruzada en la página de resumen ejecutivo, con esa
> aclaración en el texto ("a nivel país, no solo Vaca Muerta"). `subcategoria` viene en mayúsculas sin tilde
> (`"PRODUCCION"`, `"EXPORTACION Y BUNKER"`, verificado contra los datos reales) — **no** "Producción"/"Exportación
> y Bunker" con tilde como se podría asumir. `producto = "Petróleo"` sí lleva la tilde correctamente codificada
> en UTF-8 (verificado a nivel de byte — no es un carácter corrompido, al contrario de lo que se pensaba en una
> revisión anterior del proyecto). Se dejó el filtro con `SEARCH("petr", ...)` de todos modos, simplemente
> porque es inmune a cualquier diferencia de tildeo/capitalización al pegar el string en el editor DAX — no
> por un problema real de los datos.

---

## Grupo E — Índices base 100 (Página 3 — evolución en el tiempo)

### Por qué el mes base cambió de "enero 2018" a "promedio de 2019" (corregido 2026-09-21)

La primera versión usaba enero 2018 como base porque es el primer mes donde `Fact_Produccion` y
`Fact_MovimientosExportacion` tienen datos simultáneamente. Se validó esa elección contra los datos reales y
**no era representativa** — enero 2018 es un mes de cobertura de reporte incompleta, no un punto de partida
real de la serie:

| | ene-2018 | promedio 2020 | promedio 2023 |
|---|---|---|---|
| Filas con `tipo_operacion="Exportacion"` | 1 | 10,6/mes | 17,4/mes |
| Empresas distintas | **1** | 3,6 | 3,25 |
| Cargadores distintos | 1 | 8,3 | 15,0 |
| Volumen exportado | 17.022 m³ | 423.042 m³ | 563.258 m³ |

Todo 2018 tiene **una sola empresa reportando** y 3 de los 12 meses (marzo, mayo, agosto) no tienen ninguna
fila. Recién en 2019 aparecen 2-4 empresas reportando de forma más regular, y el volumen salta a un rango de
220.000-460.000 m³/mes — un salto de hasta 20x que es **cobertura de reporte mejorando, no crecimiento físico
de exportación**. Indexar contra enero 2018 mezclaba las dos cosas: el índice iba a mostrar un "crecimiento"
de +1.660% solo entre enero 2018 y el promedio de 2019, antes de que pase nada relacionado con VMOS/Oldelval o
con el boom real de Vaca Muerta.

**Corrección:** se usa el **promedio de los 12 meses de 2019** como base = 100 — el primer año calendario
completo con varias empresas reportando de forma consistente (2019 sigue teniendo un enero débil, con una sola
empresa, pero promediar 12 meses diluye ese arranque en vez de anclar todo el índice a él). Promedios de
referencia verificados: **316.714 m³/mes** de volumen exportado y **90.014 bbl/día** de producción en 2019. Con
esta base, enero 2018 pasa de "=100 por definición" a un valor real y bajo (≈5,4), que es justamente lo que
tiene que mostrar un mes de reporte incompleto — ya no distorsiona el resto de la serie.

**También se alineó la base de `Indice Produccion (base 100)` al mismo período (promedio 2019)**, aunque
`Fact_Produccion` no tiene el problema de cobertura de exportación — no había una razón de corrección para
tocarla, pero si las dos medidas usan bases de tiempo distintas (una anclada a un mes puntual de 2018, la otra
a un promedio de 2019), dejan de ser comparables como "ambas arrancan en el mismo punto de referencia", que es
el objetivo completo de este gráfico en la Página 3. Si preferís mantener `Indice Produccion` con su propia
base independiente, es cuestión de volver a poner `Dim_Fecha[fecha] = DATE(2018,1,1)` en esa medida — no hay
ningún problema de datos que lo impida.

### Bug de columnas distintas en el mismo CALCULATE (detectado por el usuario en Power BI, 2026-09-21)

La primera versión de estas medidas (`CALCULATE(AVERAGEX(...), Dim_Fecha[anio] = 2019)`, sin más) se probó en
un gráfico de líneas con `Dim_Fecha[fecha]`/`anio_mes` en el eje X, y dio **exactamente 100,00 en cualquier mes
de 2019** (confirmado en febrero y octubre) — cuando debería oscilar cerca de 100, no ser idéntico mes a mes,
porque la base es un promedio de 12 meses distintos.

**Causa confirmada:** cuando dos argumentos de filtro de `CALCULATE` apuntan a **columnas distintas de la misma
tabla** (`Dim_Fecha[fecha]`, ya filtrada por el eje del gráfico a un mes puntual, y `Dim_Fecha[anio] = 2019`,
agregado por la medida), DAX **no reemplaza** el primer filtro con el segundo — los combina con AND. El filtro
efectivo termina siendo "`fecha` = ese mes puntual **Y** `anio` = 2019", que para cualquier mes DENTRO de 2019
colapsa a una intersección de un solo mes (el mismo que se está evaluando) — `AVERAGEX` promedia una tabla de
un solo valor, que es igual al valor actual, y el índice da 100 siempre. Verificado contra los datos reales:

| Mes en el eje | `ValorBase` con el bug | Índice con el bug |
|---|---|---|
| Febrero 2019 | 314.891,6 (= el valor de febrero) | 100,00 |
| Octubre 2019 | 352.843,4 (= el valor de octubre) | 100,00 |

**Síntoma adicional, no reportado pero verificado:** para cualquier mes **fuera** de 2019 (ej. febrero 2020),
la intersección "`fecha`=feb-2020 **Y** `anio`=2019" da 0 filas — `AVERAGEX` sobre una tabla vacía es `BLANK`,
y `DIVIDE(actual, BLANK)` también es `BLANK`. El bug no solo aplanaba 2019 en 100: probablemente dejaba el
índice completamente en blanco para todos los demás años del gráfico (2018, 2020-2026) — más notorio que el
"siempre 100" pero fácil de no atribuir a la misma causa si se mira por separado.

**Corrección:** agregar `ALL(Dim_Fecha)` como argumento de filtro **antes** de `Dim_Fecha[anio] = 2019`, en el
mismo `CALCULATE`. `ALL(Dim_Fecha)` descarta cualquier filtro previo sobre la tabla completa — sin importar en
qué columna estuviera (`fecha` del eje del gráfico, un slicer de año, o ninguno) — y recién sobre esa base
limpia se aplica el filtro `anio = 2019`, dejando los 12 meses de 2019 disponibles para el `AVERAGEX` sin
importar qué esté filtrado afuera:

```dax
Indice Produccion (base 100) =
VAR ValorBase =
    CALCULATE(
        AVERAGEX(VALUES(Dim_Fecha[anio_mes]), [Prod Petroleo (bbl-dia)]),
        ALL(Dim_Fecha),
        Dim_Fecha[anio] = 2019
    )
RETURN
    DIVIDE([Prod Petroleo (bbl-dia)], ValorBase) * 100
```

```dax
Indice Exportacion (base 100) =
VAR ValorBase =
    CALCULATE(
        AVERAGEX(VALUES(Dim_Fecha[anio_mes]), [Volumen Exportado]),
        ALL(Dim_Fecha),
        Dim_Fecha[anio] = 2019
    )
RETURN
    DIVIDE([Volumen Exportado], ValorBase) * 100
```

**Verificado con los datos reales, ya con el fix:**

| Mes en el eje | `ValorBase` corregido | Índice corregido |
|---|---|---|
| Febrero 2019 | 316.714,1 (promedio de los 12 meses) | 99,42 |
| Octubre 2019 | 316.714,1 (promedio de los 12 meses) | 111,41 |

Ahora oscila alrededor de 100 en vez de ser idéntico — y el índice deja de depender de qué mes puntual esté
activo en el eje del gráfico, así que también funciona igual de bien en una tarjeta con un slicer de año en vez
de en el gráfico de líneas (el `ALL(Dim_Fecha)` limpia esa selección también antes de fijar el año base). Es el
mismo cuidado que ya había aparecido con `Var Interanual Prod` en el Grupo A, pero en su variante más engañosa:
ahí el filtro roto vivía en una tabla distinta (relación de un solo sentido); acá vive en la **misma tabla**,
por eso pasa desapercibido más fácil — dos columnas de `Dim_Fecha` conviven en el mismo `CALCULATE` sin que se
reemplacen entre sí a menos que se lo pidas explícitamente con `ALL`.

**Ya no hay meses en blanco:** con el fix, todo el rango 2018-2026 tiene un valor de índice calculable — 2018
va a mostrar números bajos (~5-8), reflejando fielmente que era un período de reporte incompleto, no un error
de la medida ni un hueco en el gráfico.

---

## Grupo F — medidas creadas al armar las páginas del reporte

```dax
% Exportacion con Pais Asignado =
DIVIDE(
    CALCULATE(
        [Volumen Exportado],
        Fact_MovimientosExportacion[pais] <> "" && NOT(ISBLANK(Fact_MovimientosExportacion[pais]))
    ),
    [Volumen Exportado]
)
```
> Qué parte del volumen exportado tiene país de destino (~72%). Los registros sin país vienen como cadena vacía, no como nulo, así que `ISBLANK` solo no alcanza.

```dax
% Exportado por Empresa (sobre total) =
DIVIDE(
    [Volumen Exportado],
    CALCULATE([Volumen Exportado], ALL(Fact_MovimientosExportacion[empresa]))
)
```
> Participación de cada empresa sobre el total exportado. `ALL(empresa)` en el denominador evita que el filtro visual Top N recalcule el % solo sobre las empresas visibles.

```dax
Tiene Capacidad Confiable =
IF(
    CALCULATE(COUNTROWS(Fact_CapacidadDuctos), Fact_CapacidadDuctos[capacidad_valida] = TRUE) > 0,
    1,
    0
)
```
> Da 1 si el ducto tiene al menos un registro con `capacidad_valida = TRUE`. Filtrada en 0, deja en el visual de `Volumen Transportado (respaldo)` solo los ductos sin capacidad confiable.

```dax
Var Interanual Prod - Ultimo Mes =
VAR UltimaFecha = CALCULATE(MAX(Fact_Produccion[fecha]), ALL(Fact_Produccion))
VAR Actual = CALCULATE([Prod Petroleo (bbl-dia)], Dim_Fecha[fecha] = UltimaFecha)
VAR Anterior = CALCULATE([Prod Petroleo (bbl-dia)], Dim_Fecha[fecha] = EDATE(UltimaFecha, -12))
RETURN
    DIVIDE(Actual - Anterior, Anterior)
```
> Variación interanual del último mes con datos contra el mismo mes del año anterior, para las tarjetas de resumen (no el acumulado histórico).

```dax
Volumen Exportado - Ultimo Mes =
VAR UltimaFecha =
    CALCULATE(
        MAX(Fact_MovimientosExportacion[fecha]),
        ALL(Fact_MovimientosExportacion),
        Fact_MovimientosExportacion[tipo_operacion] = "Exportacion"
    )
RETURN
    CALCULATE([Volumen Exportado], Dim_Fecha[fecha] = UltimaFecha)
```
> Volumen exportado del último mes con registros de exportación, para las tarjetas de resumen (no el acumulado histórico).

```dax
Color Utilizacion =
IF([Utilizacion %] > 1, "#A6402F", "#C1690E")
```
> Devuelve `#A6402F` si la utilización supera el 100% (`Utilizacion %` es un cociente: 1 = 100%) y `#C1690E` en el resto. Son los colores `bad` y el primero de `dataColors` del tema.
