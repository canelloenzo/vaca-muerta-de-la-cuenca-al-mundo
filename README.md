# Vaca Muerta: de la cuenca al mundo

Análisis de datos públicos (Secretaría de Energía y ENARGAS) sobre la formación Vaca Muerta, cuenca Neuquina, Argentina, contado en tres actos:

1. **Producción**: de dónde sale el petróleo (pozo y yacimiento, 2006–2025, más 2026 solo no convencional).
2. **Transporte**: cuánto petróleo se mueve por los principales ductos, qué informan distintas fuentes sobre su capacidad (con el ranking de utilización como detalle con advertencias) y qué proyectos se anuncian.
3. **Exportación**: cuánto crudo neuquino sale por terminales, adónde va y quién lo despacha.

El pipeline limpia los archivos crudos con Python (pandas). Las tablas alimentan un modelo y un reporte de Power BI de 6 páginas y un dashboard web con Chart.js. Cada cifra publicada declara su alcance y sale de un registro de cifras generado por los scripts; una prueba automática compara cada texto contra ese registro.

## Resultados (con su alcance)

| Cifra | Valor | Alcance |
|---|---|---|
| Producción de petróleo, junio de 2026 | 633.371 bbl/día (+33,0% interanual) | solo no convencional; el convencional de 2026 no está en las fuentes cargadas |
| Incidencia no convencional | 99,88% | volumen de Vaca Muerta 2022–2025, el único período con ambos tipos observables |
| Exportación de crudo de la cuenca, 2025 | 191.506 bbl/día, 32,3% de la producción de la cuenca, USD 4.536 millones | comercio exterior declarado por las empresas (producto "Cuenca Neuquina"), todas las vías; convencional y no convencional |
| Contraste con otras fuentes | los terminales marítimos (planilla 21) dan 166.161 bbl/día y el oleoducto a Chile (planilla 20), 79.998 bbl/día en 2025 | las fuentes no concilian desde 2023: el comercio exterior queda entre 0,75 y 0,88 veces la suma de terminales y oleoducto en 2023–2024; la serie principal es la que mide el origen directamente |
| Índice base 2022, promedio 2025 | exportación 264,9 · producción de la cuenca 168,1 · producción de Vaca Muerta 206,4 | con sensibilidad a las bases 2021 y 2023; con las tres bases y con las dos fuentes la exportación crece más que la producción de la cuenca en cada año posterior a la base |
| Concentración exportadora 2020–2025 | 58,6% las 3 mayores empresas exportadoras · 94,25% los 3 mayores operadores de terminal de todo el país | son dos medidas distintas: quién exporta y quién opera el puerto |
| Destinos, 2020–agosto 2026 | Estados Unidos 45,9% · Chile 27,0% · sin país ("no aplica") 5,9% | crudo de la cuenca, comercio exterior |
| Valor de la exportación, 2020–2025 | USD 13.752 millones; precio implícito 2025: 64,9 USD/bbl | monto FOB declarado; validado contra el precio FOB oficial de 2020 y 2021 (correlación 0,99) |
| Ductos | corredor Allen–Puerto Rosales: 22.768.324 m³ en 2025 (37,9% más que en 2024, con la línea nueva Duplicar). Capacidad válida en 44 de 83 ductos que mueven petróleo; 3 superan el 100% en su tramo más cargado (2 con la capacidad marcada "a revisar") | capacidad operativa informada en el Anexo 2A; ver Limitaciones |

Proyectos anunciados (VMOS, Duplicar Norte) figuran en una caja aparte del dashboard, con su fuente y fecha, rotulados como información externa no verificada con los datos del proyecto.

## Estado y enlaces

- Dashboard web: <https://canelloenzo.github.io/vaca-muerta-de-la-cuenca-al-mundo/>
- Power BI (`.pbix`): <https://github.com/canelloenzo/vaca-muerta-de-la-cuenca-al-mundo/releases/latest>
- Los cambios de títulos, textos y medidas del reporte de Power BI respecto de la versión original están en `CAMBIOS_POWERBI.md`.

## Páginas del reporte de Power BI

1. Vaca Muerta: de la cuenca al mundo (resumen)
2. Acto I · Producción: de dónde sale el petróleo
3. Producción y exportación: índices base 2022
4. Acto II · Transporte: capacidad informada de los ductos
5. Acto III · Exportación: adónde va
6. Acto III · Exportación: quién la despacha

## Estructura del repositorio

```
├── README.md                      # generado por scripts/15_render_textos.py
├── CHANGELOG_CORRECCIONES.md      # qué se corrigió tras la auditoría, antes y después
├── CAMBIOS_POWERBI.md             # cambios a aplicar en el reporte de Power BI, con valores esperados
├── MATRIZ_VERIFICACION.md         # cada afirmación publicada, las pruebas que la sostienen y los límites declarados
├── docs/index.html                # dashboard web (datos embebidos, Chart.js por CDN); generado
├── scripts/                       # pipeline 01–16 (Python) y verificación en navegador
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
| `precio-exportacion-crudo.xlsx` | Precios USD/bbl por tipo de crudo (enero de 2019 a junio de 2021; la tabla oficial no se actualizó después) | Dataset "Precio de exportación de petróleo crudo" de datos.energia.gob.ar |
| `TD_comercioexterior_actualizado_2026-09-24.xlsx` | Comercio exterior de Refinación y Comercialización: 125.532 registros de exportación de crudo por cuenca, 2020 a agosto de 2026, con empresa, país, cantidad y monto. La tabla dinámica visible muestra un solo mes; los datos completos están en la caché de la tabla dinámica, de donde se leen | Dataset "Precios de Comercio Exterior" de datos.energia.gob.ar (archivo `TD_comercio_exterior.zip`) |
| `serie-historica-produccion-petroleo-por-cuenca-subtipo-capitulo-iv.csv` | Producción oficial de petróleo por cuenca, mensual, 2006 a agosto de 2026 | Dataset "Producción de petróleo y gas por pozo (Capítulo IV)", recurso "Serie histórica de producción de petróleo por cuenca y sub tipo de recurso" de datos.energia.gob.ar |

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
| 11 | `11_series_cuenca_neuquina.py` | Producción de Vaca Muerta y de la cuenca por pozo, exportación por terminales (planilla 21) y oleoducto a Chile (planilla 20), concentración por operador, KPIs |
| 12 | `12_utilizacion_ductos_web.py` | Ranking y clasificación de ductos |
| 13 | `13_pozos_coordenadas_dudosas.py` | Pozos con coordenadas dudosas |
| 14 | `14_registro_cifras.py` | Registro de cifras (`data/web/registro_cifras.json`) |
| 16 | `16_comercio_exterior.py` | Serie principal de exportación: comercio exterior de la cuenca Neuquina (volumen, USD, país, empresa), producción oficial de la cuenca, índices y contraste con terminales (se corre antes del 14) |
| 17 | `17_matriz_verificacion.py` | Corre la suite y genera `MATRIZ_VERIFICACION.md` |
| 15 | `15_render_textos.py` | Genera `docs/index.html` y `README.md` desde las plantillas y el registro |

Pruebas: `python -m pytest -q`. Las que leen `raw/` tardan unos minutos la primera vez. La verificación del HTML en navegador headless: `python scripts/verificar_html_headless.py`.

### Power BI

1. Crear el parámetro `RutaClean` apuntando a la carpeta de las tablas limpias (sección 0 de `powerbi/power_query_m.md`).
2. Pegar los bloques de Power Query; todos fijan el locale `"en-US"`.
3. Control: el total de `prod_pet_bbl` en `Fact_Produccion` tiene que dar 722.439.535.
4. Armar las relaciones y pegar las medidas de `powerbi/dax_measures.md`.
5. Aplicar los cambios de `CAMBIOS_POWERBI.md`.

## Limitaciones

- **Dos fuentes oficiales de exportación con distinto nivel.** La serie principal es el comercio exterior declarado por las empresas. Los terminales marítimos (planilla 21) más el oleoducto a Chile (planilla 20) dan otros volúmenes desde 2023: 41,6% de la producción de la cuenca en 2025 contra 32,3%. Hasta 2022 difieren menos del 3%. Los datos no permiten decidir cuál es la correcta, por eso las conclusiones se limitan a lo que vale con ambas fuentes: el % exportado sube cada año de 2022 a 2025 y la exportación crece más que la producción de la cuenca con las bases 2021, 2022 y 2023.
- **Alcance de la serie principal.** Es crudo con origen en la cuenca Neuquina (Neuquén, Río Negro, La Pampa y Mendoza), convencional y no convencional, por todas las vías; no es exportación de Vaca Muerta únicamente y no se puede separar con estos datos.
- **Cobertura temporal.** El comercio exterior empieza en enero de 2020: 2020 tiene exportación en 6 meses y 2021 en 11; 2026 es parcial (enero a agosto) y solo se usa para el valor en USD. Las comparaciones cierran en diciembre de 2025. Los meses sin exportación declarada cuentan como cero.
- **Producción de septiembre de 2024.** Los archivos por pozo de ese mes quedan 157.933 m³ por debajo del agregado oficial (Shell Argentina no figura en septiembre en el archivo por pozo y sí en agosto y octubre); por eso la producción de la cuenca usa la serie oficial, y la de Vaca Muerta por pozo queda unos 0,7% por debajo en el promedio de 2024.
- **Producción de 2026.** La cifra de junio de 2026 incluye solo el archivo no convencional.
- **Capacidad de ductos.** El Anexo 2A es anual y su capacidad se repite en los 12 meses; no comparte identificador de tramo con la planilla 20. La utilización es un cociente aproximado (tramo más cargado de líquidos sobre capacidad operativa informada). La cobertura es parcial: capacidad en el 45,4% de los ducto-mes con transporte. Se excluyen 36 ducto-años de 18 ductos por las reglas R1, R3, R4, R5 y D2; R2 y R6 solo marcan "a revisar". VMOC 2025 queda excluido (D2) y no se publica su utilización.
- **Capacidades contrastadas.** Contraste de capacidades con otras fuentes. En Allen–Puerto Rosales, el Anexo 2A informa 46.384, 50.052 y 36.000 m³/día para 2022, 2023 y 2024; la Secretaría de Energía dio 36.000 m³/día como capacidad actual de Oldelval en septiembre de 2022; una nota del sector de abril de 2022 cita 42.000; y Oldelval informa objetivos de 55.000 y 86.000 m³/día para Duplicar. El petróleo transportado en 2024 fue de 45.109 m³/día en promedio, más que 36.000: esa cifra no funciona como límite físico. Con 42.000 la utilización de 2024 sería 111,2% y con la capacidad de 2023, 93,3%, en lugar de 129,7%. La tabla de Tramos de Integridad informa un caudal de referencia por tramo (campo `caudal_nominal`, sin unidad documentada; se infiere m³/h porque coincide exactamente con la capacidad del Anexo en varios ductos): en 12 de los 34 ductos del ranking con ese dato, la capacidad operativa del Anexo queda dentro de ±15% de ese caudal, y en Centenario–Allen L14, de ser m³/h, la utilización sería 53,0%. Por eso los "sobre 100%" se leen como una señal a revisar y no como un hecho.
- **Volúmenes repetidos.** En la planilla 21 hay pares de cargadores con volumen idéntico; no hay evidencia suficiente para llamarlo doble conteo y no se corrigió. En el comercio exterior no hay filas repetidas exactas.
- **Mapa.** Se omiten 2 pozos con coordenadas a más de 30 km de la mediana de su yacimiento. Los pozos convencionales no tienen coordenadas.
- **Valores en USD.** Son el monto FOB declarado por las empresas, no una serie de precios de mercado; se validaron contra la tabla oficial en 9 meses de 2020 y 2021, porque esa tabla termina en 2021.
- **Sin validación externa.** El análisis es descriptivo y no fue contrastado con la Secretaría de Energía ni con los operadores.

## Cómo se verifica

- `MATRIZ_VERIFICACION.md` lista cada grupo de afirmaciones publicadas con las pruebas que lo sostienen y su resultado, y separa lo que los datos no permiten comprobar como límite declarado. Se regenera con `python scripts/17_matriz_verificacion.py`.
- Las cifras de fuentes externas (proyectos anunciados y capacidades) se buscan en el texto crudo de cada página citada.
- Los precios implícitos del comercio exterior se contrastaron con la tabla oficial de precios FOB y la producción de la cuenca con la serie oficial; las diferencias están en las Limitaciones.
- Las cifras de producción, exportación y ductos se recalculan de forma independiente desde `raw/` en `tests/` y se comparan con las tablas de `data/web/`.
- `data/web/registro_cifras.json` es la única fuente de las cifras de este README y del dashboard; `tests/test_10_textos.py` falla si un texto contiene una cifra que no está en el registro, un marcador sin completar o una palabra que el dato no respalda.
- `scripts/verificar_html_headless.py` abre el dashboard en un navegador headless y falla si hay errores de consola.

## Qué se corrigió tras la auditoría

El detalle, con antes y después de cada cifra, está en `CHANGELOG_CORRECCIONES.md`. En resumen: se corrigió el alcance de la serie de exportación (de terminales de todo el país a crudo de la cuenca Neuquina según comercio exterior, contrastada con terminales y oleoducto), el año base del índice, la utilización de ductos (numerador de líquidos, tramo más cargado y reglas de capacidad dudosa), el doble conteo por tramo de la planilla 20, el rótulo de concentración, el volumen sin país y los años parciales.

Los documentos de trabajo anteriores a la auditoría están en `documentacion/historico/`, con un aviso al inicio; contienen afirmaciones que ya no se sostienen.

## Autor

Enzo · Buenos Aires · [LinkedIn](https://www.linkedin.com/in/enzocanello)
