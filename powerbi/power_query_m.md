# Power Query (M) — scripts listos para pegar

Cómo usar cada bloque: en Power BI Desktop, **Inicio > Transformar datos > Nueva consulta > Consulta en blanco**,
después clic derecho en la consulta > **Editor avanzado**, borrar el contenido default y pegar el bloque
correspondiente. Renombrar la consulta con el nombre que aparece en el comentario del bloque (`// nombre: ...`).

Todas las rutas asumen `clean/` en `<RUTA_AL_REPO>\clean\`. Si movés la carpeta, ajustá
la constante `Carpeta` al principio de cada bloque (o mejor: creá una consulta de parámetro `RutaClean` una sola
vez y reusala en todos los bloques — ver sección final).

---

## 0. Parámetro reusable (opcional pero recomendado)

Creá esto primero como **Nuevo parámetro** (no consulta en blanco): Inicio > Administrar parámetros > Nuevo.
- Nombre: `RutaClean`
- Tipo: Texto
- Valor actual: `<RUTA_AL_REPO>\clean\` (reemplazar `<RUTA_AL_REPO>` por la carpeta local del repositorio)

Todos los bloques de abajo usan `RutaClean` — si no querés crear el parámetro, reemplazá `RutaClean` por el
string literal de la ruta en cada bloque.

---

## ⚠️ Por qué todos los `Table.TransformColumnTypes` terminan en `"en-US"`

**Corregido 2026-09-16, tras un bug real detectado en Power BI Desktop.** Los CSV de `clean/` usan formato
numérico US (punto decimal, sin separador de miles — es lo que escribe pandas por defecto), pero cuando
`Table.TransformColumnTypes` convierte texto a número/fecha **sin especificar el locale explícitamente, usa la
configuración regional de Windows/Power BI Desktop**. En una máquina configurada en español (Argentina) —
donde el separador decimal esperado es `,` y el de miles es `.` — Power Query interpreta un valor como
`2739218.529762` borrando el punto (lo trata como separador de miles) y lo convierte en `2739218529762`
(~2,7 billones): varios órdenes de magnitud por encima de cualquier valor real. Como cada fila tiene una
cantidad distinta de decimales en cada columna, el grado de "explosión" varía fila a fila y columna a columna
— por eso el síntoma es una corrupción que no es consistente entre columnas de una misma fila. **El CSV en sí
nunca estuvo corrompido** (verificado con lectura directa en Python: `SUM(prod_pet_bbl)` da 722.439.535, igual
al total ya documentado en `diccionario_datos.md`) — el problema aparece únicamente al importar sin fijar el
locale.

**La solución es el tercer parámetro `"en-US"` en cada `Table.TransformColumnTypes(tabla, tipos, "en-US")`**
de los bloques de abajo — fuerza la interpretación de números/fechas al formato con el que se generaron los
archivos, sin importar la configuración regional de la máquina. Si armás una consulta nueva a mano más
adelante (para otro archivo, o una columna calculada), acordate de agregar siempre ese tercer parámetro.

**Cómo detectar si volvió a pasar:** después de cargar `Fact_Produccion`, fijate el total de `prod_pet_bbl` en
una tarjeta o en Power Query (`List.Sum(Fact_Produccion[prod_pet_bbl])`) — tiene que dar **~722.439.535**, no
un número con muchos más dígitos. Cualquier columna numérica con valores por encima de, digamos, unos pocos
millones en esta tabla es señal de que el locale se está interpretando mal de nuevo.

---

## 1. Fact_Produccion (grano yacimiento-mes — la tabla recomendada para el modelo)

```powerquery-m
// nombre: Fact_Produccion
let
    Origen = Csv.Document(File.Contents(RutaClean & "fact_produccion_yacimiento_mes_vaca_muerta.csv"),
        [Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {
        {"fecha", type date}, {"anio", Int64.Type}, {"mes", Int64.Type},
        {"areayacimiento", type text}, {"provincia", type text}, {"cuenca", type text},
        {"tipo_de_recurso", type text}, {"sub_tipo_recurso", type text},
        {"prod_pet_bbl", type number}, {"prod_pet_m3", type number},
        {"prod_gas_miles_m3", type number}, {"prod_agua_m3", type number},
        {"pozos_reportados", Int64.Type}, {"pozos_productivos", Int64.Type},
        {"dias_mes", Int64.Type}
    }, "en-US")
in
    Tipos
```

---

## 1B. Fact_Produccion_Pozo (grano pozo-mes — para el mapa de burbujas de la Página 2)

```powerquery-m
// nombre: Fact_Produccion_Pozo
let
    Origen = Csv.Document(File.Contents(RutaClean & "fact_produccion_pozo_mes_vaca_muerta.csv"),
        [Delimiter=",", Columns=26, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {
        {"fecha", type date}, {"anio", Int64.Type}, {"mes", Int64.Type},
        {"idempresa", type text}, {"empresa", type text},
        {"idpozo", Int64.Type}, {"sigla", type text},
        {"formprod", type text}, {"formacion", type text},
        {"tipo_de_recurso", type text}, {"sub_tipo_recurso", type text},
        {"clasificacion", type text}, {"subclasificacion", type text},
        {"cuenca", type text}, {"provincia", type text},
        {"areapermisoconcesion", type text}, {"areayacimiento", type text},
        {"tipoestado", type text}, {"tipopozo", type text},
        {"prod_pet_m3", type number}, {"prod_pet_bbl", type number},
        {"prod_gas_miles_m3", type number}, {"prod_agua_m3", type number},
        {"tef", type number}, {"dias_mes", Int64.Type}, {"fuente", type text}
    }, "en-US")
in
    Tipos
```

> `idempresa` es texto (ej. `"YPF"`), no un código numérico, a pesar del nombre — así está en el CSV, se tipa
> como `type text` para no romper la carga. `idpozo` es la clave para relacionar con `Dim_PozoCoordenadas`
> (ver relación más abajo) — cobertura verificada: 94,5% de las filas de esta tabla tienen coordenada
> (el resto son pozos convencionales, que no tienen coordenadas en el dato de origen — ver
> `diccionario_datos.md`). `tef` se carga como número pero su unidad no está confirmada contra la metadata del
> portal — no usar para KPIs de "días productivos" sin validar antes (mismo caveat que en el diccionario de
> datos).
>
> Esta tabla es la única fuente para el mapa de burbujas de la Página 2 (tamaño = producción, color =
> `sub_tipo_recurso`) porque `Fact_Produccion` (yacimiento-mes, bloque 1) no tiene grano de pozo ni coordenadas.
> Para el resto del modelo (KPIs de producción, relación con `Dim_Yacimiento`) seguí usando `Fact_Produccion`
> — no reemplaza al bloque 1, lo complementa solo para esta página.

---

## 2. Fact_TransporteDuctos

```powerquery-m
// nombre: Fact_TransporteDuctos
let
    Origen = Csv.Document(File.Contents(RutaClean & "fact_transporte_ductos.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {
        {"fecha", type date}, {"anio", Int64.Type}, {"mes", Int64.Type},
        {"idducto", Int64.Type}, {"denominacion_ducto", type text},
        {"tipo_ducto", type text}, {"tipo_jurisdiccion", type text},
        {"idnodo_origen", Int64.Type}, {"nodo_origen", type text},
        {"idnodo_destino", Int64.Type}, {"nodo_destino", type text}, {"tipo_destino", type text},
        {"area", type text}, {"cargador", type text},
        {"tipo_producto", type text}, {"producto", type text}, {"producto_norm", type text},
        {"tipo_mercado", type text}, {"volumen", type number},
        {"longitud_ducto", type number}, {"longitud_tramo", type number},
        {"tipo_operacion", type text}, {"pais", type text},
        {"idtramo_transporte", type number}, {"tramo_transporte", type text},
        {"obs", type text}, {"fecha_data", type text},
        {"es_operacion_exportacion", type logical},
        {"empresa", type text}, {"idempresa", Int64.Type}
    }, "en-US")
in
    Tipos
```

---

## 3. Fact_CapacidadDuctos

```powerquery-m
// nombre: Fact_CapacidadDuctos
let
    Origen = Csv.Document(File.Contents(RutaClean & "fact_capacidad_ductos.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {
        {"fecha", type date}, {"anio", Int64.Type}, {"mes", Int64.Type},
        {"idducto", Int64.Type}, {"denominacion_ducto", type text},
        {"empresa", type text}, {"tipo_jurisdiccion", type text},
        {"n_tramos_reportados", Int64.Type},
        {"capacidad_operativa_maxima_m3_dia", type number},
        {"capacidad_disenio_m3_dia", type number},
        {"capacidad_empleada_m3_dia", type number},
        {"dias_mes", Int64.Type}, {"capacidad_mensual_m3", type number},
        {"volumen_transportado", type number},
        {"capacidad_valida", type logical}, {"utilizacion_pct", type number}
    }, "en-US"),
    // Excluir los 6 ductos con utilizacion sospechosa detectados en la limpieza (ver diccionario_datos.md)
    ExcluirDuctosSospechosos = Table.SelectRows(Tipos, each not List.Contains({42, 97, 149, 171, 221, 329}, [idducto]))
in
    ExcluirDuctosSospechosos
```

> Se filtran acá los 6 `idducto` con utilización >5x (error de carga del Anexo 2A en origen, según
> `diccionario_datos.md`) para no arrastrar el problema a las medidas DAX. Si preferís mantenerlos visibles con
> una bandera en vez de excluirlos, sacá el paso `ExcluirDuctosSospechosos` y filtrá en la medida DAX en su lugar.

---

## 4. Fact_MovimientosExportacion

```powerquery-m
// nombre: Fact_MovimientosExportacion
let
    Origen = Csv.Document(File.Contents(RutaClean & "fact_movimientos_exportacion_ductos.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {
        {"empresa", type text}, {"cuit", type text},
        {"fecha", type date}, {"anio", Int64.Type}, {"mes", Int64.Type},
        {"idnodo", Int64.Type}, {"nodo_origen", type text},
        {"tipo_mercado", type text}, {"tipo_operacion", type text}, {"pais", type text},
        {"cargador", type text}, {"producto", type text}, {"volumen", type number},
        {"idnodo_destino", type number}, {"nodo_destino", type text}, {"obs", type text},
        {"fecha_data", type text}
    }, "en-US")
in
    Tipos
```

---

## 5. Fact_PrecioCrudo

```powerquery-m
// nombre: Fact_PrecioCrudo
let
    Origen = Csv.Document(File.Contents(RutaClean & "dim_precio_exportacion_crudo.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {
        {"fecha", type date}, {"tipo_precio", type text},
        {"tipo_crudo", type text}, {"precio_usd_bbl", type number}
    }, "en-US")
in
    Tipos
```

---

## 6. Fact_BalanceEnergetico

```powerquery-m
// nombre: Fact_BalanceEnergetico
let
    Origen = Csv.Document(File.Contents(RutaClean & "fact_balance_energetico_nacional.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {
        {"anio", Int64.Type}, {"grupo_energia", type text}, {"producto", type text},
        {"categoria", type text}, {"subcategoria", type text},
        {"valor_miles_tep", type number}, {"es_hidrocarburo", type logical}
    }, "en-US")
in
    Tipos
```

---

## 7. Dim_Ducto

```powerquery-m
// nombre: Dim_Ducto
let
    Origen = Csv.Document(File.Contents(RutaClean & "dim_ducto.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {
        {"idducto", Int64.Type}, {"denominacion", type text}, {"tipo_ducto", type text},
        {"provincia", type text}, {"tipo_jurisdiccion", type text}, {"empresa", type text},
        {"longitud_km", type number}, {"anio_construccion", Int64.Type},
        {"fechacargainfo", type datetime}, {"provincias_ducto", type text}
    }, "en-US")
in
    Tipos
```

---

## 8. Dim_TipoCrudo

```powerquery-m
// nombre: Dim_TipoCrudo
let
    Origen = Csv.Document(File.Contents(RutaClean & "dim_tipo_crudo_cuenca.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {
        {"tipo_de_crudo", type text}, {"cuenca", type text}, {"provincia", type text}
    }, "en-US")
in
    Tipos
```

---

## 9. Dim_PozoCoordenadas

```powerquery-m
// nombre: Dim_PozoCoordenadas
let
    Origen = Csv.Document(File.Contents(RutaClean & "dim_pozo_coordenadas_no_convencional.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {
        {"idpozo", type text}, {"coordenadax", type number}, {"coordenaday", type number}
    }, "en-US")
in
    Tipos
```

---

## 10. Dim_Fecha (tabla de fechas, cubre el rango de todas las fact tables)

Requiere que `Fact_Produccion`, `Fact_TransporteDuctos` y `Fact_MovimientosExportacion` ya existan como consultas
(Power Query resuelve el orden de dependencia solo).

```powerquery-m
// nombre: Dim_Fecha
let
    FechaMin = List.Min({
        List.Min(Fact_Produccion[fecha]),
        List.Min(Fact_TransporteDuctos[fecha]),
        List.Min(Fact_MovimientosExportacion[fecha])
    }),
    FechaMax = List.Max({
        List.Max(Fact_Produccion[fecha]),
        List.Max(Fact_TransporteDuctos[fecha]),
        List.Max(Fact_MovimientosExportacion[fecha])
    }),
    Calendario = List.Dates(
        Date.From(FechaMin),
        Duration.Days(Date.From(FechaMax) - Date.From(FechaMin)) + 1,
        #duration(1, 0, 0, 0)
    ),
    ATabla = Table.FromList(Calendario, Splitter.SplitByNothing(), {"fecha"}),
    Tipada = Table.TransformColumnTypes(ATabla, {{"fecha", type date}}),
    ConColumnas = Table.AddColumn(Table.AddColumn(Table.AddColumn(Table.AddColumn(
        Tipada, "anio", each Date.Year([fecha]), Int64.Type),
        "mes", each Date.Month([fecha]), Int64.Type),
        "nombre_mes", each Date.MonthName([fecha]), type text),
        "anio_mes", each Date.ToText([fecha], "yyyy-MM"), type text)
in
    ConColumnas
```

> Nota: esto genera una fila por **día**, no por mes — es la práctica estándar de Power BI para habilitar
> `SAMEPERIODLASTYEAR` y jerarquías de fecha nativas. Si el modelo se siente pesado (poco probable con este
> volumen de datos), se puede colapsar a una fila por mes quitando `List.Dates` diario y generando una lista
> mensual con `List.DateNames` — no debería hacer falta acá.

Marcar esta tabla como **tabla de fechas** en Power BI: clic derecho en `Dim_Fecha` en el panel de modelo >
**Marcar como tabla de fechas** > columna `fecha`.

---

## 11. Dim_Yacimiento

```powerquery-m
// nombre: Dim_Yacimiento
let
    Base = Table.SelectColumns(Fact_Produccion, {"areayacimiento", "provincia", "cuenca"}),
    Distintos = Table.Distinct(Base)
in
    Distintos
```

> `areayacimiento` alcanza como clave por sí sola (146 yacimientos, verificado sin ningún caso de un mismo
> `areayacimiento` con más de una `provincia` o `cuenca` distinta) — `provincia`/`cuenca` quedan como atributos
> de la dimensión, no hace falta una clave compuesta para la relación (ver tabla de relaciones más abajo).

---

## 12. Dim_Pais

```powerquery-m
// nombre: Dim_Pais
let
    Base = Table.SelectColumns(Fact_MovimientosExportacion, {"pais"}),
    SinNulos = Table.SelectRows(Base, each [pais] <> null and [pais] <> ""),
    Distintos = Table.Distinct(SinNulos)
in
    Distintos
```

---

## Relaciones a crear (vista de modelo)

| Desde | Campo | Hacia | Campo | Cardinalidad |
|---|---|---|---|---|
| Fact_Produccion | fecha | Dim_Fecha | fecha | muchos-a-uno |
| Fact_Produccion | areayacimiento | Dim_Yacimiento | areayacimiento | muchos-a-uno |
| Fact_Produccion_Pozo | fecha | Dim_Fecha | fecha | muchos-a-uno |
| Fact_Produccion_Pozo | idpozo | Dim_PozoCoordenadas | idpozo | muchos-a-uno |
| Fact_TransporteDuctos | fecha | Dim_Fecha | fecha | muchos-a-uno |
| Fact_TransporteDuctos | idducto | Dim_Ducto | idducto | muchos-a-uno |
| Fact_CapacidadDuctos | fecha | Dim_Fecha | fecha | muchos-a-uno |
| Fact_CapacidadDuctos | idducto | Dim_Ducto | idducto | muchos-a-uno |
| Fact_MovimientosExportacion | fecha | Dim_Fecha | fecha | muchos-a-uno |
| Fact_MovimientosExportacion | pais | Dim_Pais | pais | muchos-a-uno |
| Fact_PrecioCrudo | fecha | Dim_Fecha | fecha | muchos-a-uno |
| Fact_BalanceEnergetico | *(sin relación — tabla de contexto aislada, ver plan_powerbi.md)* | | | |

**No** relaciones directamente `Fact_TransporteDuctos` con `Fact_CapacidadDuctos` — ambas cuelgan de `Dim_Ducto`
y `Dim_Fecha` por separado (el plan ya lo señala para evitar relaciones muchos-a-muchos).

La relación `Fact_Produccion_Pozo[idpozo]` ↔ `Dim_PozoCoordenadas[idpozo]` cubre el 94,5% de las filas — el
resto son pozos **convencionales**, que no tienen coordenadas en el dato de origen (ver `diccionario_datos.md`).
En el mapa de burbujas de la Página 2 esos pozos simplemente no van a aparecer (sin coordenada no hay dónde
ubicarlos); no hace falta ningún tratamiento especial en Power Query para esto, pero vale la pena una nota en
el dashboard aclarando que el mapa muestra producción no convencional, no el 100% de Vaca Muerta.

Para el cruce opcional de `Fact_MovimientosExportacion[producto]` con `Dim_TipoCrudo[tipo_de_crudo]` y de ahí con
`Fact_PrecioCrudo[tipo_crudo]` (para el "Valor USD Estimado"), lo más simple es resolverlo con `LOOKUPVALUE` en
DAX en vez de una relación de modelo, porque `producto` (texto libre) y `tipo_de_crudo` no calzan 1:1 sin
normalizar primero — ver medida `Valor USD Estimado` en `dax_measures.md`.
