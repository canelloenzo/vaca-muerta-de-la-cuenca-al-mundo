# Vaca Muerta: de la cuenca al mundo

Proyecto de análisis de datos públicos sobre la formación Vaca Muerta (cuenca Neuquina, Argentina), contado en
tres actos:

1. **Producción**: de dónde sale el petróleo y el gas no convencional (producción mensual por pozo y por
   yacimiento, 2006-2025).
2. **Transporte**: cómo se mueve por oleoductos y gasoductos, y qué tan cerca de su capacidad operan los ductos.
   La página de transporte del reporte de Power BI incluye un cuadro con los hitos previstos de VMOS.
3. **Exportación**: adónde va, por país de destino y por empresa.

El pipeline limpia los archivos crudos en Python (pandas). Las tablas resultantes alimentan un modelo de Power BI
(esquema estrella, Power Query M y medidas DAX documentadas) y una versión web del dashboard.

---

## Estado

- **Modelo de Power BI:** terminado, 6 páginas.
- **Dashboard web** (`docs/index.html`): terminado.

- Dashboard web: [URL_PAGES]
- Power BI (.pbix): descargar desde Releases → [URL_RELEASE]

---

## Páginas del reporte de Power BI

1. Vaca Muerta: de la cuenca al mundo (resumen)
2. Acto I · Producción: de dónde sale el petróleo
3. Producción vs. exportación: la brecha se sostiene y crece desde 2023
4. Acto II · Transporte: ductos que superan el 100% de su capacidad informada
5. Acto III · Exportación: adónde va
6. Acto III · Exportación: quién la despacha y por qué es tan irregular

---

## Estructura del repositorio

```
├── README.md
├── .gitignore
├── requirements.txt
├── docs/
│   └── index.html                 # dashboard web autocontenido (datos embebidos, Chart.js por CDN)
├── scripts/                       # pipeline de limpieza y exportación (Python)
├── powerbi/
│   ├── power_query_m.md           # consultas M listas para pegar en Power Query
│   ├── dax_measures.md            # medidas DAX (grupos A-F) con las correcciones documentadas
│   └── tema_vaca_muerta_v2.json   # tema de colores/tipografía para Power BI
├── documentacion/
│   ├── diccionario_datos.md       # diccionario columna por columna de las tablas limpias
│   ├── plan_powerbi.md            # plan del modelo y KPIs revisado contra los datos reales
│   └── RESUMEN_PROYECTO.md        # resumen general, limitaciones y registro de correcciones
└── data/
    └── web/                       # 8 tablas resumen generadas por scripts/10_export_web_data.py
```

Las carpetas `raw/` (archivos crudos, ~1,4 GB) y `clean/` (tablas limpias) **no están en el repositorio** (ver
`.gitignore`). Para reproducir el pipeline hay que descargar los crudos y ubicarlos en `raw/`, en la raíz del repo.

> Los documentos de `documentacion/` y `powerbi/` mencionan rutas del proyecto original (por ejemplo
> `clean/diccionario_datos.md` o `data/raw/`). En este repositorio el diccionario está en
> `documentacion/diccionario_datos.md`, y los scripts esperan `raw/` y `clean/` en la raíz.

---

## Fuentes de datos

Según `RESUMEN_PROYECTO.md`, `raw/` tiene 16 archivos CSV/XLSX de **energia.gob.ar / ENARGAS**. El dashboard
web cita como fuentes **datos.energia.gob.ar** y **ENARGAS**. La fuente puntual de cada archivo solo figura donde
está documentada:

| Archivo(s) en `raw/` | Contenido | Fuente documentada |
|---|---|---|
| `produccin-de-pozos-de-gas-y-petrleo-2022.csv` … `-2025.csv` | Producción mensual por pozo, convencional + no convencional, 2022-2025 | Dataset "Producción de Petróleo y Gas por Pozo": `datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo` (URL citada en la guía original del proyecto) |
| `produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv` | Producción por pozo, solo no convencional, histórico con coordenadas | Probablemente el mismo dataset de producción por pozo (deducido por el nombre del archivo, no confirmado en el portal) |
| `volumnenes-de-transporte-de-hidrocarburos-planilla-20.csv` | Movimientos por ducto/tramo | Dataset "Transporte de Hidrocarburos" de datos.energia.gob.ar |
| `volumenes-de-transporte-de-hidrocarburos-planilla-21.csv` | Movimientos por nodo/terminal, con país de destino | Dataset "Transporte de Hidrocarburos" de datos.energia.gob.ar |
| `registro-del-midstream-ductos-empresas.csv` | Registro de ductos (dimensión) | Dataset "Transporte de Hidrocarburos" de datos.energia.gob.ar |
| `anexo-2a-capacidad-de-transporte-de-hidrocarburos-a-travs-de-ductos.csv` | Capacidad de transporte por ducto (anual) | Dataset "Transporte de Hidrocarburos" de datos.energia.gob.ar |
| `anexo-2b-capacidad-de-tanques-de-almacenamiento-de-hidrocarburos.csv`, `anexo-2b-por-plantas-…csv` | Capacidad de almacenamiento (evaluado, **fuera del modelo**) | Dataset "Transporte de Hidrocarburos" de datos.energia.gob.ar |
| `Balance_2023_V0_H.xlsx`, `Balance_2024_V0_H.xlsx`, `balance_2025_v0_h.xlsx` | Balance Energético Nacional anual | — |
| `precio-exportacion-crudo.xlsx` | Precios USD/bbl por tipo de crudo | — |
| `TD_comercioexterior.xlsx` | Tabla dinámica de comercio exterior (explorada y **descartada**, ver Limitaciones) | — |

---

## Cómo correr el pipeline

Dependencias: `pip install -r requirements.txt` (pandas, numpy, ftfy y openpyxl; este último lo necesitan los
scripts 03 y 09 para leer los `.xlsx`). Las rutas son relativas a la raíz del repositorio: leen de
`raw/`, escriben en `clean/` y el script 10 escribe en `data/web/`. Antes de empezar hay que crear la carpeta
`clean/`, porque los scripts 01-08 no la crean.

Ejecutar desde la raíz del repo, en este orden:

| # | Script | Lee de `raw/` | Lee de `clean/` | Escribe |
|---|---|---|---|---|
| 1 | `01_clean_produccion.py` | `produccin-de-pozos-de-gas-y-petrleo-2022.csv` … `-2025.csv`, `produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv` | — | `clean/fact_produccion_pozo_mes_vaca_muerta.csv`, `clean/fact_produccion_yacimiento_mes_vaca_muerta.csv`, `clean/dim_pozo_coordenadas_no_convencional.csv` |
| 2 | `02_clean_transporte_ductos.py` | `volumnenes-de-transporte-de-hidrocarburos-planilla-20.csv`, `volumenes-de-transporte-de-hidrocarburos-planilla-21.csv`, `registro-del-midstream-ductos-empresas.csv` | — | `clean/fact_transporte_ductos.csv`, `clean/fact_movimientos_exportacion_ductos.csv`, `clean/dim_ducto.csv` |
| 3 | `03_clean_balance_y_precios.py` | `Balance_2023_V0_H.xlsx`, `Balance_2024_V0_H.xlsx`, `balance_2025_v0_h.xlsx`, `precio-exportacion-crudo.xlsx` | — | `clean/fact_balance_energetico_nacional.csv`, `clean/dim_precio_exportacion_crudo.csv`, `clean/dim_tipo_crudo_cuenca.csv` |
| 4 | `04_profile_clean_tables.py` | — | todos los CSV | solo consola (perfilado: nulos, cardinalidad, muestras) |
| 5 | `05_sanity_check_produccion.py` | — | las 2 tablas de producción | solo consola (controles de rangos, negativos y totales) |
| 6 | `06_fix_agregado_yacimiento.py` | — | `fact_produccion_pozo_mes_vaca_muerta.csv` | reescribe `clean/fact_produccion_yacimiento_mes_vaca_muerta.csv` (corrige un bug de alineación de índice en `pozos_productivos` del script 01) |
| 7 | `07_explore_anexos.py` | `anexo-2a-…csv`, `anexo-2b-…csv`, `anexo-2b-por-plantas-…csv` | — | solo consola (exploración) |
| 8 | `08_clean_capacidad_ductos.py` | `anexo-2a-capacidad-de-transporte-de-hidrocarburos-a-travs-de-ductos.csv` | `fact_transporte_ductos.csv` (del paso 2) | `clean/fact_capacidad_ductos.csv` |
| 9 | `09_explore_comercio_exterior.py` | `TD_comercioexterior.xlsx` | — | solo consola (exploración; la fuente se descartó) |
| 10 | `10_export_web_data.py` | — | producción (pozo y yacimiento), coordenadas, movimientos de exportación, capacidad y transporte | `data/web/` (8 archivos: `resumen_kpis.json`, `produccion_mapa.csv`, `produccion_anual.csv`, `indices_mensuales.csv`, `top_yacimientos.csv`, `exportacion_por_pais_anual.csv`, `exportacion_por_empresa.csv`, `capacidad_ductos.csv`) |

Los pasos 4, 5, 7 y 9 son de control o exploración y no generan tablas. El 6 tiene que correr después del 1, el 8
después del 2 y el 10 al final.

### Power BI

1. Crear el parámetro `RutaClean` apuntando a la carpeta `clean/` local (sección 0 de `powerbi/power_query_m.md`).
2. Pegar los bloques de Power Query. Todos fijan el locale `"en-US"` en `Table.TransformColumnTypes`.
3. Control: el total de `prod_pet_bbl` en `Fact_Produccion` tiene que dar **~722.439.535**. Si da un número con
   muchos más dígitos, el locale se está interpretando mal.
4. Armar las relaciones y pegar las medidas de `powerbi/dax_measures.md` (grupos A a F).
5. Opcional: aplicar el tema `powerbi/tema_vaca_muerta_v2.json`.

---

## Limitaciones documentadas

- **La exportación se mide en volumen (m³), no en USD.** El dataset de comercio exterior en USD por país no está
  entre los archivos crudos. `TD_comercioexterior.xlsx` se exploró y se descartó: es una tabla dinámica de un solo
  mes (agosto 2025) con el filtro de país colapsado en "(Todas)", sin serie temporal ni apertura geográfica. Además,
  la tabla de precios de crudo cubre solo **enero 2019 a junio 2021**, así que la medida `Valor USD Estimado` queda
  en blanco para 2022 en adelante, justo el período del boom exportador. Esa medida está documentada en
  `powerbi/dax_measures.md`, pero **no se incluyó en el reporte final**.
- **La capacidad de ductos tiene cobertura parcial.** El Anexo 2A permite calcular `Utilizacion %` solo para el
  ~45% de los ducto-mes con transporte real (41,1% a nivel ducto-año). El resto son ductos menores o provinciales
  que no reportan. Para ellos se muestra el volumen transportado, no un %. Se excluyen 6 ductos con utilización
  absurda por un error de carga en origen (`idducto` 42, 97, 149, 171, 221, 329). El Anexo 2A es anual: su
  capacidad se replica en los 12 meses del año, lo que supone capacidad constante dentro del año.
- **Los pozos convencionales no tienen coordenadas.** Las coordenadas solo existen para pozos no convencionales
  (3.335 pozos en `dim_pozo_coordenadas_no_convencional.csv`). Los 238 pozos convencionales de Vaca Muerta no
  pueden ubicarse en el mapa.

### Nota de metodología: utilización de ductos en Power BI vs. web

Las dos versiones usan la misma base: `fact_capacidad_ductos.csv` con `capacidad_valida = TRUE`, sin los 6 ductos
excluidos, y utilización = volumen transportado / capacidad mensual. Lo que cambia es el período:

- **Power BI:** la medida `Utilizacion %` divide `SUM(volumen_transportado)` por `SUM(capacidad_mensual_m3)`. En un
  visual por ducto sin filtro de fecha, acumula el volumen y la capacidad de todos los años con dato.
- **Web:** `scripts/10_export_web_data.py` calcula la utilización por ducto y por año, y `capacidad_ductos.csv`
  guarda todos los años. El gráfico de `docs/index.html` muestra, para cada ducto, solo el año más reciente
  informado.

Por eso cambia la cantidad de ductos por encima del 100%: son 3 con el acumulado y 6 con el año más reciente, sobre
57 ductos con capacidad confiable. VMOC da **171,1%** en las dos versiones porque tiene un solo año con capacidad
válida (2025).

`docs/index.html` incorpora los datos de `data/web/` ya agregados para visualización (por ejemplo, el año más
reciente por ducto y los 10 principales países de destino). Esa agregación final se hizo al armar la página y no
está en `scripts/`.

---

## Bugs encontrados y corregidos

Filas 1-9: tomadas de `documentacion/RESUMEN_PROYECTO.md` (sección 8) y `powerbi/dax_measures.md`. Filas 10-14:
correcciones hechas al armar las páginas del reporte y la versión web (medidas en el Grupo F de `dax_measures.md`).

| # | Problema | Corrección |
|---|---|---|
| 1 | Faltaban columnas reales (`idnodo_origen`, `idnodo_destino`, `idtramo_transporte`, `tramo_transporte`, `obs`, `fecha_data`) en el tipado M de `Fact_TransporteDuctos` y `Fact_MovimientosExportacion` | Agregadas en `power_query_m.md` |
| 2 | `Prod Petroleo` sumaba `dias_mes` y se inflaba con más de un yacimiento en contexto | Corregido en `dax_measures.md` |
| 3 | `Top Yacimientos` usaba `TOPN` como medida escalar, lo que no es válido en DAX | Reemplazado por `RANKX` más el filtro visual Top N |
| 4 | `Dim_Yacimiento` usaba una clave compuesta innecesaria | Clave simple `areayacimiento`, verificada única |
| 5 | El "encoding corrompido en origen" era un diagnóstico falso: el mojibake lo causaba leer UTF-8 como latin-1 | Diagnóstico corregido en la documentación y en el docstring de `01_clean_produccion.py`. El script no se reescribió para no invalidar `clean/`, que se verificó sin caracteres corruptos |
| 6 | Ningún bloque de Power Query fijaba el locale: en una máquina en español los números se inflaban varios órdenes de magnitud (~13% de las filas de `Fact_Produccion`) | `"en-US"` como tercer parámetro en los 9 `Table.TransformColumnTypes` |
| 7 | `Prod Petroleo (bbl-dia)` se inflaba ~12x con un año filtrado y `Var Interanual Prod` siempre daba -100% (por `LASTDATE` sobre `Dim_Fecha`, de grano diario) | `SUMX(VALUES(fecha), CALCULATE(AVERAGE(dias_mes)))` + `DATEADD`; aplicado también, de forma preventiva, a `Var Interanual Exportacion` |
| 8 | El mes base del índice de exportación (enero 2018) no era representativo: había una sola empresa reportando | Base = promedio de los 12 meses de 2019, también para `Indice Produccion` |
| 9 | Los índices base 100 daban exactamente 100 en cualquier mes de 2019 (y probablemente blanco en los demás años) porque dos filtros sobre `Dim_Fecha` se combinaban con AND | `ALL(Dim_Fecha)` antes del filtro `anio = 2019` |
| 10 | `top_yacimientos.csv` (versión web) calculaba el bbl/día sumando `dias_mes` sin deduplicar por fecha: 23 de los 146 yacimientos tienen más de un `tipo_de_recurso` en el mismo mes y contaban ese mes dos veces. Ej.: Bajada del Palo Oeste daba 22.622,7 bbl/día contra 31.386,5 en Power BI. Se detectó al comparar el mismo dato en las dos herramientas | Se agrupa primero por yacimiento y fecha (promedio de `dias_mes`) y recién después se suma. 44 de los 146 yacimientos cambiaron de posición en el ranking completo; el Top 10 mantuvo el orden. Power BI estaba bien |
| 11 | `% Exportacion con Pais Asignado` daba 100% porque `ISBLANK` no detecta una cadena vacía: los registros sin país estaban vacíos, no nulos | Condición `pais <> "" && NOT(ISBLANK(pais))`; el valor real es ~72% (comprobado en Power BI: con solo ISBLANK daba 100%; al agregar la condición pais <> "" bajó a 72,01%). |
| 12 | El gráfico de concentración por empresa sumaba 100% entre las 3 empresas visibles: "Mostrar valor como % del total general" calcula sobre lo que queda después del filtro Top N (todos los años: 64,3 / 29,6 / 6,1). | Medida `% Exportado por Empresa (sobre total)` con ALL(empresa) en el denominador (mismo período, todos los años: 60,90 / 27,99 / 5,79). Además el visual no tenía el filtro de años 2020-2025; con ese filtro da 61,08 / 27,94 / 5,23, igual que la versión web (94,25% entre las tres). |
| 13 | `Volumen Transportado (respaldo)` incluía también los ductos con capacidad confiable, que aparecían en los dos gráficos de la página de transporte | Medida `Tiene Capacidad Confiable` como filtro del visual (solo valor 0) |
| 14 | Las tarjetas de resumen de Power BI mostraban acumulados históricos (variación interanual 11,1% y 53,76 M m³) en vez del último mes, y no coincidían con la web (31,9% y 1,27 M m³) | Medidas `Var Interanual Prod - Ultimo Mes` y `Volumen Exportado - Ultimo Mes` |

---

## Autor

Enzo · Buenos Aires · LinkedIn: [URL_LINKEDIN]
