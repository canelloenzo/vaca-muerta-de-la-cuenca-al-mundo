> **Nota:** documento de trabajo del proceso. El modelo final de Power BI tiene 6 páginas (ver `README.md`).

# Vaca Muerta: plan de acción para Power BI (revisado contra los datos reales)

Este documento reemplaza las secciones 4-7 de `guia_proyecto_vaca_muerta.md` una vez confrontada la guía
contra la estructura real de los 12 archivos en `data/raw/`. El diccionario de datos completo está en
`data/clean/diccionario_datos.md`; los scripts de limpieza en `data/scripts/`.

---

## 1. Los tres desvíos que cambian el proyecto

### 1.1. No existe el dataset "Comercio Exterior de Hidrocarburos por país destino"
La guía asume un CSV de exportaciones en USD por país (sección 2, fila "Comercio Exterior..."). **Ese
archivo no está entre los 12 que me pasaste.** Lo que sí hay:

| Archivo real | Qué es | Por qué no es un reemplazo directo |
|---|---|---|
| `volumenes-de-transporte-de-hidrocarburos-planilla-21.csv` | Movimientos por terminal, con país destino explícito (21 países reales tras limpieza) | Es **volumen**, no USD. Es la mejor aproximación disponible. |
| `volumnenes-de-transporte-de-hidrocarburos-planilla-20.csv` | Movimientos por ducto/tramo | Campo `pais` completo en solo 0,9% de filas (exportación directa por ducto) |
| `Balance_2023/2024/2025_*.xlsx` | Balance Energético Nacional anual | Agregado a nivel país-año completo, sin apertura por país destino ni por mes; en miles de TEP, no USD |
| `precio-exportacion-crudo.xlsx` | Precio USD/bbl por tipo de crudo | Solo precio, no volumen ni valor total |

**Decisión recomendada:** construir el KPI de exportación como **volumen por país** (desde planilla-21) como
métrica primaria, y agregar un **valor USD estimado** = volumen × precio (cruzando `producto` con
`dim_tipo_crudo_cuenca` y `dim_precio_exportacion_crudo`) rotulado explícitamente como estimación, solo para
crudo (no hay serie de precios para gas/GNL en los archivos entregados). Si el USD real es importante para el
posteo de LinkedIn, hay que bajar el dataset real de comercio exterior de datos.energia.gob.ar — no vino en
este lote.

### 1.2. Capacidad nominal de gasoductos — RESUELTO PARCIALMENTE (actualizado 2026-08-12)
En la primera vuelta, ningún archivo traía capacidad nominal. Con el **Anexo 2A** (`anexo-2a-capacidad-de-
transporte-de-hidrocarburos-a-travs-de-ductos.csv`) el KPI original de la guía, `Utilización % =
volumen_transportado / capacidad`, **ya se puede calcular** — con tres condiciones que hay que respetar:

1. **La clave de unión es `idducto`, no `idtramo`** (`idtramo` no es un espacio de IDs compartido entre el
   Anexo 2A y `fact_transporte_ductos` — se verificó y descartó).
2. **Conversión de unidad obligatoria:** la capacidad del Anexo 2A es un caudal **diario** (m³/día);
   `fact_transporte_ductos.volumen` es un total **mensual**. Hay que multiplicar la capacidad diaria por los
   días del mes antes de dividir — dividir volumen mensual directamente por capacidad diaria infla el
   resultado ~30x. Ya resuelto en `fact_capacidad_ductos.csv`.
3. **Cobertura parcial:** el cruce cubre 41,1% de las combinaciones ducto-año con transporte real (45,4% a
   nivel fila ducto-mes) — el 55-59% restante son ductos, en general menores o provinciales, que no reportan al
   Anexo 2A. El KPI es válido para los ductos cubiertos, no para el universo completo de `fact_transporte_ductos`.

Con esas correcciones, la mediana de utilización sale en 0,54 (RIC 0,25-0,81), un rango físicamente razonable.
Hay un residuo de 6 ductos (de ~91) con utilización >5x que parece error de carga del Anexo 2A en origen, no
un problema del cruce — ver detalle y lista de IDs en `data/clean/diccionario_datos.md`.

**Decisión recomendada:** usar `fact_capacidad_ductos.csv` como fuente del KPI de utilización, filtrando por
`capacidad_valida = True` y excluyendo/anotando los 6 ductos con utilización sospechosa (42, 97, 149, 171, 221,
329). Para los ductos sin cobertura, mantener como respaldo la narrativa de "volumen transportado en el
tiempo" (sección 4, Grupo B) en vez de forzar un % de utilización sin denominador confiable.

### 1.3. El campo de filtro de la guía para Vaca Muerta apunta a la columna equivocada
La guía filtra por `formprod.str.contains("Vaca Muerta")`. En los datos reales, `formprod` es un **código
corto** (`VMUT`, `CENT`, `FIMP`...) — nunca contiene el string "Vaca Muerta". El campo correcto es `formacion`
(texto completo, minúsculas, sin tilde: `"vaca muerta"`). Ya corregido en `data/scripts/01_clean_produccion.py`.
Además: no existe columna `periodo` (está partida en `anio`/`mes`) ni `dias_del_mes` (se calculó como campo
derivado `dias_mes`).

---

## 2. Otros hallazgos relevantes (menores pero accionables)

- **Encoding real (corregido 2026-09-10):** los archivos crudos son UTF-8 puro con BOM (verificado a nivel de
  bytes: ej. la cuenca "ÑIRIHUAU" está guardada como `0xC3 0x91` + "IRIHUAU", la codificación UTF-8 correcta de
  "Ñ"). **No hay pérdida de información en origen** — lo que parecía mojibake irreversible era: (a) el script
  `01_clean_produccion.py` leyendo esos CSV con `encoding="latin-1"` en vez de `utf-8`/`utf-8-sig`, lo que
  fabrica mojibake donde no lo había, reparado después con `ftfy` + un diccionario manual (`CUENCA_FIX`); y
  (b) la consola de Windows usada durante la exploración, que no renderiza bien los caracteres acentuados y los
  muestra como `�` aunque el byte subyacente sea correcto. Verificado en `clean/`: no quedan caracteres de
  reemplazo (`U+FFFD`) reales en ningún campo de texto revisado. Power BI va a mostrar los nombres con tilde
  correctamente. Separador real: `,` (no `;`).
- **Vaca Muerta no es 100% no convencional:** 193.886 registros NO CONVENCIONAL vs. 11.028 CONVENCIONAL sobre
  205.082 filas totales. Si el proyecto quiere hablar específicamente del "boom shale", filtrar además por
  `sub_tipo_recurso == 'SHALE'`; si quiere hablar de "toda la formación Vaca Muerta", dejar ambos.
  ~722,4 millones de barriles acumulados 2006-2025 en el filtro amplio.
- **Coordenadas de pozo solo existen para pozos no convencionales** (`dim_pozo_coordenadas_no_convencional.csv`,
  3.335 pozos). Los ~238 pozos convencionales de Vaca Muerta no se pueden ubicar en el mapa de la Página 2.
- **El archivo "no-convencional" solapa 100% con las filas 2022-2025 de los archivos anuales** — se usó solo
  para sumar el histórico 2006-2021 (87.157 filas adicionales), evitando duplicar producción.
- **Nueva dimensión disponible que la guía no contemplaba:** `registro-del-midstream-ductos-empresas.csv`
  (362 ductos, con provincia/jurisdicción/año de construcción) — vale la pena sumarla al modelo como
  `Dim_Ducto`, con 95,6% de cobertura contra `fact_transporte_ductos`.
- **`producto` en transporte tiene 156 grafías distintas** para ~15 categorías reales — se generó
  `producto_norm` (103 valores, colapsando tildes/mayúsculas/espacios); la diversidad remanente es en buena
  parte real (grados de gasoil, crudos importados con nombre propio como Bonny Light/Forcados).
- **Anexo 2A trae filas duplicadas por tramo y por cargador** con la capacidad repetida idéntica en cada
  duplicado — hay que dedupear a nivel ducto-año antes de usar la capacidad, nunca sumarla (sumar
  multiplicaría la capacidad real por la cantidad de cargadores/tramos reportados).
- **Anexo 2B y Anexo 2B por Plantas (capacidad de almacenamiento) se evaluaron y quedaron fuera del modelo**:
  dominio distinto (stock, no flujo), cobertura débil de nodos contra el resto del modelo (10/28 y 4/28 nodos
  cruzan con transporte/exportación respectivamente) y varios de los nodos de mayor capacidad están en Golfo
  San Jorge, no en la cuenca Neuquina de Vaca Muerta. Quedan documentados en `diccionario_datos.md` por si el
  proyecto suma explícitamente un cuarto acto de "almacenamiento" más adelante.

---

## 3. Modelo de datos revisado (esquema estrella)

```
                              Dim_Fecha
                                  │
        ┌─────────────┬──────────┼───────────┬──────────────┐
        │             │          │           │              │
  Dim_Yacimiento  Dim_Pozo   Fact_Produccion  Dim_Ducto ──── Fact_Capacidad
   (yacimiento/     (coord.  (pozo-mes o          │              Ductos
    provincia/       solo NC)  yacim-mes)   Fact_Transporte  (Anexo 2A, ducto-mes)
    cuenca)                                   Ductos
                                              (planilla 20)

                                              Dim_Pais ── Fact_Movimientos
                                                              Exportacion
                                                             (planilla 21)
                                                                    │
                                                            Dim_TipoCrudo ── Fact_PrecioCrudo
                                                            (cuenca/prov.)   (USD/bbl mensual)

  Fact_BalanceEnergetico (anual, nacional, sin FK a Dim_Pais/Dim_Ducto — tabla de contexto aislada)

  [fuera del modelo: Anexo 2B / 2B-Plantas (almacenamiento) — ver diccionario_datos.md]
```

**Tablas y grano:**

| Tabla | Grano | Filas | Archivo fuente |
|---|---|---|---|
| Fact_Produccion | pozo-mes (o yacimiento-mes agregado) | 205.082 (15.762 agregado) | `fact_produccion_pozo_mes_vaca_muerta.csv` |
| Fact_TransporteDuctos | empresa-ducto-tramo-producto-mes | 56.566 | `fact_transporte_ductos.csv` |
| Fact_CapacidadDuctos | ducto-mes | 3.603 | `fact_capacidad_ductos.csv` |
| Fact_MovimientosExportacion | nodo-empresa-producto-país-mes | 3.543 | `fact_movimientos_exportacion_ductos.csv` |
| Fact_PrecioCrudo | tipo_crudo-tipo_precio-mes | 480 | `dim_precio_exportacion_crudo.csv` |
| Fact_BalanceEnergetico | producto-categoría-año (nacional) | 2.160 | `fact_balance_energetico_nacional.csv` |
| Dim_Ducto | ducto | 362 | `dim_ducto.csv` |
| Dim_TipoCrudo | tipo de crudo | 9 | `dim_tipo_crudo_cuenca.csv` |
| Dim_Pozo_Coordenadas | pozo (solo no convencionales) | 3.335 | `dim_pozo_coordenadas_no_convencional.csv` |

`Fact_CapacidadDuctos` se relaciona con `Fact_TransporteDuctos` a través de `Dim_Ducto` (ambas tienen
`idducto`) — no unir directamente entre sí en Power BI para evitar relaciones muchos-a-muchos; cada una cuelga
de `Dim_Ducto` y `Dim_Fecha` por separado, y las medidas de utilización combinan ambas vía `RELATED`/`CALCULATE`.

`Dim_Fecha`, `Dim_Yacimiento` y `Dim_Pais` se construyen en Power Query (CALENDAR() y VALUES/DISTINCT sobre las
columnas correspondientes), igual que planteaba la guía original.

---

## 4. KPIs revisados

### Grupo A — Producción (sin cambios de fondo, con una corrección de DAX)
- `Prod Petróleo (bbl/día)` = `DIVIDE(SUM(Fact_Produccion[prod_pet_bbl]), SUM(Fact_Produccion[dias_mes]))` —
  la guía usaba `DISTINCTCOUNT(dias_del_mes)`, columna inexistente; `dias_mes` ya viene calculado en la tabla
  limpia.
- Variación interanual y Top 5 yacimientos: se mantienen tal como en la guía, funcionan sobre
  `fact_produccion_yacimiento_mes_vaca_muerta.csv`.
- **Nuevo KPI sugerido:** % de producción CONVENCIONAL vs. NO CONVENCIONAL dentro de Vaca Muerta — dato que
  la guía no anticipaba y que es un buen matiz para el storytelling ("Vaca Muerta no es solo shale").

### Grupo B — Transporte (KPI ancla recuperado, con salvedades)
- `Utilización % = DIVIDE(SUM(Fact_CapacidadDuctos[volumen_transportado]), SUM(Fact_CapacidadDuctos[capacidad_mensual_m3]))`,
  filtrando `capacidad_valida = TRUE` y excluyendo los 6 `idducto` con utilización sospechosa (42, 97, 149,
  171, 221, 329 — ver 1.2 y diccionario). Es el KPI original de la guía, ya calculable sobre
  `Fact_CapacidadDuctos`.
- **Importante:** este KPI solo es representativo para el ~45% de ducto-meses con cobertura del Anexo 2A
  (`capacidad_valida = TRUE`). Para el resto, no mostrar un % de utilización sin denominador — usar el
  respaldo de abajo.
- **Respaldo/complemento para ductos sin capacidad reportada:** `Volumen Transportado =
  SUM(Fact_TransporteDuctos[volumen])`, con eje de tiempo por `tramo_transporte` o `denominacion_ducto`,
  filtrando `tipo_producto = "Petroleo"` — sigue mostrando tendencia de saturación aunque no haya capacidad
  para relativizarla.
- **Evolución de la utilización en el tiempo:** mismo cálculo del primer KPI con eje de tiempo — ahora sí
  disponible; es el ángulo que la guía quería para conectar con la justificación de VMOS/Oldelval.

### Grupo C — Exportación (redefinido sobre datos volumétricos)
- `Volumen Exportado = SUM(Fact_MovimientosExportacion[volumen])`, filtrando `tipo_operacion = "Exportacion"`
  o `tipo_mercado = "Externo"`.
- `% País = DIVIDE(CALCULATE([Volumen Exportado], ALLEXCEPT(Fact_MovimientosExportacion, Dim_Pais)), CALCULATE([Volumen Exportado], ALL(Dim_Pais)))`
  — misma lógica que la guía, cambiando USD por volumen.
- `Valor USD Estimado` (opcional) = volumen de crudo × `precio_usd_bbl` (join por tipo de crudo y mes) —
  rotular como estimación en el dashboard, no como cifra oficial.
- Ratio producción/exportación: calculable en volumen (bbl producidos vs. m³ exportados, con conversión de
  unidades), no en USD, salvo que se consiga el dataset oficial de comercio exterior.

---

## 5. Páginas del dashboard (ajustadas)

1. **Resumen ejecutivo** — igual que la guía, con volumen de exportación en vez de USD si no se consigue el
   dataset oficial.
2. **Mapa de producción** — igual, pero acotar el texto a "pozos no convencionales" o agregar una nota
   aclarando que los pozos convencionales de Vaca Muerta no tienen coordenadas en la fuente.
3. **Evolución en el tiempo** — sin cambios.
4. **Destinos de exportación** — sin cambios de estructura, cambiando USD por volumen (m³) como métrica
   principal.
5. **Infraestructura y cuello de botella** — recuperado tal como lo planteaba la guía: gráfico de "% de
   utilización" por ducto/corredor en el tiempo (fuente `Fact_CapacidadDuctos`, filtrando `capacidad_valida`),
   con "volumen transportado" (`Fact_TransporteDuctos`) como complemento para los ductos sin capacidad
   reportada; la línea de tiempo de hitos (VMOS, Oldelval) se mantiene igual, sigue siendo anotación manual.

---

## 6. Orden de trabajo sugerido (actualizado 2026-08-12)

El Anexo 2A resolvió el KPI de capacidad, así que la semana 5 original (decidir si perseguir datasets externos)
se acorta: solo queda pendiente el comercio exterior en USD (ver sección 7 — y ojo, puede que ya no sea
"externo": ver nota al final).

| Semana | Foco |
|---|---|
| 1 (hecho) | Exploración real de los 12 archivos originales, limpieza en Python, diccionario de datos |
| 1b (hecho) | Anexo 2A integrado como `Fact_CapacidadDuctos`; Anexo 2B evaluado y dejado fuera del modelo |
| 2 | Cargar las 9 tablas limpias en Power Query, construir Dim_Fecha/Dim_Yacimiento/Dim_Pais, armar relaciones (incluyendo `Fact_CapacidadDuctos` ↔ `Dim_Ducto`) |
| 3 | Medidas DAX Grupo A y B — el KPI de utilización ya no es un reemplazo, es el original de la guía |
| 4 | Página de destinos de exportación (volumen) + mapa de producción (con nota sobre cobertura de coordenadas) + página de infraestructura/cuello de botella con el % de utilización real |
| 5 | Definir si se persigue el dataset oficial de comercio exterior en USD (ver sección 7); pulido visual, redacción, capturas |

---

## 7. Si querés cerrar la brecha de USD
El dataset de capacidad de ductos ya se integró (Anexo 2A). Queda un solo pendiente del plan original:
- **Comercio Exterior de Hidrocarburos** (datos.energia.gob.ar, sección Comercio Exterior) — exportaciones en
  USD por país y producto.

**Nota:** en `data/raw/` apareció un archivo nuevo, `TD_comercioexterior.xlsx`, que no estaba en el alcance de
esta consigna y todavía no fue explorado — por el nombre, podría ser justamente este dataset. Si querés, en la
próxima vuelta lo reviso con el mismo criterio (estructura real, sin asumir nada) y evalúo si cierra la brecha
de USD de la sección 1.1.
