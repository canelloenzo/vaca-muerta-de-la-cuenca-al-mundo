# Vaca Muerta: de la cuenca al mundo

Análisis de datos públicos (Secretaría de Energía y ENARGAS) sobre la formación Vaca Muerta, cuenca Neuquina, Argentina, contado en tres actos:

1. **Producción**: de dónde sale el petróleo (pozo y yacimiento, 2006–2025, más 2026 solo no convencional).
2. **Transporte**: cuántos ductos informan capacidad y cuánto se carga su tramo más exigido frente a esa capacidad.
3. **Exportación**: cuánto crudo neuquino sale por terminales, adónde va y quién lo despacha.

El pipeline limpia los archivos crudos con Python (pandas). Las tablas alimentan un modelo y un reporte de Power BI de 6 páginas y un dashboard web con Chart.js. Cada cifra publicada declara su alcance y sale de un registro de cifras generado por los scripts; una prueba automática compara cada texto contra ese registro.

## Resultados (con su alcance)

| Cifra | Valor | Alcance |
|---|---|---|
| Producción de petróleo, junio de 2026 | {{prod_ultimo_mes_bbl_dia:0}} bbl/día (+{{prod_var_interanual_pct:1}}% interanual) | solo no convencional; el convencional de 2026 no está en las fuentes cargadas |
| Incidencia no convencional | {{pct_nc_2022_2025:2}}% | volumen de Vaca Muerta 2022–2025, el único período con ambos tipos observables |
| Exportación de crudo neuquino, 2025 | {{exp_neu_2025_bbl_dia:0}} bbl/día, {{pct_exp_cuenca_2025:1}}% de la producción de la cuenca | terminales neuquinos (Oiltanking + Refinería Bahía Blanca), planilla 21; sin oleoducto a Chile |
| Oleoducto a Chile | {{chile_2024_bbl_dia:0}} bbl/día (2024) y {{chile_2025_bbl_dia:0}} bbl/día (2025) | planilla 20, serie aparte; no se suma a la anterior |
| Índice base {{anio_base_indice:y}}, promedio 2025 | exportación {{idx_exp_2025_base2022:1}} · producción de Vaca Muerta {{idx_vm_2025_base2022:1}} · producción de la cuenca {{idx_cuenca_2025_base2022:1}} | con sensibilidad a las bases 2021 y 2023; en 2024 la dirección entre exportación y producción cambia según la base, por eso no se afirma una tendencia |
| Concentración 2020–2025 | {{conc_top3_cargadores_pct:1}}% top 3 cargadores · {{conc_top3_operadores_pct:2}}% top 3 operadores de terminal | son dos medidas distintas; 6 operadores de terminal de todo el país |
| Volumen exportado sin país identificado | {{sin_pais_pct:1}}% | planilla 21, 2018–junio 2026; todo de TERMAP |
| Ductos con capacidad válida | {{ductos_ranking_n:0}} de {{ductos_petroleo_n:0}} que mueven petróleo; {{ductos_sobre_100_n:0}} superan el 100% en su tramo más cargado ({{ductos_sobre_100_a_revisar_n:0}} con la capacidad marcada "a revisar") | capacidad operativa informada en el Anexo 2A; ver Limitaciones |

## Estado y enlaces

- Dashboard web: <https://canelloenzo.github.io/vaca-muerta-de-la-cuenca-al-mundo/>
- Power BI (`.pbix`): <https://github.com/canelloenzo/vaca-muerta-de-la-cuenca-al-mundo/releases/latest>
- Los cambios de títulos, textos y medidas del reporte de Power BI respecto de la versión original están en `CAMBIOS_POWERBI.md`.

## Páginas del reporte de Power BI

1. Vaca Muerta: de la cuenca al mundo (resumen)
2. Acto I · Producción: de dónde sale el petróleo
3. Producción y exportación: índices base {{anio_base_indice:y}}
4. Acto II · Transporte: capacidad informada de los ductos
5. Acto III · Exportación: adónde va
6. Acto III · Exportación: quién la despacha

## Estructura del repositorio

```
├── README.md                      # generado por scripts/15_render_textos.py
├── CHANGELOG_CORRECCIONES.md      # qué se corrigió tras la auditoría, antes y después
├── CAMBIOS_POWERBI.md             # cambios a aplicar en el reporte de Power BI, con valores esperados
├── docs/index.html                # dashboard web (datos embebidos, Chart.js por CDN); generado
├── scripts/                       # pipeline 01–15 (Python) y verificación en navegador
├── tests/                         # pruebas (pytest) con recálculo independiente desde raw/
├── powerbi/                       # consultas M, medidas DAX y tema
├── documentacion/                 # diccionario de datos, plantillas de textos, documentos históricos
└── data/web/                      # tablas resumen publicadas y registro_cifras.json
```

`raw/` (archivos crudos, más de 1 GB) y `clean/` (tablas limpias) **no están en el repositorio**.

## Fuentes de datos

Datos públicos de datos.energia.gob.ar y ENARGAS. La fuente puntual de cada archivo figura solo donde está documentada:

| Archivo(s) en `raw/` | Contenido | Fuente documentada |
|---|---|---|
| `produccin-de-pozos-de-gas-y-petrleo-2022.csv` … `-2025.csv` | Producción mensual por pozo, convencional + no convencional, 2022–2025 | Dataset "Producción de Petróleo y Gas por Pozo": `datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo` |
| `produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv` | Producción por pozo, solo no convencional, histórico con coordenadas y 2026 | Probablemente el mismo dataset (deducido por el nombre del archivo, no confirmado en el portal) |
| `volumnenes-de-transporte-de-hidrocarburos-planilla-20.csv` | Movimientos por ducto y tramo | Dataset "Transporte de Hidrocarburos" de datos.energia.gob.ar |
| `volumenes-de-transporte-de-hidrocarburos-planilla-21.csv` | Movimientos por nodo y terminal, con país de destino | Ídem |
| `registro-del-midstream-ductos-empresas.csv` | Registro de ductos | Ídem |
| `anexo-2a-capacidad-de-transporte-de-hidrocarburos-a-travs-de-ductos.csv` | Capacidad de transporte por ducto (anual) | Ídem |
| `anexo-2b-…csv` | Capacidad de almacenamiento (evaluado, fuera del modelo) | Ídem |
| `Balance_2023_V0_H.xlsx`, `Balance_2024_V0_H.xlsx`, `balance_2025_v0_h.xlsx` | Balance Energético Nacional | Sin fuente documentada en el proyecto |
| `precio-exportacion-crudo.xlsx` | Precios USD/bbl por tipo de crudo (enero de 2019 a junio de 2021) | Sin fuente documentada en el proyecto |
| `TD_comercioexterior.xlsx` | Tabla dinámica de comercio exterior (explorada y descartada) | Sin fuente documentada en el proyecto |

## Cómo correr el pipeline y las pruebas

Dependencias: `pip install -r requirements.txt`. Para las pruebas de navegador: `pip install playwright` y `python -m playwright install chromium`.

Variables de entorno (ver `scripts/_rutas.py`): `VM_DATA_ROOT` es la carpeta que contiene `raw/` (y `clean/` por defecto); `VM_CLEAN_DIR` es la carpeta de las tablas limpias, que se crea si no existe. Ningún script escribe en `raw/`.

Orden, desde la raíz del repositorio:

| # | Script | Qué hace |
|---|---|---|
| 01 | `01_clean_produccion.py` | Limpia la producción por pozo y yacimiento |
| 02 | `02_clean_transporte_ductos.py` | Limpia planillas 20 y 21 y el registro de ductos; elimina las filas de la planilla 20 repetidas solo por tramo |
| 03 | `03_clean_balance_y_precios.py` | Balance energético y precios |
| 04–05, 07, 09 | `04_…`, `05_…`, `07_…`, `09_…` | Perfilado, controles y exploración (solo consola) |
| 06 | `06_fix_agregado_yacimiento.py` | Corrige el agregado por yacimiento |
| 08 | `08_clean_capacidad_ductos.py` | Capacidad de ductos, numerador de líquidos y reglas de capacidad dudosa |
| 10 | `10_export_web_data.py` | Mapa, producción anual y yacimientos |
| 11 | `11_series_cuenca_neuquina.py` | Producción de la cuenca, exportación por terminales, índices y KPIs |
| 12 | `12_utilizacion_ductos_web.py` | Ranking y clasificación de ductos |
| 13 | `13_pozos_coordenadas_dudosas.py` | Pozos con coordenadas dudosas |
| 14 | `14_registro_cifras.py` | Registro de cifras (`data/web/registro_cifras.json`) |
| 15 | `15_render_textos.py` | Genera `docs/index.html` y `README.md` desde las plantillas y el registro |

Pruebas: `python -m pytest -q`. Las que leen `raw/` tardan unos minutos la primera vez. La verificación del HTML en navegador headless: `python scripts/verificar_html_headless.py`.

### Power BI

1. Crear el parámetro `RutaClean` apuntando a la carpeta de las tablas limpias (sección 0 de `powerbi/power_query_m.md`).
2. Pegar los bloques de Power Query; todos fijan el locale `"en-US"`.
3. Control: el total de `prod_pet_bbl` en `Fact_Produccion` tiene que dar {{prod_acum_2006_2025_bbl:0}}.
4. Armar las relaciones y pegar las medidas de `powerbi/dax_measures.md`.
5. Aplicar los cambios de `CAMBIOS_POWERBI.md`.

## Limitaciones

- **Alcance de la exportación.** La planilla 21 recoge movimientos de {{operadores_n:0}} operadores de terminal de todo el país; solo el {{exp_neuquina_pct_del_nacional:1}}% del volumen es crudo neuquino. La serie principal usa Oiltanking y Refinería Bahía Blanca como indicador de la cuenca: el {{proxy_pct_producto_neuquino:1}}% de su volumen exportado está rotulado como crudo Neuquén / Río Negro (Medanito). Es un indicador, no una medición directa; esos terminales también despachan crudo convencional.
- **Cobertura por serie.** La producción de la cuenca existe solo para 2022–2025; el % exportado de la cuenca, solo en esos años. 2018 y 2026 son años parciales. El último mes de exportación se apoya casi por completo en Oiltanking; Refinería Bahía Blanca no informa desde febrero de 2026 (aportó el {{rbb_pct_2025:1}}% de la exportación neuquina de 2025), así que el mes podría estar subestimado en ese orden. Por eso las comparaciones cierran en diciembre de 2025. La producción de la cuenca antes de 2022 queda como trabajo futuro.
- **Huecos.** Los meses sin dato figuran como "sin dato", no como cero. Los meses de 2019–2021 en que Oiltanking informó operaciones sin exportación se tratan como cero informado.
- **Capacidad de ductos.** El Anexo 2A es anual y su capacidad se repite en los 12 meses; no comparte identificador de tramo con la planilla 20. La utilización es un cociente aproximado (tramo más cargado de líquidos sobre capacidad operativa informada). La cobertura es parcial: capacidad en el {{cobertura_capacidad_ducto_mes_pct:1}}% de los ducto-mes con transporte. Se excluyen {{ducto_anios_excluidos_n:0}} ducto-años de {{ductos_con_anio_excluido_n:0}} ductos por las reglas R1, R3, R4, R5 y D2; R2 y R6 solo marcan "a revisar". VMOC 2025 queda excluido (D2) y no se publica su utilización.
- **Volúmenes repetidos.** En la planilla 21 hay pares de cargadores con volumen idéntico; no hay evidencia suficiente para llamarlo doble conteo y no se corrigió.
- **Mapa.** Se omiten {{pozos_mapa_omitidos:0}} pozos con coordenadas a más de {{umbral_km:0}} km de la mediana de su yacimiento. Los pozos convencionales no tienen coordenadas.
- **Volumen, no USD.** La tabla de precios cubre solo hasta junio de 2021, así que no se estima ningún valor en dólares.
- **Sin validación externa.** El análisis es descriptivo y no fue contrastado con la Secretaría de Energía ni con los operadores.

## Cómo se verifica

- Las cifras de producción, exportación y ductos se recalculan de forma independiente desde `raw/` en `tests/` y se comparan con las tablas de `data/web/`.
- `data/web/registro_cifras.json` es la única fuente de las cifras de este README y del dashboard; `tests/test_10_textos.py` falla si un texto contiene una cifra que no está en el registro, un marcador sin completar o una palabra que el dato no respalda.
- `scripts/verificar_html_headless.py` abre el dashboard en un navegador headless y falla si hay errores de consola.

## Qué se corrigió tras la auditoría

El detalle, con antes y después de cada cifra, está en `CHANGELOG_CORRECCIONES.md`. En resumen: se corrigió el alcance de la serie de exportación (terminales neuquinos en lugar de todo el país), el año base del índice, la utilización de ductos (numerador de líquidos, tramo más cargado y reglas de capacidad dudosa), el doble conteo por tramo de la planilla 20, el rótulo de concentración, el volumen sin país y los años parciales.

Los documentos de trabajo anteriores a la auditoría están en `documentacion/historico/`, con un aviso al inicio; contienen afirmaciones que ya no se sostienen.

## Autor

Enzo · Buenos Aires · [LinkedIn](https://www.linkedin.com/in/enzocanello)
