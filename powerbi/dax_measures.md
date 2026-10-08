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
resultante: 243.237 en 2022, 501.956 en 2025 — coherente con la serie de producción anual del proyecto).

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
        SUM(Fact_CapacidadDuctos[volumen_segmento_mas_cargado]),
        SUM(Fact_CapacidadDuctos[capacidad_mensual_m3])
    ),
    Fact_CapacidadDuctos[capacidad_valida] = TRUE,
    Fact_CapacidadDuctos[capacidad_dudosa] = FALSE
)
```
> **Corregida tras la auditoría (F2, F3, F5).** El numerador era `volumen_transportado`, que suma todos los
> productos (incluido gas natural) y todos los segmentos en serie del ducto contra la capacidad de una sola
> fila. Ahora usa `volumen_segmento_mas_cargado` (solo líquidos; el mayor volumen entre los segmentos
> origen→destino de cada ducto-mes). No es una cota: coincide con la utilización real solo si la capacidad
> informada corresponde a ese tramo (el Anexo 2A y la planilla 20 no comparten identificador de tramo).
> `capacidad_dudosa = FALSE` reemplaza a la exclusión por ducto completo de los 6 `idducto` (42, 97, 149, 171,
> 221, 329): ahora se descartan **ducto-años** según las reglas R1, R3, R4, R5 y la decisión D2 (ver
> `diccionario_datos.md`), y esos ducto-años se listan aparte en `data/web/ductos_capacidad_dudosa.csv`, sin
> publicar su utilización. `capacidad_valida = TRUE` sigue cubriendo las 120 filas con capacidad en cero.

```dax
Volumen Transportado (respaldo) =
CALCULATE(
    SUM(Fact_TransporteDuctos[volumen]),
    Fact_TransporteDuctos[tipo_producto] = "Petroleo"
)
```
> Complemento para ductos sin cobertura en el Anexo 2A (~55% de los ducto-mes) — mostrar como serie de
> "volumen transportado" en vez de forzar un % de utilización sin denominador válido.

> **Medida retirada (`% Ductos con Capacidad Reportada`).** Dividía 57 ductos con capacidad (13 de ellos sin
> petróleo) por 133 ductos de transporte: universos distintos. La cobertura se informa con la clasificación de los
> ductos lógicos que mueven petróleo (`data/web/clasificacion_ductos_petroleo.csv`): con capacidad no dudosa (entran al
> ranking), sin capacidad en el Anexo 2A y con capacidad dudosa en todos los años. Los conteos vigentes están en
> `data/web/registro_cifras.json`.

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
    [Volumen Exportado],
    CALCULATE([Volumen Exportado], ALL(Dim_Pais))
)
```
> **Corregida (F12).** La versión anterior usaba `ALLEXCEPT(Fact_MovimientosExportacion, Dim_Pais)`, que pasa una
> tabla donde DAX espera columnas de la tabla indicada y no es una sintaxis válida. El numerador es el volumen del
> país en contexto y el denominador el volumen total sin filtro de país. **El denominador incluye el volumen sin
> país identificado** (27,99% del total: rótulo "NO IDENTIFICADO" de la planilla 21, todo de TERMAP), de modo que
> los porcentajes por país suman 72,01% y no 100%. Para repartir solo entre países identificados, usar como
> denominador `CALCULATE([Volumen Exportado], ALL(Dim_Pais), NOT(ISBLANK(Fact_MovimientosExportacion[pais])), Fact_MovimientosExportacion[pais] <> "")`.

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

> **Medida retirada (`Ratio Exportado (vol)`).** Dividía la exportación de las 6 terminales de todo el país (el
> 62% es crudo neuquino; el 28% es del Golfo San Jorge) por la producción de Vaca Muerta: el numerador no es un
> subconjunto del denominador y la razón supera 1 en 5 meses (máx 1,79). El reemplazo es el `% exportado de la
> cuenca` (crudo exportado por terminales neuquinos / producción total de la Cuenca Neuquina, solo 2022–2025),
> calculado en `scripts/11_series_cuenca_neuquina.py` y publicado en `data/web/comparacion_produccion_exportacion.csv`.

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
VAR Exportado = ABS(CALCULATE(SUM(Fact_BalanceEnergetico[valor_miles_tep]), Fact_BalanceEnergetico[subcategoria] = "EXPORTACION Y BUNKER", SEARCH("petr", Fact_BalanceEnergetico[producto], 1, 0) = 1))
VAR Producido = CALCULATE(SUM(Fact_BalanceEnergetico[valor_miles_tep]), Fact_BalanceEnergetico[subcategoria] = "PRODUCCION", SEARCH("petr", Fact_BalanceEnergetico[producto], 1, 0) = 1)
RETURN
    DIVIDE(Exportado, Producido)
```
> **Corregida (F12):** en el Balance las exportaciones figuran con signo negativo (convención de balance: las
> salidas restan); sin `ABS` la medida devolvía −19,0% (2023), −26,6% (2024) y −28,8% (2025). Con `ABS`: 19,0%,
> 26,6% y 28,8%. "EXPORTACION Y BUNKER" incluye además el combustible vendido a buques (bunker), así que no es
> exportación pura. Solo tiene sentido a nivel **año** (no hay mes en esta tabla) y es a nivel **nacional**, no específico de
> Vaca Muerta — usar como cifra de contexto/validación cruzada en la página de resumen ejecutivo, con esa
> aclaración en el texto ("a nivel país, no solo Vaca Muerta"). `subcategoria` viene en mayúsculas sin tilde
> (`"PRODUCCION"`, `"EXPORTACION Y BUNKER"`, verificado contra los datos reales) — **no** "Producción"/"Exportación
> y Bunker" con tilde como se podría asumir. `producto = "Petróleo"` sí lleva la tilde correctamente codificada
> en UTF-8 (verificado a nivel de byte — no es un carácter corrompido, al contrario de lo que se pensaba en una
> revisión anterior del proyecto). Se dejó el filtro con `SEARCH("petr", ...)` de todos modos, simplemente
> porque es inmune a cualquier diferencia de tildeo/capitalización al pegar el string en el editor DAX — no
> por un problema real de los datos.

---

## Grupo E — Índices base 2022 y exportación por comercio exterior (Páginas 1, 3, 5 y 6)

> **Reemplaza al Grupo E original (base 2019, exportación de todas las terminales del país).** La serie de exportación es ahora el
> crudo de la cuenca Neuquina según el comercio exterior declarado por las empresas (`Fact_ExportacionComex`, serie principal), y la
> producción de la cuenca es la serie oficial (`Fact_ProduccionCuenca`). Los terminales marítimos (planilla 21) quedan como contraste.
> La base es el promedio de 2022: primer año con exportación en 12 de 12 meses y exportación mayor o igual al 10% de la producción de la
> cuenca. Las conclusiones usan promedios anuales y medias móviles de 12 meses, no un mes aislado.
>
> Nota (F16): el salto de enero de 2018 contra el promedio de 2019, que se citaba con un valor no reproducible, recalculado da +1.761%; con la base 2022 ese contraste ya no se usa.
>
> **Estas medidas no se pudieron ejecutar en Power BI Desktop (NO VERIFICADO).** Los valores esperados están en
> `CAMBIOS_POWERBI.md` y salen de `data/web/registro_cifras.json`.

```dax
Dias del Periodo =
SUMX(VALUES(Dim_Fecha[anio_mes]), DAY(EOMONTH(CALCULATE(MIN(Dim_Fecha[fecha])), 0)))
```
> Cuenta los días de cada mes una sola vez. El `CALCULATE` interno es necesario: sin él, el recorrido por `VALUES(anio_mes)` no filtra cada mes (un recorrido sobre una columna no cambia el contexto de filtro) y `MIN(fecha)` devuelve siempre el primer día del período, con lo que un año daba 12 × 31 = 372 días en lugar de 365 (error detectado al comparar 187.904 contra el valor esperado 191.506).

```dax
Volumen Exportado Cuenca =
CALCULATE(
    SUM(Fact_ExportacionComex[cantidad]),
    Fact_ExportacionComex[cuenca] = "Cuenca Neuquina"
)
```
> m³. Alcance: crudo de la cuenca Neuquina (Neuquén, Río Negro, La Pampa y Mendoza), convencional y no convencional, todas las vías.

```dax
Monto Exportado Cuenca (USD) =
CALCULATE(
    SUM(Fact_ExportacionComex[monto]),
    Fact_ExportacionComex[cuenca] = "Cuenca Neuquina"
)
```

```dax
Precio Implicito (USD-bbl) =
DIVIDE([Monto Exportado Cuenca (USD)], [Volumen Exportado Cuenca] * 6.2898)
```

```dax
Exportacion Cuenca (bbl-dia) =
DIVIDE([Volumen Exportado Cuenca] * 6.2898, [Dias del Periodo])
```
> 1 m³ = 6,2898 bbl, el mismo factor del resto del proyecto. Los meses sin exportación declarada cuentan como cero (hay datos desde enero de 2020).

```dax
Produccion Cuenca (bbl-dia) =
DIVIDE(SUM(Fact_ProduccionCuenca[cuenca_neuquina]) * 6.2898, [Dias del Periodo])
```

```dax
% Exportado de la Cuenca =
DIVIDE([Exportacion Cuenca (bbl-dia)], [Produccion Cuenca (bbl-dia)])
```

```dax
Indice Exportacion Cuenca (base 2022) =
VAR ValorBase = CALCULATE([Exportacion Cuenca (bbl-dia)], ALL(Dim_Fecha), Dim_Fecha[anio] = 2022)
RETURN DIVIDE([Exportacion Cuenca (bbl-dia)], ValorBase) * 100
```

```dax
Indice Produccion Cuenca (base 2022) =
VAR ValorBase = CALCULATE([Produccion Cuenca (bbl-dia)], ALL(Dim_Fecha), Dim_Fecha[anio] = 2022)
RETURN DIVIDE([Produccion Cuenca (bbl-dia)], ValorBase) * 100
```

```dax
Indice Produccion VM (base 2022) =
VAR ValorBase = CALCULATE([Prod Petroleo (bbl-dia)], ALL(Dim_Fecha), Dim_Fecha[anio] = 2022)
RETURN DIVIDE([Prod Petroleo (bbl-dia)], ValorBase) * 100
```
> Con `Dim_Fecha[anio]` en el eje o en una tarjeta con un año filtrado, dan el promedio anual. `ALL(Dim_Fecha)` limpia el filtro de fecha antes de fijar el año base.

```dax
Indice Exportacion Cuenca MA12 (base 2022) =
VAR Fin = MAX(Dim_Fecha[fecha])
VAR Ventana = DATESINPERIOD(Dim_Fecha[fecha], Fin, -12, MONTH)
VAR Base = CALCULATE(AVERAGEX(VALUES(Dim_Fecha[anio_mes]), [Exportacion Cuenca (bbl-dia)]), ALL(Dim_Fecha), Dim_Fecha[anio] = 2022)
VAR Meses = CALCULATE(COUNTROWS(VALUES(Dim_Fecha[anio_mes])), Ventana)
VAR Media = CALCULATE(AVERAGEX(VALUES(Dim_Fecha[anio_mes]), [Exportacion Cuenca (bbl-dia)]), Ventana)
RETURN IF(Meses = 12, DIVIDE(Media, Base) * 100)
```

```dax
Indice Produccion Cuenca MA12 (base 2022) =
VAR Fin = MAX(Dim_Fecha[fecha])
VAR Ventana = DATESINPERIOD(Dim_Fecha[fecha], Fin, -12, MONTH)
VAR Base = CALCULATE(AVERAGEX(VALUES(Dim_Fecha[anio_mes]), [Produccion Cuenca (bbl-dia)]), ALL(Dim_Fecha), Dim_Fecha[anio] = 2022)
VAR Meses = CALCULATE(COUNTROWS(VALUES(Dim_Fecha[anio_mes])), Ventana)
VAR Media = CALCULATE(AVERAGEX(VALUES(Dim_Fecha[anio_mes]), [Produccion Cuenca (bbl-dia)]), Ventana)
RETURN IF(Meses = 12, DIVIDE(Media, Base) * 100)
```

```dax
Indice Produccion VM MA12 (base 2022) =
VAR Fin = MAX(Dim_Fecha[fecha])
VAR Ventana = DATESINPERIOD(Dim_Fecha[fecha], Fin, -12, MONTH)
VAR Base = CALCULATE(AVERAGEX(VALUES(Dim_Fecha[anio_mes]), [Prod Petroleo (bbl-dia)]), ALL(Dim_Fecha), Dim_Fecha[anio] = 2022)
VAR Meses = CALCULATE(COUNTROWS(VALUES(Dim_Fecha[anio_mes])), Ventana)
VAR Media = CALCULATE(AVERAGEX(VALUES(Dim_Fecha[anio_mes]), [Prod Petroleo (bbl-dia)]), Ventana)
RETURN IF(Meses = 12, DIVIDE(Media, Base) * 100)
```
> Media móvil de 12 meses (promedio simple de los 12 valores mensuales), vacía mientras no haya 12 meses. No poner un filtro de año en el gráfico: dejaría la ventana sin los meses anteriores.

```dax
% Exportado por Empresa Exportadora =
DIVIDE(
    [Volumen Exportado Cuenca],
    CALCULATE([Volumen Exportado Cuenca], ALL(Fact_ExportacionComex[empresa]))
)
```
> Participación de cada razón social exportadora. `ALL(empresa)` en el denominador evita que el filtro Top N recalcule el % solo sobre las visibles. Varias empresas aparecen con más de una razón social (por ejemplo Vista, Pluspetrol y Pan American): en la versión web se agrupan; en Power BI, para igualar, agrupar en Power Query o con una tabla de equivalencias.

```dax
Volumen Terminales Neuquinos (contraste) =
CALCULATE(
    [Volumen Exportado],
    Fact_MovimientosExportacion[empresa] IN { "Oiltanking EBYTEM S.A.", "Refineria Bahia Blanca SAU" }
)
```
> Contraste con la planilla 21 (terminales marítimos): no es la serie principal.

```dax
Utilizacion % (anio mas reciente valido) =
VAR UltimoAnio =
    CALCULATE(
        MAX(Fact_CapacidadDuctos[anio]),
        Fact_CapacidadDuctos[capacidad_valida] = TRUE,
        Fact_CapacidadDuctos[capacidad_dudosa] = FALSE,
        ALL(Dim_Fecha)
    )
RETURN
    CALCULATE([Utilizacion %], Fact_CapacidadDuctos[anio] = UltimoAnio, ALL(Dim_Fecha))
```
> Equivale al ranking de la versión web: para cada ducto, el año más reciente con capacidad válida y no dudosa. Usar `Dim_Ducto[denominacion_logica]` en el eje, para que los dos `idducto` de un mismo ducto cuenten una sola vez.

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
Tiene Capacidad No Dudosa =
IF(
    CALCULATE(
        COUNTROWS(Fact_CapacidadDuctos),
        Fact_CapacidadDuctos[capacidad_valida] = TRUE,
        Fact_CapacidadDuctos[capacidad_dudosa] = FALSE
    ) > 0,
    1,
    0
)
```
> Reemplaza a `Tiene Capacidad Confiable` (F5: "confiable" solo significaba `capacidad operativa > 0`). Da 1 si el
> ducto tiene al menos un ducto-año con capacidad informada y no dudosa. Depende del contexto de fecha: con un
> filtro de año, un ducto con capacidad solo en otros años da 0. Filtrada en 0, deja en el visual de
> `Volumen Transportado (respaldo)` los ductos sin capacidad utilizable.

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
