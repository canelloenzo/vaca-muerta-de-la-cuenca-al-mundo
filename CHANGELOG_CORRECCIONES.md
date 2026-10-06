# Changelog de correcciones (rama `correcciones-auditoria`)

Base: commit `Estado auditado`. Todo lo que sigue responde a `AUDITORIA_2026-10-05.md` y a las decisiones D1–D3.
Este documento se completa fase por fase. **Estado actual: Fases 1 y 2 terminadas; Fase 3 (textos), Fase 4 (Power BI) y Fase 5 (registro) pendientes.**

## Pendientes de tu parte

| marcador / tema | estado |
|---|---|
| `[URL_PAGES]`, `[URL_RELEASE]`, `[URL_LINKEDIN]` (README) | se dejan como marcador: el proyecto todavía no está publicado. No se cuentan como afirmaciones |
| `.pbit` del reporte | necesario antes de la Fase 4 para verificar medidas y relaciones reales |
| Decisiones abiertas de la Fase 2 | ver la sección "Decisiones abiertas" más abajo |

## Fase 1 — Pruebas y línea de base

- `tests/` (pytest) con recálculo independiente desde `raw/`: reconciliación raw→clean, unicidad de claves, exportación, ductos, métricas, coincidencia de cifras publicadas (data/web y `DATA` del HTML) y cada cifra de la sección 4 de la auditoría. Más pruebas de "estado objetivo" (`test_07`) que codifican cómo debe quedar el proyecto.
- Línea de base (`tests/baseline/linea_base.md`): 100 pruebas, 76 PASS, 24 FAIL. Las 24 son de estado objetivo; todas las pruebas de cifras y cálculos pasaban.

## Fase 2 — Datos y cálculos

### Cambios por hallazgo

| hallazgo | qué se hizo | archivos |
|---|---|---|
| F1 / D1 | Serie "Cuenca Neuquina (proxy por terminal)": Oiltanking + Refinería Bahía Blanca, en bbl/día, con meses sin dato y el volumen sin país de la serie nacional. Producción total de la cuenca (2022–2025) y `% exportado`. Índice con año base por criterio explícito (2022) y sensibilidad 2021/2023, promedios anuales y media móvil de 12 meses | `scripts/11_*`, `data/web/*` nuevos |
| F2 / F3 / D2 | Utilización con numerador solo de líquidos y segmento más cargado. Se retira el 171,1% (VMOC, D2). Exclusión por ducto-año (en vez de 6 ductos completos) con la causa real documentada | `scripts/08_*`, `scripts/12_*` |
| F4 | Clasificación explícita de los 83 ductos lógicos que mueven petróleo | `data/web/clasificacion_ductos_petroleo.csv` |
| F5 | Reglas de capacidad dudosa R1, R3, R4, R5 (excluyen del ranking) y R2 (solo "a revisar") | `scripts/08_*` |
| F6 / D3 | Tarjeta de producción jun-2026 (solo no convencional) y comparaciones cerradas en dic-2025 | `data/web/kpis_resumen.json` |
| F7 | `pais_original` y `pais_estado` conservan "NO IDENTIFICADO"; la serie nacional lo muestra | `scripts/02_*`, `scripts/11_*` |
| F8 | Concentración por operador de terminal (94,25%) y por cargador (47,02%) | `data/web/concentracion_exportacion_2020_2025.csv` |
| F12 | `% Pais` sin `ALLEXCEPT` con tabla; Balance con `ABS`; medidas `Ratio Exportado` y `% Ductos con Capacidad Reportada` retiradas | `powerbi/dax_measures.md` |
| F13 | Investigado, **sin corregir** (ver más abajo) | — |
| F15 | Alias documentado como inferencia; ids originales intactos | `scripts/02_*` |
| F16 | +1.660% → +1.761% | `powerbi/dax_measures.md` |
| F18 | Pozos a más de 30 km de su yacimiento marcados y listados; no se borran de los datos | `scripts/13_*`, `data/web/pozos_coordenadas_dudosas.csv` |
| Rutas | `VM_DATA_ROOT`, `VM_RAW_DIR`, `VM_CLEAN_DIR`, `VM_WEB_DIR`; ningún script escribe en `raw/` | `scripts/_rutas.py` |
| F9, F10, F11, F14, F17, F19 | **Fase 3** (textos) | — |

Los archivos históricos de `data/web/` (`indices_mensuales.csv`, `capacidad_ductos.csv`, `resumen_kpis.json`, etc.) se mantienen hasta reescribir el HTML en la Fase 3, para no dejar el dashboard desincronizado.

### ANTES / DESPUÉS de las cifras que cambiaron

| cifra | antes (publicado) | después | causa |
|---|---|---|---|
| Serie de exportación principal | 6 terminales de todo el país: 53,76 M m³ (2018–jun 2026) | Terminales neuquinos: 33,41 M m³ (62,2%); la serie nacional queda como contexto | el 28% era crudo del Golfo San Jorge (TERMAP) |
| Exportación del último mes (jun-2026) | 1.268.381 m³ (nacional) | 1.234.735 m³ = 258.875 bbl/día (neuquina) | alcance de la serie |
| Producción del último mes | 590.754,6 bbl/día (dic-2025, total VM) | 633.371,1 bbl/día (jun-2026, **solo no convencional**) | D3: datos 2026 existentes en `raw/` |
| Variación interanual de producción | +31,92% (dic-25 vs dic-24) | +33,0% (jun-26 vs jun-25, misma base NC); +31,92% sigue siendo el dato de dic-2025 | D3 |
| Índice (año 2025) | base promedio 2019: producción 656,29 (dic-25), exportación 400,48 (jun-26) | base 2022, promedios anuales: exportación 227,0 · producción VM 206,4 · producción de la cuenca 168,1 | la base 2019 era 79% TERMAP |
| Sensibilidad del índice (2025) | no existía | base 2021: 586,0 / 308,7 · base 2023: 208,9 / 164,0 / 144,2 (exportación / VM / cuenca) | D1 / C |
| "Brecha ≥120 puntos desde 2023 y creciente" | afirmación causal sobre la serie nacional | media móvil 12m, base 2022, a diciembre: 2023 → VM 125,8 · cuenca 116,6 · exportación 108,8; 2024 → 159,1 · 138,1 · 121,4; 2025 → 206,2 · 168,0 · 226,5 | la exportación neuquina por terminales queda por detrás de la producción en 2023–2024 y la supera en 2025 |
| % exportado (nuevo) | — | de la cuenca: 20,8% (2022) · 19,4% · 18,2% · 28,1% (2025); de VM: 30,1% · 26,0% · 22,9% · 33,1% | solo 2022–2025 para la cuenca |
| VMOC | 171,1% | retirado (D2); 123,3% / 89,3% con un solo segmento no se publican | numerador sumaba 2 segmentos en serie |
| Ductos sobre 100% | 6 (web) / 3 (Power BI) | 3 en un ranking de 43 ductos: Allen–Puerto Rosales 129,7 · LINDERO ATRAVESADO-CENTENARIO 111,1 (2 meses, "a revisar") · Centenario–Allen L14 106,9 | numerador, segmentos, reglas de capacidad |
| "57 con capacidad / 85 sin capacidad" | 142 ductos mezclando universos | 83 ductos lógicos que mueven petróleo: 43 en ranking · 6 con capacidad dudosa en todos los años · 34 sin capacidad en el Anexo 2A | F4 |
| Exclusión de ductos | 6 ductos completos (42, 97, 149, 171, 221, 329) | 40 ducto-años en 20 ductos (R1 4 · R3 23 · R4 2 · R5 11 · D2 1) | 97, 171 y 329 daban valores absurdos por sumar gas, no por error del Anexo |
| Concentración | "94% en 3 empresas/terminales" | 94,25% por operador de terminal · 47,02% top 3 por cargador | F8 |
| Volatilidad mensual | 76,85% vs 5,18% (14,8×, 2020–25, exportación nacional) | exportación neuquina 34,02% vs producción VM 2,55% (13,3×, 2022–25); nacional 76,85% como contexto | misma serie y ventana de los datos completos |
| Volumen sin país | no se mostraba en el HTML | 27,99% (15.044.986 m³), 100% TERMAP; 79% del volumen de 2019 y 4% del de 2026 | F7 |
| Salto "+1.660%" | +1.660% | +1.761% (17.022 → 316.714 m³) | cálculo |
| Balance, % exportado/producido | −19,0 / −26,6 / −28,8% | 19,0 / 26,6 / 28,8% (con `ABS`) | signo del Balance |
| Producción total de la Cuenca Neuquina (nuevo) | — | 2022–2025: 20,44 · 23,83 · 28,31 · 34,36 M m³; VM = 69,1 · 74,5 · 79,6 · 84,8% | A |
| Oleoducto a Chile (nuevo, aparte) | no considerado | 35.039 · 71.020 · 79.998 bbl/día (2023 · 2024 · 2025) | B |
| Pozos con coordenada dudosa | 0 marcados | 2 (153751 y 159086; 0,066% de la producción) | F18 |

## Decisiones abiertas (a resolver con tu OK)

1. **Oleoducto a Chile en la serie principal.** La planilla 20 trae exportaciones de petróleo por el ducto "Puesto Hernandez - Buta Mallin" (Oleoducto Trasandino Argentina S.A.), de 2023-05 a 2026-06. Equivalen al 48% del volumen de los terminales neuquinos en 2025. Con ellos, el % exportado de la cuenca sería 27,9% (2023) · 32,8% (2024) · 41,6% (2025). Hoy va aparte y no se suma.
2. **F13, planilla 20.** Evidencia fuerte de doble conteo en los ductos 374 y 489 (volumen repetido por tramo). Corregirlo cambia poco: el ranking pasa de 43 a 44 ductos y los ductos sobre 100% siguen siendo 3.
3. **Meses sin exportación 2019–2021.** Oiltanking reportó operaciones pero ninguna exportación en 10 meses de 2019, 6 de 2020 y 1 de 2021; se tratan como cero reportado (no afecta 2022 en adelante).
4. **Allen–Puerto Rosales 2024** encabeza el ranking con operativa = diseño = empleada = 36.000 m³/día. Propongo marcarlo "a revisar" (regla R6, solo marca).
5. **Producción de la cuenca antes de 2022.** El portal oficial publica una "Serie histórica de producción de petróleo por cuenca y sub tipo de recurso (Capítulo IV)" que permitiría reconstruirla; hace falta tu OK para descargarla.

## Investigación F13 (sin corregir)

- **Planilla 20 (ductos 374 y 489, y el gasoducto 156): doble conteo confirmado.** Hay 344 filas idénticas en todo salvo `longitud_tramo` (un registro por tramo del mismo volumen). Sin la repetición, el caudal observado dividido por la capacidad "empleada" que informa la propia empresa da 1,00 en el ducto 489 (2023 y 2024) y 0,84–1,07 en el 374; con la repetición daba 2,0 y 1,7–2,1.
- **Planilla 21 (59 pares de cargadores con el mismo volumen exacto): no hay evidencia de doble conteo.** Los volúmenes de los pares (~10.000 m³ cada uno) son la mitad de un embarque típico (mediana 14.431 m³ en CGC, 23.693 m³ en Oiltanking), lo que es más compatible con un reparto en mitades entre dos cargadores. No se puede confirmar sin datos del buque.
