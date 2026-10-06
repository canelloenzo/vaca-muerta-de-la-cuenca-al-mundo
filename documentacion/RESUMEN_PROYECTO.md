> **Nota:** documento de trabajo del proceso. El modelo final de Power BI tiene 6 páginas (ver `README.md`).

# Vaca Muerta — resumen del proyecto (para retomar en una conversación nueva)

Generado 2026-09-10. Este documento es autocontenido: resume todo lo que se armó hasta ahora para poder
consultarlo en una conversación nueva sin tener que releer todos los archivos del proyecto.

---

## 1. Qué es el proyecto

Dashboard de Power BI **"Vaca Muerta: de la cuenca al mundo"**, contado en tres actos: **producción** (de
dónde sale el petróleo/gas no convencional) → **transporte** (oleoductos/gasoductos, con VMOS/Oldelval como
punto de tensión) → **exportación** (adónde va, por país). El gancho de timing: 2025 fue año récord de
exportación desde Vaca Muerta y VMOS está por entrar en operación.

Está pensado para terminar en un posteo de LinkedIn con una conclusión de negocio (infraestructura logística
como techo de crecimiento del sector), no solo como ejercicio técnico.

---

## 2. Estado del pipeline

```
raw/ (16 archivos: CSV + XLSX, energia.gob.ar / ENARGAS)
   │  scripts/01-08 (Python, pandas)
   ▼
clean/ (9 tablas CSV, UTF-8, listas para Power BI)
   │  powerbi/power_query_m.md + powerbi/dax_measures.md (Power Query + DAX ya escritos)
   ▼
Power BI Desktop  ← ACÁ ESTAMOS: falta cargar, relacionar y armar las páginas
```

- `scripts/01` a `07`: limpieza de producción, transporte, balance/precios, perfilado, sanity checks,
  exploración de anexos.
- `scripts/08_clean_capacidad_ductos.py`: cruza el Anexo 2A de capacidad con el transporte real — este es el
  script más delicado del pipeline (ver limitaciones en sección 6).
- `scripts/09_explore_comercio_exterior.py`: exploración de `TD_comercioexterior.xlsx` (ver sección 6.1 — se
  descartó).
- **Nada de esto se cargó todavía en Power BI Desktop** — es la app que no puedo operar yo directamente (es
  una GUI de escritorio, no tiene CLI). Lo que sí dejé listo son los scripts de Power Query (M) y las medidas
  DAX para pegar directo.

---

## 3. Las 9 tablas limpias (`clean/`)

| Tabla | Grano | Filas | Rol en el modelo |
|---|---|---|---|
| `fact_produccion_pozo_mes_vaca_muerta.csv` | pozo-mes | 205.082 | detalle, no se carga al modelo estrella (ver `fact_produccion_yacimiento...` para eso) |
| `fact_produccion_yacimiento_mes_vaca_muerta.csv` | yacimiento-provincia-mes | 15.762 | **Fact_Produccion** — tabla de hechos de producción |
| `fact_transporte_ductos.csv` | empresa-ducto-tramo-producto-mes | 56.566 | **Fact_TransporteDuctos** — movimientos internos/externos por ducto |
| `fact_capacidad_ductos.csv` | ducto-mes | 3.603 | **Fact_CapacidadDuctos** — cruce con Anexo 2A, habilita el KPI de utilización |
| `fact_movimientos_exportacion_ductos.csv` | nodo-empresa-producto-país-mes | 3.543 | **Fact_MovimientosExportacion** — mejor proxy de exportación por país (volumen, no USD) |
| `dim_precio_exportacion_crudo.csv` | tipo_crudo-tipo_precio-mes | 480 | **Fact_PrecioCrudo** — precios USD/bbl, **solo ene-2019 a jun-2021** (ver 6.3) |
| `dim_tipo_crudo_cuenca.csv` | tipo de crudo | 9 | **Dim_TipoCrudo** — mapeo crudo→cuenca/provincia |
| `dim_ducto.csv` | ducto | 362 | **Dim_Ducto** — registro de ductos, clave `idducto` |
| `dim_pozo_coordenadas_no_convencional.csv` | pozo (solo NC) | 3.335 | **Dim_PozoCoordenadas** — solo pozos no convencionales tienen coordenadas |
| `fact_balance_energetico_nacional.csv` | producto-categoría-año (nacional) | 2.160 | **Fact_BalanceEnergetico** — tabla de contexto anual, aislada, sin FK al resto |

Diccionario de datos completo, columna por columna: `clean/diccionario_datos.md`.

---

## 4. Modelo de datos (esquema estrella)

```
                              Dim_Fecha
                                  │
        ┌─────────────┬──────────┼───────────┬──────────────┐
        │             │          │           │              │
  Dim_Yacimiento   (no usar)  Fact_Produccion  Dim_Ducto ──── Fact_Capacidad
   (areayacimiento,                              │              Ductos
    provincia, cuenca                       Fact_Transporte
    como atributos)                            Ductos

                                              Dim_Pais ── Fact_Movimientos
                                                              Exportacion
                                                                    │
                                                            Dim_TipoCrudo ── Fact_PrecioCrudo

  Fact_BalanceEnergetico (aislada, sin relaciones)
```

Relaciones exactas (columna por columna) en `powerbi/power_query_m.md`, sección "Relaciones a crear". Puntos
clave:
- `Dim_Yacimiento` se relaciona por **`areayacimiento` solo** (verificado: 146 yacimientos, cero colisiones
  con provincia/cuenca — no hace falta clave compuesta).
- `Fact_TransporteDuctos` y `Fact_CapacidadDuctos` **no se relacionan directamente entre sí** — ambas cuelgan
  de `Dim_Ducto` y `Dim_Fecha` por separado, para evitar una relación muchos-a-muchos.
- `Fact_BalanceEnergetico` queda sin relaciones (tabla de contexto anual/nacional).

---

## 5. KPIs por grupo (fórmulas DAX ya escritas y verificadas en `powerbi/dax_measures.md`)

**Grupo A — Producción:** `Prod Petroleo (bbl-dia)`, `Var Interanual Prod`, `Rank Yacimiento` (+ filtro visual
Top N, no `TOPN` como medida), `% Produccion No Convencional`.

**Grupo B — Transporte:** `Utilizacion %` (filtrando `capacidad_valida=TRUE`, ya excluidos los 6 ductos con
dato sospechoso), `Volumen Transportado (respaldo)` para ductos sin capacidad reportada, `% Ductos con
Capacidad Reportada` (nota de cobertura).

**Grupo C — Exportación:** `Volumen Exportado` (filtro `tipo_operacion = "Exportacion"`), `% Pais`, `Var
Interanual Exportacion`, `Ratio Exportado (vol)`, `Valor USD Estimado` (opcional — **ver limitación grave en
sección 6.3, casi no sirve como está**).

**Grupo D — Contexto:** `% Exportado sobre Produccion` (anual, nacional, filtro `SEARCH("petr", ...)` sobre
`producto`, `subcategoria` en mayúsculas sin tilde).

---

## 6. Limitaciones y decisiones de alcance conocidas

### 6.1. No hay comercio exterior en USD por país
El dataset ideal (exportaciones en USD por país, de datos.energia.gob.ar) no vino en el lote de `raw/`. Se
exploró `TD_comercioexterior.xlsx` (aparecido después, sin estar en el alcance original) y **se descartó**: es
un export de tabla dinámica de un solo mes (agosto 2025), con el filtro de país colapsado en "(Todas)" — no
tiene ni serie temporal ni apertura geográfica. No cierra la brecha.

**Decisión vigente:** exportación se mide en **volumen** (`Fact_MovimientosExportacion`), no en USD.

### 6.2. Capacidad de ductos — cobertura parcial
El Anexo 2A permite calcular `Utilizacion %`, pero solo cubre ~45% de los ducto-mes con transporte real (el
resto son ductos menores/provinciales sin reporte). Además, 6 ductos (`idducto` 42, 97, 149, 171, 221, 329)
tienen utilización absurda (hasta 876x) por un error de carga en el Anexo 2A de origen — ya excluidos en la
consulta de Power Query. Para el 55% sin cobertura, usar `Volumen Transportado (respaldo)` en vez de forzar un
% sin denominador confiable.

### 6.3. Precios de crudo — cobertura muy corta (hallazgo de este control final)
`dim_precio_exportacion_crudo.csv` solo cubre **enero 2019 a junio 2021** (30 meses) — verificado contra el
Excel original, no es un recorte de la limpieza. **No hay precio para 2022 en adelante**, que es justo el
período del boom de exportación que el proyecto quiere narrar. La medida `Valor USD Estimado` va a devolver
blanco para toda la parte interesante de la historia. Recomendación: no invertir tiempo en el mapeo
producto→crudo para esta medida a menos que consigas una fuente de precios más actualizada — con los datos
actuales, casi no aporta.

### 6.4. Encoding — no era un problema real (corregido en este control)
Se había documentado (en `plan_powerbi.md` y en el docstring de `scripts/01_clean_produccion.py`) que había
"pérdida irreversible de caracteres" en los crudos (ej. cuenca "ÑIRIHUAU" apareciendo como "ÃIRIHUAU"/"�"). Se
verificó a nivel de bytes: **es un diagnóstico equivocado**. Los archivos crudos son UTF-8 correcto (`0xC3
0x91` = "Ñ", codificación válida). El mojibake era autoinfligido: `01_clean_produccion.py` lee esos CSV con
`encoding="latin-1"` (equivocado) y después repara el daño con `ftfy` + un diccionario manual. Funciona en la
práctica — se verificó que `clean/` no tiene caracteres de reemplazo reales — pero es una vuelta innecesaria.
Power BI va a mostrar los nombres con tilde correctamente, sin problema.

### 6.5. Locale de Power Query — corregido, era el bug más peligroso hasta ahora (2026-09-16)
Al importar en Power BI Desktop, ~13% de las filas de `Fact_Produccion` mostraban valores del orden de E+12/E+15
en `prod_pet_bbl`/`prod_pet_m3`/`prod_gas_miles_m3`, sin patrón consistente entre columnas de una misma fila.
**El CSV nunca estuvo corrompido** (verificado leyéndolo directo: `SUM(prod_pet_bbl)` = 722.439.535, igual al
total ya documentado). La causa era que ninguno de los scripts de `power_query_m.md` fijaba el locale al
convertir texto a número — en una máquina con configuración regional en español, Power Query interpreta el
punto decimal de los CSV (formato US, generados por pandas) como separador de miles y borra la coma... el punto,
inflando el número varios órdenes de magnitud. Como la cantidad de decimales varía por fila/columna, el grado de
inflación también varía — de ahí la inconsistencia entre columnas.

**Corregido:** los 9 bloques de `power_query_m.md` ahora pasan `"en-US"` como tercer parámetro de
`Table.TransformColumnTypes`, forzando la interpretación correcta sin importar el locale de la máquina. Esto
afectaba potencialmente **todas** las columnas numéricas del modelo, no solo producción — si ya habías cargado
alguna consulta en Power BI Desktop antes de este fix, hay que volver a pegar el bloque actualizado y refrescar.
**Cómo verificar que quedó bien:** el total de `prod_pet_bbl` en `Fact_Produccion` tiene que dar ~722.439.535,
no un número con muchos más dígitos.

### 6.6. Otras limitaciones ya conocidas (sin cambios)
- Coordenadas de pozo solo existen para pozos **no convencionales** (3.335 de ~3.300 pozos únicos; los ~238
  convencionales no se pueden ubicar en el mapa).
- Anexo 2B (capacidad de almacenamiento/tanques) se evaluó y quedó **fuera del modelo**: dominio distinto
  (stock, no flujo), cobertura débil de nodos, sesgo geográfico a Golfo San Jorge. Documentado en
  `diccionario_datos.md` por si se agrega un "cuarto acto" de almacenamiento más adelante.
- Vaca Muerta no es 100% no convencional (193.886 NO CONVENCIONAL vs. 11.028 CONVENCIONAL) — si el proyecto
  quiere hablar específicamente de "shale", filtrar además por `sub_tipo_recurso == 'SHALE'`.

---

## 7. Qué falta hacer (dentro de Power BI Desktop)

1. Abrir Power BI Desktop, crear el parámetro `RutaClean` (ver `powerbi/power_query_m.md` sección 0).
2. Pegar los 12 bloques de Power Query (bloques 1 a 9 = tablas fuente; 10-12 = `Dim_Fecha`, `Dim_Yacimiento`,
   `Dim_Pais` calculadas). **Después de cargar `Fact_Produccion`, verificar que `SUM(prod_pet_bbl)` dé
   ~722.439.535** (ver sección 6.5) antes de seguir — si da un número con muchos más dígitos, el locale se
   está interpretando mal de nuevo.
3. Armar las relaciones según la tabla de la sección 4 de este resumen (o la sección completa en
   `power_query_m.md`).
4. Crear una tabla de medidas vacía y pegar las medidas de `powerbi/dax_measures.md`, grupo por grupo (A, B,
   C, D) — ya vienen con las correcciones de este control (ver sección 8).
5. Construir las 5 páginas del dashboard (resumen ejecutivo, mapa de producción, evolución temporal, destinos
   de exportación, infraestructura/cuello de botella) — detalle de cada una en `plan_powerbi.md` sección 5.
6. Pulido visual + redacción del posteo de LinkedIn.

---

## 8. Qué se corrigió en los controles finales (2026-09-10 a 2026-09-21)

| # | Hallazgo | Dónde se corrigió |
|---|---|---|
| 1 | Faltaban columnas reales (`idnodo_origen`, `idnodo_destino`, `idtramo_transporte`, `tramo_transporte`, `obs`, `fecha_data`) en el tipado M de `Fact_TransporteDuctos`/`Fact_MovimientosExportacion` | `powerbi/power_query_m.md` |
| 2 | `Prod Petroleo` sumaba `dias_mes` en vez de promediarlo (se infla con más de un yacimiento en contexto) | `powerbi/dax_measures.md` |
| 3 | `Top Yacimientos` usaba `TOPN` como medida escalar (no es válido en DAX) | `powerbi/dax_measures.md` (reemplazado por `RANKX` + filtro visual Top N) |
| 4 | `Dim_Yacimiento` se planteaba con clave compuesta innecesaria | `powerbi/power_query_m.md` (clave simple `areayacimiento`, verificada única) |
| 5 | **"Encoding corrompido en origen" era un diagnóstico falso** — mojibake autoinfligido por leer UTF-8 como latin-1 | `plan_powerbi.md`, `powerbi/dax_measures.md`, `scripts/01_clean_produccion.py` |
| 6 | **(09-16) Ningún bloque de Power Query fijaba el locale** — al importar en una máquina en español, todas las columnas numéricas de las 9 tablas corrían riesgo de inflarse varios órdenes de magnitud (detectado por el usuario en `Fact_Produccion`, ~13% de filas afectadas al importar) | `powerbi/power_query_m.md` (agregado `"en-US"` como tercer parámetro en los 9 `Table.TransformColumnTypes`) |
| 7 | **(09-16, detectado por el usuario probando slicers de año) `Prod Petroleo (bbl-dia)` se inflaba ~12x con un año completo filtrado** (`AVERAGE(dias_mes)` no escala con más de un mes en contexto) **y `Var Interanual Prod` siempre daba -100%** (`LASTDATE(Dim_Fecha[fecha])` apunta al 31/12 calendario, que nunca tiene datos porque `Fact_Produccion` es mensual). La corrección propuesta inicialmente (`COUNTROWS(Dim_Fecha)`) se descartó por generar un bug nuevo y más difícil de detectar (relación `Dim_Fecha`→`Fact_Produccion` de un solo sentido) — se usó en su lugar `SUMX(VALUES(fecha), CALCULATE(AVERAGE(dias_mes)))` + `DATEADD` | `powerbi/dax_measures.md` (Grupo A y, preventivamente, Grupo C) |
| 8 | **(09-21, detectado por el usuario) El mes base de `Indice Exportacion (base 100)` (enero 2018) no era representativo** — ese mes tiene 1 sola empresa reportando (vs. 3-4 en 2019-2023) y volumen ~18-20x más bajo que el promedio real, por cobertura de reporte incompleta, no por menor exportación física. Cambiado a promedio de los 12 meses de 2019 (primer año con cobertura de reporte estable); se alineó `Indice Produccion` a la misma base por consistencia del gráfico comparativo | `powerbi/dax_measures.md` (Grupo E) |
| 9 | **(09-21, detectado por el usuario en Power BI) Las medidas de índice del punto 8 daban exactamente 100 para cualquier mes de 2019, y probablemente en blanco para todos los demás años** — `CALCULATE(..., Dim_Fecha[anio]=2019)` no reemplaza un filtro previo sobre `Dim_Fecha[fecha]` (columna distinta de la misma tabla, se combinan con AND) cuando la medida se usa en un gráfico con esa columna en el eje. Corregido agregando `ALL(Dim_Fecha)` antes del filtro de año en el mismo `CALCULATE` | `powerbi/dax_measures.md` (Grupo E) |
| 6 | **Tabla de precios de crudo solo cubre 2019-2021**, no descubierto hasta ahora — invalida `Valor USD Estimado` para el período relevante | `clean/diccionario_datos.md`, `powerbi/dax_measures.md` |

Verificaciones hechas sin encontrar problemas (para que sepas que se revisaron): unicidad de `idducto` en
`dim_ducto` y de `idpozo` en `dim_pozo_coordenadas`, ausencia de fechas nulas en las 5 tablas con columna
`fecha`, encoding real de tipos booleanos (`capacidad_valida`, `es_operacion_exportacion`), y el caso
`pais = "ARGENTINA"` en movimientos de exportación (son 72 filas de mercado **interno**, `tipo_operacion` nulo
— la medida `Volumen Exportado` ya las excluye correctamente al filtrar por `tipo_operacion = "Exportacion"`).

---

## 9. Archivos de referencia (rutas del proyecto original; en el repositorio, ver la estructura en `README.md`)

- `plan_powerbi.md` — plan revisado contra los datos reales (reemplaza secciones 4-7 de la guía original)
- `clean/diccionario_datos.md` — diccionario de datos completo, columna por columna, con todos los caveats
- `powerbi/power_query_m.md` — scripts M listos para pegar en Power Query
- `powerbi/dax_measures.md` — medidas DAX listas para pegar
- `raw/guia_proyecto_vaca_muerta.md` — guía original (histórica; las secciones 4-7 están reemplazadas por
  `plan_powerbi.md`, pero las secciones 1-3 siguen siendo el contexto narrativo del proyecto)
