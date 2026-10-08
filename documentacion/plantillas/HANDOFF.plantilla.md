# Traspaso: Vaca Muerta, de la cuenca al mundo

Insumo para escribir, en otra conversación, el posteo de LinkedIn, la entrada del CV y la preparación de entrevista. Este archivo no contiene el posteo ni el CV. Todas las cifras salen de `data/web/registro_cifras.json`; no hay que recalcular nada ni usar una cifra que no esté acá con su alcance.

## 1. Enlaces públicos

- Repositorio: <https://github.com/canelloenzo/vaca-muerta-de-la-cuenca-al-mundo>
- Dashboard web (GitHub Pages): <https://canelloenzo.github.io/vaca-muerta-de-la-cuenca-al-mundo/>
- Release con el `.pbix`: <https://github.com/canelloenzo/vaca-muerta-de-la-cuenca-al-mundo/releases/latest>
- LinkedIn del autor: <https://www.linkedin.com/in/enzocanello>

## 2. Qué es el proyecto, en cuatro líneas

Pipeline en Python (pandas) que limpia datos públicos de la Secretaría de Energía y ENARGAS, un modelo y reporte de Power BI de 6 páginas, y un dashboard web con Chart.js. Cuenta la historia en tres actos: producción, transporte y exportación de petróleo de la cuenca Neuquina. Una auditoría completa encontró {{hallazgos_n:0}} hallazgos que se corrigieron antes de publicar. Cada cifra publicada declara su alcance y una prueba automática compara los textos con el registro de cifras.

## 3. Mensajes que los datos sostienen

- La producción de petróleo de Vaca Muerta fue de {{prod_ultimo_mes_bbl_dia:0}} bbl/día en junio de 2026 (solo no convencional), {{prod_var_interanual_pct:1}}% más que un año antes.
- Casi todo el petróleo de Vaca Muerta es no convencional: {{pct_nc_2022_2025:2}}% del volumen de 2022–2025.
- La exportación de crudo de la cuenca Neuquina (comercio exterior declarado) pasó de {{pct_exp_cuenca_2022:1}}% de la producción de la cuenca en 2022 a {{pct_exp_cuenca_2025:1}}% en 2025, y de {{exp_2022_bbl_dia:0}} a {{exp_2025_bbl_dia:0}} bbl/día. En 2025 valió USD {{exp_2025_usd_millones:0}} millones.
- Con las tres bases del índice (2021, 2022 y 2023), la exportación de la cuenca crece más que la producción de la cuenca en cada año posterior a la base. Esa lectura es de la serie de comercio exterior; con la de terminales marítimos la dirección en 2024 cambia según la base.
- Destinos 2020–agosto 2026: Estados Unidos {{comex_eeuu_pct:1}}% y Chile {{comex_chile_pct:1}}%.
- Las 3 mayores empresas exportadoras concentran {{conc_exp_top3_pct:1}}% (2020–2025). Es otra medida que el {{conc_top3_operadores_pct:2}}% de los 3 mayores operadores de terminal de todo el país.
- El corredor Allen–Puerto Rosales movió {{allen_total_2025_m3:0}} m³ de petróleo en 2025, {{allen_crec_2025_pct:1}}% más que en 2024, con la línea nueva Duplicar desde marzo de 2025.
- La capacidad de los ductos no es una base sólida para concluir: las fuentes no coinciden en Allen–Puerto Rosales y el petróleo transportado en 2024 superó la capacidad que informa el Anexo. Solo {{ductos_ranking_n:0}} de {{ductos_petroleo_n:0}} ductos que mueven petróleo tienen capacidad utilizable; {{ductos_sobre_100_n:0}} superan el 100% en su tramo más cargado ({{ductos_sobre_100_a_revisar_n:0}} de ellos con la capacidad marcada "a revisar"), sin que los datos permitan decidir si es sobrecarga o capacidad mal informada.

## 4. Lo que NO se puede decir

- Que la exportación sea "de Vaca Muerta" únicamente: la serie incluye todo el crudo de la cuenca Neuquina, convencional y no convencional.
- Que el volumen exportado es el que dicen los terminales marítimos o el que dice el comercio exterior: las dos fuentes oficiales no concilian desde 2023 y no hay información para decidir.
- Cualquier cifra de utilización de VMOC: se retiró (decisión D2).
- Que un ducto esté "sobrecargado" por superar el 100% de su capacidad informada: las capacidades de las fuentes no coinciden.
- Fechas y capacidades de VMOS o Duplicar Norte como hechos: son anuncios de las empresas y del Estado, con fuente y fecha, en una caja aparte.
- Una causa para la volatilidad de la exportación.
- Un valor de mercado en USD: es el monto FOB declarado por las empresas.
- Producción convencional de 2026.

## 5. Hallazgos de la auditoría (F1–F19), una línea cada uno

- **F1.** La exportación de la planilla 21 incluía terminales de todo el país; se pasó primero a terminales neuquinos y, tras hallar el comercio exterior por cuenca, a esa serie, con el índice en base 2022 y sensibilidad.
- **F2.** La utilización de ductos sumaba gas y segmentos en serie; ahora usa líquidos y el tramo más cargado. Se retiró la cifra de VMOC.
- **F3.** Se excluían 6 ductos completos por un supuesto error de carga que en 3 casos era gas en el numerador; ahora se excluye por ducto-año con reglas explícitas.
- **F4.** El conteo "con capacidad / sin capacidad" mezclaba universos; ahora se parte de los {{ductos_petroleo_n:0}} ductos que mueven petróleo.
- **F5.** El rótulo de capacidad válida solo exigía un valor mayor a cero; se agregaron reglas de capacidad dudosa y se cambió el rótulo.
- **F6.** Había producción de 2026 en los datos crudos sin usar; se incorporó la de junio como no convencional y se rotuló su alcance.
- **F7.** El volumen sin país identificado no figuraba en el HTML; ahora se muestra ({{comex_sin_pais_pct:1}}% sin país en el comercio exterior) y se conserva la etiqueta original.
- **F8.** La concentración por operador de terminal se presentaba como concentración de exportadores; ahora se mide por empresa exportadora y se aclara la diferencia.
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

### Hallazgos posteriores a la auditoría

- **G1.** El archivo de comercio exterior se había descartado por leer solo la tabla visible; sus datos completos (caché de la tabla dinámica) traen origen por cuenca, país, empresa y USD, y pasaron a ser la serie principal.
- **G2.** La serie oficial de producción por cuenca reemplaza la suma por pozo para la cuenca: coincide salvo en septiembre de 2024, donde los archivos por pozo quedan {{sep24_dif_cuenca_m3:0}} m³ por debajo.
- **G3.** Las dos fuentes oficiales de exportación no concilian desde 2023; se muestran lado a lado en lugar de elegir en silencio.
- **G4.** El valor en USD sale del monto FOB declarado y se validó contra la tabla oficial de precios (correlación {{val_precios_corr:2}} en {{val_precios_meses:0}} meses de 2020–2021).

## 6. Capturas sugeridas

1. Dashboard web, encabezado y tarjetas: muestra la cifra principal con su alcance y las cuatro tarjetas (producción, incidencia no convencional, exportación con USD, concentración).
2. Dashboard web, índices base 2022 con las tablas de promedios anuales y sensibilidad: muestra que la conclusión se sostiene con las tres bases.
3. Dashboard web, gráfico de petróleo transportado por los principales ductos y tabla de capacidades por fuente: muestra el dato sólido y por qué no se publica un porcentaje de utilización.
4. Dashboard web, tabla de contraste entre fuentes oficiales y nota de que no concilian: muestra el criterio de transparencia.
5. Power BI, página 3 (índices base 2022) y página 4 (capacidad informada): muestra el modelo corregido.
6. Salida de la suite de pruebas pasando: muestra el control automático de cifras y textos.
7. Dashboard web, destinos y valor en USD: muestra adónde va el crudo y a qué precio.

## 7. Preguntas que puede hacer un entrevistador

- Por qué la serie principal es comercio exterior y no los terminales marítimos, y qué pasa con las diferencias entre fuentes.
- Por qué el año base es 2022 y qué cambia con 2021 o 2023.
- Por qué no se publica la utilización de VMOC.
- Cómo se evita que un texto contenga una cifra equivocada (registro de cifras y pruebas).
- Qué quedó fuera: producción convencional de 2026, exportación antes de 2020 y precios de mercado.

## 8. Registro de cifras finales

{{TABLA_REGISTRO}}
