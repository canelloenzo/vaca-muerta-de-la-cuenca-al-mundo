# Diccionario de datos — tablas limpias (data/clean/)

Generado a partir de la exploración real de los archivos en `data/raw/`. Todas las tablas se guardan en
UTF-8 (`utf-8-sig`, compatible con Power BI / Excel). Fecha de generación: 2026-08-12. Actualizado 2026-08-12
con el Anexo 2A (capacidad de transporte).

---

## fact_produccion_pozo_mes_vaca_muerta.csv
Producción mensual por pozo, filtrada a formación **Vaca Muerta** (convencional + no convencional), 2006-2025.
**205.082 filas.** Composición real: 193.886 NO CONVENCIONAL (193.548 SHALE + 240 TIGHT) vs. 11.028 CONVENCIONAL
(+144 SIN RESERVORIO, 24 NO DISCRIMINADO) — confirma que Vaca Muerta es predominantemente no convencional pero
no exclusivamente. Producción acumulada 2006-2025: ~722,4 millones de barriles de petróleo.

| Columna | Tipo | Descripción |
|---|---|---|
| fecha | date | Primer día del mes de producción (derivado de `anio`+`mes`, no existía como campo único en el crudo) |
| anio, mes | int | Año y mes calendario |
| idempresa, empresa | str | Operador del pozo |
| idpozo, sigla | str/int | Identificador y nombre de pozo |
| formprod | str | Código corto de formación productiva (ej. `VMUT`) |
| formacion | str | Nombre completo de formación, en minúsculas (`vaca muerta`) — **este es el campo correcto para filtrar**, no `formprod` |
| tipo_de_recurso | str | `CONVENCIONAL` / `NO CONVENCIONAL` / `SIN RESERVORIO` / `NO DISCRIMINADO` — Vaca Muerta tiene pozos en ambas categorías |
| sub_tipo_recurso | str | `SHALE` / `TIGHT` (solo pozos no convencionales) |
| clasificacion, subclasificacion | str | `EXPLOTACION`/`EXPLORACION`, `DESARROLLO`/`AVANZADA` |
| cuenca | str | Cuenca sedimentaria (`NEUQUINA` para Vaca Muerta) |
| provincia | str | Provincia del pozo |
| areapermisoconcesion, areayacimiento | str | Área de concesión / yacimiento |
| tipoestado, tipopozo | str | Estado operativo y tipo (`Petrolífero`/`Gasífero`) |
| prod_pet_m3 | float | Producción de petróleo, m³/mes (unidad original) |
| prod_pet_bbl | float | Producción de petróleo en barriles (`prod_pet_m3 × 6.2898`) |
| prod_gas_miles_m3 | float | Producción de gas, miles de m³/mes |
| prod_agua_m3 | float | Producción de agua, m³/mes |
| tef | float | Campo original del dataset (tiempo efectivo); **unidad no confirmada por metadata pública** — no usar sin validar contra la documentación del portal antes de construir KPIs de "días productivos" |
| dias_mes | int | Días calendario del mes — calculado, sustituye al inexistente `dias_del_mes` de la guía |
| fuente | str | `anual_2022_2025` o `no_convencional_historico_pre2022` (trazabilidad del archivo crudo de origen) |

**Filtro aplicado:** `formacion.str.contains("vaca muerta", case=False)`. La guía original proponía filtrar por
`formprod`, pero ese campo contiene códigos cortos (`VMUT`, `CENT`, `FIMP`...), no el nombre de formación.

**Deduplicación:** el archivo `produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv` solapa 100% con las
filas `NO CONVENCIONAL` de los archivos anuales 2022-2025 (verificado exactamente para 2023: 43.219/43.219 filas
coinciden). Se usó solo para aportar el histórico 2006-2021, ausente en los archivos anuales.

**Limitación conocida:** las coordenadas de pozo (ver `dim_pozo_coordenadas_no_convencional.csv`) solo existen
para pozos no convencionales — los pozos convencionales de Vaca Muerta no tienen lat/long en los datos crudos.

---

## fact_produccion_yacimiento_mes_vaca_muerta.csv
Igual que la anterior pero agregada a nivel yacimiento-provincia-mes-tipo de recurso (grano sugerido por la guía).
**15.762 filas.**

| Columna | Tipo | Descripción |
|---|---|---|
| fecha, anio, mes | date/int | Período |
| areayacimiento | str | Yacimiento |
| provincia, cuenca | str | Ubicación |
| tipo_de_recurso, sub_tipo_recurso | str | Convencional/No convencional, Shale/Tight |
| prod_pet_bbl, prod_pet_m3, prod_gas_miles_m3, prod_agua_m3 | float | Sumas mensuales |
| pozos_reportados | int | Pozos distintos con reporte en el período |
| pozos_productivos | int | Pozos distintos con `prod_pet_m3 > 0` en el período |
| dias_mes | int | Días del mes |

---

## dim_pozo_coordenadas_no_convencional.csv
Dimensión de coordenadas por pozo — **solo disponible para pozos no convencionales** (limitación de origen).
**3.335 pozos con coordenadas.** La tabla de producción Vaca Muerta tiene 3.300 pozos únicos en total, de los
cuales 3.062 son NO CONVENCIONAL — prácticamente todos cubiertos por esta dimensión (más algunos pozos que
quedan fuera del rango final por year/formación). Los pozos CONVENCIONAL de Vaca Muerta (238 pozos únicos, el
resto hasta 3.300) **no tienen coordenadas** en los datos crudos entregados.

| Columna | Tipo | Descripción |
|---|---|---|
| idpozo | str/int | Identificador de pozo (clave para unir con las tablas de producción) |
| coordenadax, coordenaday | float | Longitud, latitud (grados decimales) |

---

## fact_transporte_ductos.csv
Movimientos de hidrocarburos por ducto/tramo (fuente: `volumnenes-de-transporte-de-hidrocarburos-planilla-20.csv`, ENARGAS/Sec. Energía). Mayormente mercado interno; incluye exportación directa por ducto cuando aplica.

| Columna | Tipo | Descripción |
|---|---|---|
| empresa, idempresa | str/int | Transportista |
| fecha, anio, mes | date/int | Período |
| idducto, denominacion_ducto | int/str | Ducto — clave para unir con `dim_ducto.csv` (95.6% de cobertura; 4.4% de los ductos referenciados no están en el registro) |
| tipo_ducto | str | Oleoducto / Gasoducto / Poliducto / Propanoducto / JP Ducto |
| tipo_jurisdiccion | str | Nación / Provincial |
| nodo_origen, nodo_destino, idnodo_origen, idnodo_destino | str/int | Extremos del tramo |
| tipo_destino | str | Operación de Entrega / Devolución |
| area, cargador | str | Área operativa y empresa cargadora |
| tipo_producto | str | Petróleo / Gas / Derivados del Gas / Derivados del Petróleo / Reconstituido |
| producto | str | Producto específico, texto libre (156 grafías distintas de origen) |
| producto_norm | str | Versión normalizada (minúsculas, sin tildes, espacios colapsados) — reduce a 103 variantes; la diversidad remanente es en gran parte real (grados de gasoil, crudos importados con nombre propio) |
| tipo_mercado | str | Interno / Externo |
| volumen | float | Volumen transportado (unidad no especificada en el crudo — típicamente m³; validar contra metadata del portal) |
| longitud_ducto, longitud_tramo | float | Km |
| tipo_operacion | str | Solo se completa (`Exportacion`) en 0,9% de filas — **no usar como indicador general de exportación**, ver `es_operacion_exportacion` |
| pais | str | País destino — 99,1% nulo; solo presente en operaciones de exportación directa por ducto |
| idtramo_transporte, tramo_transporte | float/str | Tramo |
| obs | str | Observaciones libres (98,2% nulo) |
| fecha_data | str | Fecha de corte del reporte (texto original) |
| es_operacion_exportacion | bool | `tipo_operacion == "Exportacion"` — bandera booleana lista para usar |

**Hallazgo crítico:** no existe ningún campo de capacidad nominal en este archivo, ni en `dim_ducto.csv`
(solo trae longitud en km, no m³/día). El KPI de la guía "Utilización % = flujo / capacidad nominal"
**no se puede calcular con los datos entregados**.

---

## fact_movimientos_exportacion_ductos.csv
Movimientos por nodo/terminal con apertura explícita por país (fuente: `volumenes-de-transporte-de-hidrocarburos-planilla-21.csv`). Es el mejor proxy disponible para "comercio exterior por país destino" — **en volumen, no en USD**.

| Columna | Tipo | Descripción |
|---|---|---|
| empresa, cuit | str/int | Operador del nodo/terminal |
| fecha, anio, mes | date/int | Período (2018-2026) |
| idnodo, nodo_origen | int/str | Terminal de despacho |
| tipo_mercado | str | Interno / Externo |
| tipo_operacion | str | Exportación / Carga / Descarga |
| pais | str | País destino — 21 valores reales tras limpieza (Chile, Estados Unidos, China, Brasil, etc.); 63,9% nulo (operaciones internas sin país aplicable) |
| cargador | str | Empresa que carga el producto |
| producto | str | Tipo de crudo (Crudo MI, Crudo Mezcla, Crudo Liviano, etc.) |
| volumen | float | Volumen movido |
| idnodo_destino, nodo_destino | float/str | Destino, si aplica (80% nulo) |
| obs | str | Observaciones (87% nulo) |

**Limitación:** no trae valor en USD ni empresa importadora en destino — para estimar valor económico, cruzar
`producto` con `dim_tipo_crudo_cuenca.csv` (mapea tipo de crudo a cuenca) y `dim_precio_exportacion_crudo.csv`
(precio USD/bbl mensual por tipo de crudo), multiplicando volumen × precio como aproximación.

---

## dim_ducto.csv
Registro de ductos (fuente: `registro-del-midstream-ductos-empresas.csv`).

| Columna | Tipo | Descripción |
|---|---|---|
| idducto | int | Clave — une con `fact_transporte_ductos.idducto` (cobertura 95.6%) |
| denominacion | str | Nombre del ducto |
| tipo_ducto | str | Gasoducto/Oleoducto/Poliducto/Gasolinoducto/Propanoducto/JP Ducto |
| provincia | str | Provincia principal |
| tipo_jurisdiccion | str | Nación / Provincial (6,1% nulo) |
| empresa | str | Titular |
| longitud_km | float | Longitud en km (6,1% nulo) — **no es capacidad de transporte** |
| anio_construccion | Int64 | Año de construcción (6,1% nulo; incluye valores sospechosos como `1.0`, revisar antes de usar) |
| fechacargainfo | datetime | Fecha de carga del registro |
| provincias_ducto | str | Lista de provincias que atraviesa (83,7% nulo, solo ductos interprovinciales) |

---

## fact_capacidad_ductos.csv
Capacidad de transporte por ducto vs. volumen realmente transportado, a nivel **ducto-mes** (fuente: Anexo 2A
`anexo-2a-capacidad-de-transporte-de-hidrocarburos-a-travs-de-ductos.csv`, cruzado con `fact_transporte_ductos`).
**3.603 filas** (idducto × mes, 2018-2026).

| Columna | Tipo | Descripción |
|---|---|---|
| fecha, anio, mes | date/int | Período |
| idducto, denominacion_ducto, empresa, tipo_jurisdiccion | int/str | Ducto — mismas claves que `dim_ducto` y `fact_transporte_ductos` |
| n_tramos_reportados | int | Cantidad de tramos que reportó el Anexo 2A para ese ducto-año (informativo; no se usa para escalar capacidad, ver nota abajo) |
| capacidad_operativa_maxima_m3_dia | float | Capacidad operativa máxima, **m³/día** — denominador del KPI de utilización |
| capacidad_disenio_m3_dia | float | Capacidad de diseño (teórica), m³/día — alternativa más conservadora al denominador |
| capacidad_empleada_m3_dia | float | Capacidad empleada reportada por la empresa, m³/día |
| dias_mes | int | Días del mes (para llevar la capacidad diaria a base mensual) |
| capacidad_mensual_m3 | float | `capacidad_operativa_maxima_m3_dia × dias_mes` |
| volumen_transportado | float | Volumen real del mes, agregado de `fact_transporte_ductos` (todos los productos/tramos/cargadores del ducto) |
| capacidad_valida | bool | `False` en 120/3.603 filas (3,3%) donde el Anexo 2A reportó capacidad = 0 (ducto probablemente fuera de servicio o dato no cargado ese año) — `utilizacion_pct` queda nulo en esas filas en vez de `inf` |
| utilizacion_pct | float | `volumen_transportado / capacidad_mensual_m3`, nulo si `capacidad_valida = False` |

**Validaciones hechas antes de construir el KPI (detalle completo en el docstring de
`data/scripts/08_clean_capacidad_ductos.py`):**
- **Clave de unión:** `idtramo` NO es un espacio de IDs compartido entre el Anexo 2A y `fact_transporte_ductos`
  — de 88 valores de `idtramo` que coinciden numéricamente entre ambos archivos, el `idducto` asociado solo
  coincide en 1/88 (match espurio). La clave correcta y confiable es **`idducto`**.
- **Grano real del Anexo 2A:** idducto × idtramo × cargador × año. Se verificó que `capacidad_operativa_maxima`
  es idéntica entre todos los cargadores de un mismo tramo, y también idéntica entre todos los tramos de un
  mismo ducto-año (0/77 grupos con más de un tramo mostraron variación) — sumar por tramo o por cargador
  hubiera multiplicado artificialmente la capacidad real. Se dedupe a un único valor por ducto-año.
- **Unidades:** no hay columna de unidad explícita en el Anexo 2A. Se comparó `capacidad_operativa_maxima`
  contra el promedio diario de `volumen` de `fact_transporte_ductos` (volumen mensual / días del mes) para los
  mismos idducto+año: el cociente cae sistemáticamente en el orden de 1x-10x (nunca en O(1000) ni O(0.001)),
  confirmando que ambas magnitudes están en la misma unidad base (m³) pero a distinta frecuencia — capacidad
  es un caudal **diario**, volumen de `fact_transporte_ductos` es un total **mensual**. Dividir volumen mensual
  directamente por capacidad diaria sin este ajuste habría inflado artificialmente el "% de utilización" ~30x.
- **Granularidad temporal:** el Anexo 2A es **anual** (campo `dias_operativos` ≈ 365), no mensual. Para llevarlo
  a ducto-mes se replicó el mismo valor de capacidad anual en los 12 meses de ese año — es un supuesto
  (capacidad constante intra-año), no un dato medido mes a mes.

**Cobertura del cruce:** de las 756 combinaciones idducto-año con transporte real registrado en
`fact_transporte_ductos`, 311 (**41,1%**) tienen capacidad reportada en el Anexo 2A ese mismo año. A nivel fila
ducto-mes, 3.603/7.939 (**45,4%**) — la cobertura NO es total: 55% del transporte real no tiene capacidad
asociada, principalmente ductos menores/provinciales que no reportan al Anexo 2A. El KPI de utilización solo
es representativo para los ductos con cobertura, no para el universo completo.

**Calidad de los datos resultantes:** con `capacidad_valida = True`, la mediana de `utilizacion_pct` es 0,54
(rango intercuartílico 0,25-0,81) — valores fisicamente razonables. 291/3.483 filas (8,4%) superan el 100%,
concentradas en solo 6 ductos de los ~91 con datos; el caso extremo es **idducto 329 "Oleoducto AM6-AM3"**
(hasta 876x en 2023), donde `capacidad_operativa_maxima_m3_dia` = 330 pero el volumen mensual real implica un
caudal diario de ~266.000 m³ — inconsistencia que parece un error de carga en el Anexo 2A de origen (no un
error del cruce), no un caso real de sobre-operación. **Recomendación: excluir o verificar manualmente estos
6 ductos (42, 97, 149, 171, 221, 329) antes de mostrar el KPI de utilización a nivel dashboard.**

---

## dim_precio_exportacion_crudo.csv
Precios mensuales por tipo de crudo (fuente: `precio-exportacion-crudo.xlsx`, hoja "precios", reformateada de ancho a largo).

| Columna | Tipo | Descripción |
|---|---|---|
| fecha | date | Mes (2019-01 en adelante) |
| tipo_precio | str | Una de 5 series: `Futures Settlements 1st line (Bloomberg)`, `Precio FOB exportación (fuente SESCO)`, `Precio mercado interno (fuente regalías)`, `Precio FOB exportación - ICE BRENT`, `Precio mercado interno - ICE BRENT` |
| tipo_crudo | str | ICE BRENT, ESCALANTE, CAÑADON SECO, MARIA INES, SAN SEBASTIAN, MEDANITO |
| precio_usd_bbl | float | USD/barril |

**Nota:** las series `... - ICE BRENT` son **diferenciales contra el Brent** (valores negativos observados en el
crudo), no precios absolutos — no sumar directamente con las otras series sin aclarar en el dashboard.

**Limitación crítica (detectada 2026-09-10):** la serie completa cubre solo **30 meses, enero 2019 a junio
2021** — verificado contra el Excel original (`precio-exportacion-crudo.xlsx`, hoja "precios"), no es un
recorte introducido en la limpieza. **No hay ningún precio disponible para 2022 en adelante**, que es
justo el período del "boom" de exportación que el proyecto quiere narrar (2025 récord, entrada en operación de
VMOS). En la práctica esto vuelve inutilizable el KPI "Valor USD Estimado" para la parte más relevante de la
historia — solo podría mostrarse, con esta fuente, para 2019-2021. Si el valor en USD es importante para el
storytelling, hace falta conseguir una fuente de precios más actualizada (no viene en los 16 archivos
entregados); si no, descartar el KPI de USD estimado y quedarse con volumen como métrica principal de
exportación (ya es la recomendación de `plan_powerbi.md`, pero ahora aplica también al precio, no solo al
comercio exterior en USD).

---

## dim_tipo_crudo_cuenca.csv
Mapeo tipo de crudo → cuenca → provincia (fuente: `precio-exportacion-crudo.xlsx`, hoja "tipos de crudo").

| Columna | Tipo | Descripción |
|---|---|---|
| tipo_de_crudo | str | Nombre comercial del crudo (Magallanes, Hidra, San Sebastián, María Inés, Cañadón Seco, Escalante, Medanito, Mendoza Norte, Noroeste) |
| cuenca | str | Cuenca sedimentaria de origen |
| provincia | str | Provincia(s) asociadas |

---

## fact_balance_energetico_nacional.csv
Balance Energético Nacional anual, reformateado de la matriz ancha original a formato largo (fuente: `Balance_2023_V0_H.xlsx`, `Balance_2024_V0_H.xlsx`, `balance_2025_v0_h.xlsx`).

| Columna | Tipo | Descripción |
|---|---|---|
| anio | int | 2023, 2024 o 2025 — **granularidad anual, no mensual** |
| grupo_energia | str | PRIMARIA / SECUNDARIA |
| producto | str | 30 formas de energía (Petróleo, Gas Natural de Pozo, Energía Hidráulica, Carbón Mineral, Leña, Biodiesel, etc.) — no son solo hidrocarburos |
| categoria | str | OFERTA / CENTROS DE TRANSFORMACION / CONSUMO |
| subcategoria | str | Producción, Importación, Variación de Stock, Exportación y Bunker, Refinerías, Consumo Final, Transporte, etc. (24 valores) |
| valor_miles_tep | float | Valor en **miles de TEP** (tonelada equivalente de petróleo) — no está en m³, barriles ni USD |
| es_hidrocarburo | bool | `True` si `producto` es petróleo o alguno de sus derivados/subproductos de gas |

**Hallazgo crítico:** este NO es el dataset "Comercio Exterior de Hidrocarburos por país destino" que pide la
guía. Es el balance energético nacional agregado, sin apertura geográfica ni mensual. Útil solo como cifra de
contexto/validación anual (ej. "% de la producción de petróleo que se exportó en 2023"), no como fact table de
exportaciones por país.

---

## Fuentes evaluadas y dejadas fuera del modelo: Anexo 2B (almacenamiento)

Dos archivos nuevos, **explorados pero no procesados a `data/clean/`** por decisión de alcance (ver resumen al
final de este documento y sección 4 de `plan_powerbi.md`):

### anexo-2b-capacidad-de-tanques-de-almacenamiento-de-hidrocarburos.csv
Grano: **tanque individual** (720 filas). Columnas relevantes: `idnodo`, `denominacion` (terminal/planta),
`nro_tanque`, `tipo_usoplanta` (uso a terceros/propio/operativo, 44% nulo), `capacidad_operativa`,
`capacidad_reservada`, `capacidad_fuera_servicio`, `capacidad_disenio`, `cant_tanques`, `anio` (2018-2025,
snapshot anual por tanque), `habilitado`. Capacidad típica por tanque: mediana 10.000, máximo ~50.800
(unidad no confirmada, probablemente m³ por magnitud). 28 `idnodo` únicos.

### anexo-2b-por-plantas-capacidad-de-plantas-de-almacenamiento-de-hidrocarburos.csv
Grano: **planta-nodo × empresa cargadora × año** (2278 filas, mismo patrón de duplicación por cargador que el
Anexo 2A — `capacidad_operativa` se repite idéntica entre cargadores de la misma planta-año). Solo **5 `idnodo`
únicos** (19 combinaciones planta-año distintas) — dataset muy concentrado en unas pocas terminales grandes
(ej. Puerto Rosales, con capacidad operativa total ~328.386 en 2022). anio 2018-2025.

### Por qué quedan fuera del modelo por ahora
- **Dominio distinto:** capacidad de almacenamiento (stock/buffer) es una pregunta de negocio distinta a las
  tres que estructuran el proyecto (producción → transporte → exportación, todas de **flujo**). No hay ningún
  KPI de la guía original ni del plan revisado que dependa de esta tabla.
- **Cobertura de nodos débil con el resto del modelo:** de los 28 `idnodo` del Anexo 2B, solo 10 aparecen como
  origen/destino en `fact_transporte_ductos` y solo 4 en `fact_movimientos_exportacion_ductos` — el cruce
  posible es parcial, no sistemático.
- **Sesgo geográfico:** varios de los nodos con mayor capacidad (ej. Puerto Rosales) están en la cuenca Golfo
  San Jorge (Santa Cruz/Chubut), no en la cuenca Neuquina donde está Vaca Muerta — sumarlos sin filtrar
  contaminaría el storytelling específico de Vaca Muerta con infraestructura de otra cuenca.
- **Mismo patrón de limpieza que el Anexo 2A** (duplicación por cargador) — integrarlos bien llevaría un
  esfuerzo de limpieza comparable al ya hecho para capacidad de ductos, para una tabla que no responde ninguna
  pregunta planteada del dashboard actual.

**Recomendación:** dejarlos documentados acá (no en `data/clean/`) y revisarlos si en una futura iteración el
proyecto suma explícitamente un cuarto acto de "almacenamiento" a la narrativa — por ejemplo, si se quiere
mostrar que la capacidad de tanques en Neuquén es también un cuello de botella, no solo el ducto.
