# Traspaso: Vaca Muerta, de la cuenca al mundo

Insumo para escribir, en otra conversación, el posteo de LinkedIn, la entrada del CV y la preparación de entrevista. Este archivo no contiene el posteo ni el CV. Todas las cifras salen de `data/web/registro_cifras.json`; no hay que recalcular nada ni usar una cifra que no esté acá con su alcance.

## 1. Enlaces públicos

- Repositorio: <https://github.com/canelloenzo/vaca-muerta-de-la-cuenca-al-mundo>
- Dashboard web (GitHub Pages): <https://canelloenzo.github.io/vaca-muerta-de-la-cuenca-al-mundo/>
- Release con el `.pbix`: <https://github.com/canelloenzo/vaca-muerta-de-la-cuenca-al-mundo/releases/latest>
- LinkedIn del autor: sin completar (el autor lo agrega al publicar el posteo).

## 2. Qué es el proyecto, en cuatro líneas

Pipeline en Python (pandas) que limpia datos públicos de la Secretaría de Energía y ENARGAS, un modelo y reporte de Power BI de 6 páginas, y un dashboard web con Chart.js. Cuenta la historia en tres actos: producción, transporte y exportación de petróleo de la cuenca Neuquina. Una auditoría completa encontró {{hallazgos_n:0}} hallazgos que se corrigieron antes de publicar. Cada cifra publicada declara su alcance y una prueba automática compara los textos con el registro de cifras.

## 3. Mensajes que los datos sostienen

- La producción de petróleo de Vaca Muerta fue de {{prod_ultimo_mes_bbl_dia:0}} bbl/día en junio de 2026 (solo no convencional), {{prod_var_interanual_pct:1}}% más que un año antes.
- Casi todo el petróleo de Vaca Muerta es no convencional: {{pct_nc_2022_2025:2}}% del volumen de 2022–2025.
- Los terminales neuquinos exportaron en 2025 un promedio de {{exp_neu_2025_bbl_dia:0}} bbl/día, el {{pct_exp_cuenca_2025:1}}% de la producción de la cuenca; en 2022 era el {{pct_exp_cuenca_2022:1}}%. El oleoducto a Chile se mide aparte.
- En 2025 la exportación neuquina queda por encima de la producción de Vaca Muerta con las tres bases del índice; en 2024 la dirección depende de la base, por eso no se afirma una tendencia.
- La concentración depende de cómo se mida: {{conc_top3_operadores_pct:2}}% por operador de terminal y {{conc_top3_cargadores_pct:1}}% por cargador (2020–2025).
- Solo {{ductos_ranking_n:0}} de {{ductos_petroleo_n:0}} ductos que mueven petróleo tienen capacidad utilizable; {{ductos_sobre_100_n:0}} superan el 100% en su tramo más cargado, sin que los datos permitan decidir si es sobrecarga o capacidad mal informada.

## 4. Lo que NO se puede decir

- Que la exportación de la planilla 21 sea "de Vaca Muerta": solo el {{exp_neuquina_pct_del_nacional:1}}% del volumen total es crudo neuquino.
- Cualquier cifra de utilización de VMOC: se retiró (decisión D2).
- Una tendencia entre exportación y producción en 2023–2024: cambia de signo con la base.
- Una causa para la volatilidad de la exportación.
- Valores en USD, producción de la cuenca antes de 2022 o producción convencional de 2026.

## 5. Hallazgos de la auditoría (F1–F19), una línea cada uno

- **F1.** La exportación de la planilla 21 incluía terminales de todo el país; se pasó a terminales neuquinos y el índice a base 2022 con sensibilidad.
- **F2.** La utilización de ductos sumaba gas y segmentos en serie; ahora usa líquidos y el tramo más cargado. Se retiró la cifra de VMOC.
- **F3.** Se excluían 6 ductos completos por un supuesto error de carga que en 3 casos era gas en el numerador; ahora se excluye por ducto-año con reglas explícitas.
- **F4.** El conteo "con capacidad / sin capacidad" mezclaba universos; ahora se parte de los {{ductos_petroleo_n:0}} ductos que mueven petróleo.
- **F5.** El rótulo de capacidad válida solo exigía un valor mayor a cero; se agregaron reglas de capacidad dudosa y se cambió el rótulo.
- **F6.** Había producción de 2026 en los datos crudos sin usar; se incorporó la de junio como no convencional y se rotuló su alcance.
- **F7.** El volumen sin país identificado ({{sin_pais_pct:1}}%) no figuraba en el HTML; ahora se muestra y se conserva la etiqueta original.
- **F8.** La concentración por operador de terminal se presentaba como concentración de exportadores; se publican ambas medidas.
- **F9.** "Convencional desde 2022" era un artefacto de los archivos cargados; ahora figura como "sin dato" antes de 2022.
- **F10.** Frases que afirmaban más de lo que muestran los datos; se reescribieron y una prueba vigila las palabras prohibidas.
- **F11.** Años parciales sin rotular; 2018 y 2026 quedan marcados y fuera de los gráficos anuales.
- **F12.** Medidas DAX con defectos (signo del Balance, filtros sobre tablas); corregidas o retiradas.
- **F13.** Volumen repetido por tramo en la planilla 20; se eliminó el doble conteo. En la planilla 21 no hay evidencia suficiente y no se tocó.
- **F14.** Cobertura de exportación irregular; se eligió un año base con 12 de 12 meses y se avisa del último mes.
- **F15.** Un mismo ducto con dos identificadores; se agregó un identificador lógico sin tocar los originales.
- **F16.** Un salto citado con otro valor al recalcularlo; se corrigió.
- **F17.** Imprecisiones en documentos (conteos de pozos y ductos); corregidas.
- **F18.** Dos pozos con coordenadas dudosas; se omiten del mapa con nota al pie.
- **F19.** Cuadro de hitos de VMOS sin fuente; se elimina del reporte.

## 6. Capturas sugeridas

1. Dashboard web, encabezado y tarjetas: muestra la cifra principal con su alcance y las cuatro tarjetas.
2. Dashboard web, índices base 2022 con las dos tablas (promedios anuales y sensibilidad): muestra que la dirección cambia con la base y cómo se evita una conclusión.
3. Dashboard web, ranking de utilización de ductos con la nota de cobertura: muestra el criterio de exclusión.
4. Dashboard web, concentración por operador de terminal frente a cargador: muestra por qué una misma cifra puede leerse de dos maneras.
5. Power BI, página 3 (índices base 2022) y página 4 (capacidad informada): muestra el modelo corregido.
6. Salida de la suite de pruebas pasando: muestra el control automático de cifras y textos.

## 7. Preguntas que puede hacer un entrevistador

- Por qué la exportación se mide por terminales y no por país o por empresa (alcance, proxy y limitación).
- Por qué el año base es 2022 y qué cambia con 2021 o 2023.
- Por qué no se publica la utilización de VMOC.
- Cómo se evita que un texto contenga una cifra equivocada (registro de cifras y pruebas).
- Qué quedó fuera: producción de la cuenca antes de 2022, USD, convencional de 2026.

## 8. Registro de cifras finales

{{TABLA_REGISTRO}}
