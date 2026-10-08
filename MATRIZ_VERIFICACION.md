# Matriz de verificación

Qué afirma el informe, qué pruebas lo sostienen y su resultado actual. Se genera con `python scripts/17_matriz_verificacion.py` (corre toda la suite). Un grupo figura como **VERIFICADO** solo si todas sus pruebas pasaron, sin omitidas. Lo que los datos no permiten comprobar figura aparte como **LÍMITE DECLARADO**, con la evidencia que lo acota y el lugar del informe donde se declara.

Resultado de la suite en esta corrida: `208 passed, 1 warning in 38.33s`.

## Producción

| Id | Afirmación publicada | Pruebas | Estado |
|---|---|---|---|
| P1 | Producción de Vaca Muerta 2006–2025 (acumulado, filas, diciembre de 2025, variación interanual) | 7 | VERIFICADO |
| P2 | Producción de junio de 2026, solo no convencional, y su variación interanual | 4 | VERIFICADO |
| P3 | % no convencional 2022–2025 y rango del convencional | 2 | VERIFICADO |
| P4 | Producción de la cuenca (serie oficial) y coincidencia con la suma por pozo, salvo septiembre de 2024 (Shell no figura) | 7 | VERIFICADO |
| P5 | Mapa (pozos y omitidos), yacimientos y producción anual | 7 | VERIFICADO |

## Exportación

| Id | Afirmación publicada | Pruebas | Estado |
|---|---|---|---|
| E1 | Serie principal de exportación (comercio exterior): registros, volumen y USD por año | 3 | VERIFICADO |
| E2 | Valor en USD: precio implícito validado contra la tabla oficial de precios FOB (2020–2021) y contra el Brent mensual de la EIA (2020–2025) | 3 | VERIFICADO |
| E3 | % exportado de la producción de la cuenca y elección del año base | 3 | VERIFICADO |
| E4 | Conclusión: con las dos fuentes y las tres bases, la exportación crece más que la producción y el % exportado sube cada año | 5 | VERIFICADO |
| E5 | Contraste entre fuentes: difieren menos del 3% hasta 2022, distinto nivel desde 2023, no es calendario y aparece en los destinos citados | 7 | VERIFICADO |
| E6 | Destinos y concentración por empresa exportadora (y por operador de terminal como contexto) | 4 | VERIFICADO |
| E7 | Volatilidad mensual de la exportación frente a la producción | 2 | VERIFICADO |

## Transporte

| Id | Afirmación publicada | Pruebas | Estado |
|---|---|---|---|
| D1 | Petróleo transportado por Allen–Puerto Rosales y la línea Duplicar (inicio en marzo de 2025) | 3 | VERIFICADO |
| D2 | Capacidades: reglas de exclusión, ranking y contraste (el flujo de 2024 supera la capacidad que informa el Anexo) | 7 | VERIFICADO |
| D3 | No se publica una utilización para VMOC | 3 | VERIFICADO |

## Fuentes externas

| Id | Afirmación publicada | Pruebas | Estado |
|---|---|---|---|
| X1 | Cifras y fechas de la caja de proyectos y de las capacidades externas: cada una está en el texto de la fuente citada y el enlace responde | 15 | VERIFICADO |

## Forma y publicación

| Id | Afirmación publicada | Pruebas | Estado |
|---|---|---|---|
| T1 | Toda cifra de README, HTML y traspaso sale del registro; sin palabras que el dato no respalda, rutas, correos ni marcadores | 46 | VERIFICADO |
| T2 | El dashboard abre sin errores de consola en un navegador (escritorio y celular) | 2 | VERIFICADO |

## Límites declarados (no verificables con los datos disponibles)

| Id | Qué no se puede comprobar | Evidencia que lo acota | Dónde se declara |
|---|---|---|---|
| L1 | Cuál de las dos fuentes de exportación (comercio exterior; terminales más oleoducto) es la correcta | No hay un tercer dato público. Se acotó: no es calendario, aparece en todos los destinos y la dirección coincide. Por eso el informe solo afirma la dirección y muestra el nivel como rango. | Sección de exportación (contraste) y Limitaciones del dashboard; README. |
| L2 | Exportación de Vaca Muerta aislada del resto de la cuenca | El comercio exterior rotula por cuenca, no por formación; Vaca Muerta es una parte de la producción de la cuenca. La serie se rotula como crudo de la cuenca Neuquina. | Limitaciones del dashboard; README. |
| L3 | Capacidad física de cada ducto | Las fuentes (Anexo 2A, Secretaría de Energía, Oldelval, nota del sector, Tramos de Integridad) no coinciden. Se publica el petróleo transportado y las capacidades por fuente, sin porcentaje de utilización como resultado. | Acto II del dashboard; Limitaciones. |
| L4 | Fechas y capacidades futuras de VMOS y Duplicar Norte | Son anuncios. Cada cifra figura en el texto crudo de su fuente (prueba X1), con fecha, fuera de gráficos e indicadores. | Caja "Proyectos anunciados" del dashboard. |
| L5 | Contraste con la Secretaría de Energía o con las operadoras | Requiere una consulta externa; el análisis es descriptivo sobre datos públicos. | Limitaciones. |
| L6 | Unidad del campo caudal_nominal de la tabla de Tramos de Integridad | Inferida (m³/h) por coincidencia exacta con la capacidad del Anexo en varios ductos; se declara como inferencia y no sostiene ninguna conclusión. | Limitaciones (capacidades contrastadas). |
| L7 | Medidas DAX y páginas del reporte de Power BI | No se pudieron ejecutar sin el archivo de plantilla (.pbit). Los valores esperados salen de las mismas tablas verificadas arriba. | CAMBIOS_POWERBI.md. |

**Grupos de afirmaciones verificados: 18 de 18.** Límites declarados: 7.
