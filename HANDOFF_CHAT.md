# Traspaso: Vaca Muerta, de la cuenca al mundo

Insumo para escribir, en otra conversación, el posteo de LinkedIn, la entrada del CV y la preparación de entrevista. Este archivo no contiene el posteo ni el CV. Todas las cifras salen de `data/web/registro_cifras.json`; no hay que recalcular nada ni usar una cifra que no esté acá con su alcance.

## 1. Enlaces públicos

- Repositorio: <https://github.com/canelloenzo/vaca-muerta-de-la-cuenca-al-mundo>
- Dashboard web (GitHub Pages): <https://canelloenzo.github.io/vaca-muerta-de-la-cuenca-al-mundo/>
- Release con el `.pbix`: <https://github.com/canelloenzo/vaca-muerta-de-la-cuenca-al-mundo/releases/latest>
- LinkedIn del autor: <https://www.linkedin.com/in/enzocanello>

## 2. Qué es el proyecto, en cuatro líneas

Pipeline en Python (pandas) que limpia datos públicos de la Secretaría de Energía y ENARGAS, un modelo y reporte de Power BI de 6 páginas, y un dashboard web con Chart.js. Cuenta la historia en tres actos: producción, transporte y exportación de petróleo de la cuenca Neuquina. Una auditoría completa encontró 19 hallazgos que se corrigieron antes de publicar. Cada cifra publicada declara su alcance y una prueba automática compara los textos con el registro de cifras.

## 3. Mensajes que los datos sostienen

- La producción de petróleo de Vaca Muerta fue de 633.371 bbl/día en junio de 2026 (solo no convencional), 33,0% más que un año antes.
- Casi todo el petróleo de Vaca Muerta es no convencional: 99,88% del volumen de 2022–2025.
- La exportación de crudo de la cuenca Neuquina (comercio exterior declarado) pasó de 20,5% de la producción de la cuenca en 2022 a 32,3% en 2025, y de 72.301 a 191.506 bbl/día. En 2025 valió USD 4.536 millones.
- Con las tres bases del índice (2021, 2022 y 2023), la exportación de la cuenca crece más que la producción de la cuenca en cada año posterior a la base. Esa lectura es de la serie de comercio exterior; con la de terminales marítimos la dirección en 2024 cambia según la base.
- Destinos 2020–agosto 2026: Estados Unidos 45,9% y Chile 27,0%.
- Las 3 mayores empresas exportadoras concentran 58,6% (2020–2025). Es otra medida que el 94,25% de los 3 mayores operadores de terminal de todo el país.
- Solo 44 de 83 ductos que mueven petróleo tienen capacidad utilizable; 3 superan el 100% en su tramo más cargado (2 de ellos con la capacidad marcada "a revisar"), sin que los datos permitan decidir si es sobrecarga o capacidad mal informada.

## 4. Lo que NO se puede decir

- Que la exportación sea "de Vaca Muerta" únicamente: la serie incluye todo el crudo de la cuenca Neuquina, convencional y no convencional.
- Que el volumen exportado es el que dicen los terminales marítimos o el que dice el comercio exterior: las dos fuentes oficiales no concilian desde 2023 y no hay información para decidir.
- Cualquier cifra de utilización de VMOC: se retiró (decisión D2).
- Una causa para la volatilidad de la exportación.
- Un valor de mercado en USD: es el monto FOB declarado por las empresas.
- Producción convencional de 2026.

## 5. Hallazgos de la auditoría (F1–F19), una línea cada uno

- **F1.** La exportación de la planilla 21 incluía terminales de todo el país; se pasó primero a terminales neuquinos y, tras hallar el comercio exterior por cuenca, a esa serie, con el índice en base 2022 y sensibilidad.
- **F2.** La utilización de ductos sumaba gas y segmentos en serie; ahora usa líquidos y el tramo más cargado. Se retiró la cifra de VMOC.
- **F3.** Se excluían 6 ductos completos por un supuesto error de carga que en 3 casos era gas en el numerador; ahora se excluye por ducto-año con reglas explícitas.
- **F4.** El conteo "con capacidad / sin capacidad" mezclaba universos; ahora se parte de los 83 ductos que mueven petróleo.
- **F5.** El rótulo de capacidad válida solo exigía un valor mayor a cero; se agregaron reglas de capacidad dudosa y se cambió el rótulo.
- **F6.** Había producción de 2026 en los datos crudos sin usar; se incorporó la de junio como no convencional y se rotuló su alcance.
- **F7.** El volumen sin país identificado no figuraba en el HTML; ahora se muestra (5,9% sin país en el comercio exterior) y se conserva la etiqueta original.
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
- **G2.** La serie oficial de producción por cuenca reemplaza la suma por pozo para la cuenca: coincide salvo en septiembre de 2024, donde los archivos por pozo quedan 157.933 m³ por debajo.
- **G3.** Las dos fuentes oficiales de exportación no concilian desde 2023; se muestran lado a lado en lugar de elegir en silencio.
- **G4.** El valor en USD sale del monto FOB declarado y se validó contra la tabla oficial de precios (correlación 0,99 en 9 meses de 2020–2021).

## 6. Capturas sugeridas

1. Dashboard web, encabezado y tarjetas: muestra la cifra principal con su alcance y las cuatro tarjetas (producción, incidencia no convencional, exportación con USD, concentración).
2. Dashboard web, índices base 2022 con las tablas de promedios anuales y sensibilidad: muestra que la conclusión se sostiene con las tres bases.
3. Dashboard web, ranking de utilización de ductos con la nota de cobertura: muestra el criterio de exclusión.
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

| Clave | Valor | Unidad | Alcance |
|---|---|---|---|
| `prod_ultimo_mes_bbl_dia` | 633.371 | bbl/dia | jun-2026, solo no convencional (el convencional de 2026 no esta en las fuentes cargadas) |
| `prod_var_interanual_pct` | 33,00 | % | jun-2026 vs jun-2025, ambos solo no convencional |
| `prod_vm_dic2025_bbl_dia` | 590.755 | bbl/dia | dic-2025, Vaca Muerta convencional + no convencional |
| `prod_var_dic2025_pct` | 31,92 | % | dic-2025 vs dic-2024, Vaca Muerta |
| `pct_nc_2022_2025` | 99,88 | % | volumen de petroleo de Vaca Muerta 2022-2025 (unico periodo con convencional observable) |
| `prod_acum_2006_2025_bbl` | 722.439.535 | bbl | Vaca Muerta, 2006-2025, fuentes cargadas |
| `yacimientos_n` | 146 | yacimientos | Vaca Muerta, fuentes cargadas |
| `yac_top1_bbl_dia` | 31.386 | bbl/dia | BAJADA DEL PALO OESTE, promedio de los meses con dato del yacimiento |
| `pct_conv_min_2022_2025` | 0,08 | % | convencional / total de Vaca Muerta, anual 2022-2025 |
| `pct_conv_max_2022_2025` | 0,20 | % | convencional / total de Vaca Muerta, anual 2022-2025 |
| `conv_2022_bbl` | 173.590 | bbl | produccion convencional de Vaca Muerta, 2022 |
| `pozos_nc_con_coordenadas` | 3.062 | pozos | pozos no convencionales con coordenadas en la fuente |
| `pozos_mapa_omitidos` | 2 | pozos | coordenada a mas de 30 km de la mediana de su yacimiento |
| `pozos_mapa` | 3.060 | pozos | pozos dibujados en el mapa |
| `pozos_omitidos_pct_prod` | 0,07 | % | produccion acumulada de los pozos omitidos / total |
| `prod_cuenca_2020_bbl_dia` | 236.002 | bbl/dia | 2020, produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `exp_2020_bbl_dia` | 18.016 | bbl/dia | 2020, promedio diario del anio, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2020_m3` | 1.048.359 | m3 | 2020, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2020_usd_millones` | 226,07 | millones de USD | 2020, monto FOB declarado, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2020_usd_bbl` | 34,28 | USD/bbl | 2020, monto declarado / volumen, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2020_meses` | 6 | meses | 2020: meses con exportacion declarada de crudo de la cuenca Neuquina |
| `pct_exp_cuenca_2020` | 7,63 | % | 2020: exportacion de crudo de la cuenca (comercio exterior) / produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `chile_pct_exp_2020` | 11,89 | % | 2020: parte de la exportacion declarada con destino Chile |
| `prod_cuenca_2021_bbl_dia` | 278.462 | bbl/dia | 2021, produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `exp_2021_bbl_dia` | 28.144 | bbl/dia | 2021, promedio diario del anio, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2021_m3` | 1.633.220 | m3 | 2021, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2021_usd_millones` | 706,65 | millones de USD | 2021, monto FOB declarado, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2021_usd_bbl` | 68,79 | USD/bbl | 2021, monto declarado / volumen, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2021_meses` | 11 | meses | 2021: meses con exportacion declarada de crudo de la cuenca Neuquina |
| `pct_exp_cuenca_2021` | 10,11 | % | 2021: exportacion de crudo de la cuenca (comercio exterior) / produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `chile_pct_exp_2021` | 8,20 | % | 2021: parte de la exportacion declarada con destino Chile |
| `prod_cuenca_2022_bbl_dia` | 352.235 | bbl/dia | 2022, produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `exp_2022_bbl_dia` | 72.301 | bbl/dia | 2022, promedio diario del anio, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2022_m3` | 4.195.638 | m3 | 2022, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2022_usd_millones` | 2.441 | millones de USD | 2022, monto FOB declarado, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2022_usd_bbl` | 92,51 | USD/bbl | 2022, monto declarado / volumen, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2022_meses` | 12 | meses | 2022: meses con exportacion declarada de crudo de la cuenca Neuquina |
| `pct_exp_cuenca_2022` | 20,53 | % | 2022: exportacion de crudo de la cuenca (comercio exterior) / produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `chile_pct_exp_2022` | 3,14 | % | 2022: parte de la exportacion declarada con destino Chile |
| `prod_cuenca_2023_bbl_dia` | 410.640 | bbl/dia | 2023, produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `exp_2023_bbl_dia` | 90.581 | bbl/dia | 2023, promedio diario del anio, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2023_m3` | 5.256.472 | m3 | 2023, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2023_usd_millones` | 2.515 | millones de USD | 2023, monto FOB declarado, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2023_usd_bbl` | 76,06 | USD/bbl | 2023, monto declarado / volumen, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2023_meses` | 12 | meses | 2023: meses con exportacion declarada de crudo de la cuenca Neuquina |
| `pct_exp_cuenca_2023` | 22,06 | % | 2023: exportacion de crudo de la cuenca (comercio exterior) / produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `chile_pct_exp_2023` | 22,44 | % | 2023: parte de la exportacion declarada con destino Chile |
| `prod_cuenca_2024_bbl_dia` | 489.263 | bbl/dia | 2024, produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `exp_2024_bbl_dia` | 119.688 | bbl/dia | 2024, promedio diario del anio, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2024_m3` | 6.964.578 | m3 | 2024, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2024_usd_millones` | 3.327 | millones de USD | 2024, monto FOB declarado, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2024_usd_bbl` | 75,95 | USD/bbl | 2024, monto declarado / volumen, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2024_meses` | 12 | meses | 2024: meses con exportacion declarada de crudo de la cuenca Neuquina |
| `pct_exp_cuenca_2024` | 24,46 | % | 2024: exportacion de crudo de la cuenca (comercio exterior) / produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `chile_pct_exp_2024` | 44,72 | % | 2024: parte de la exportacion declarada con destino Chile |
| `prod_cuenca_2025_bbl_dia` | 592.113 | bbl/dia | 2025, produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `exp_2025_bbl_dia` | 191.506 | bbl/dia | 2025, promedio diario del anio, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2025_m3` | 11.113.169 | m3 | 2025, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2025_usd_millones` | 4.536 | millones de USD | 2025, monto FOB declarado, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2025_usd_bbl` | 64,89 | USD/bbl | 2025, monto declarado / volumen, crudo de la cuenca Neuquina exportado segun comercio exterior declarado por las empresas (producto 'Cuenca Neuquina - ...', todas las vias); incluye convencional y no convencional |
| `exp_2025_meses` | 12 | meses | 2025: meses con exportacion declarada de crudo de la cuenca Neuquina |
| `pct_exp_cuenca_2025` | 32,34 | % | 2025: exportacion de crudo de la cuenca (comercio exterior) / produccion de petroleo de la cuenca Neuquina, serie oficial (convencional + no convencional, todas las provincias) |
| `chile_pct_exp_2025` | 33,77 | % | 2025: parte de la exportacion declarada con destino Chile |
| `prod_vm_2022_bbl_dia` | 243.237 | bbl/dia | 2022, Vaca Muerta (por pozo) |
| `vm_sobre_cuenca_2022` | 69,06 | % | 2022: Vaca Muerta (por pozo) / cuenca Neuquina (serie oficial) |
| `prod_vm_2023_bbl_dia` | 306.023 | bbl/dia | 2023, Vaca Muerta (por pozo) |
| `vm_sobre_cuenca_2023` | 74,52 | % | 2023: Vaca Muerta (por pozo) / cuenca Neuquina (serie oficial) |
| `prod_vm_2024_bbl_dia` | 387.221 | bbl/dia | 2024, Vaca Muerta (por pozo) |
| `vm_sobre_cuenca_2024` | 79,14 | % | 2024: Vaca Muerta (por pozo) / cuenca Neuquina (serie oficial) |
| `prod_vm_2025_bbl_dia` | 501.956 | bbl/dia | 2025, Vaca Muerta (por pozo) |
| `vm_sobre_cuenca_2025` | 84,77 | % | 2025: Vaca Muerta (por pozo) / cuenca Neuquina (serie oficial) |
| `idx_exp_2022_base2021` | 256,89 | indice | promedio anual 2022, base 2021 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2022_base2021` | 149,58 | indice | promedio anual 2022, base 2021 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2022_base2021` | 126,49 | indice | promedio anual 2022, base 2021 = 100, produccion de la cuenca |
| `idx_exp_2022_base2022` | 100,00 | indice | promedio anual 2022, base 2022 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2022_base2022` | 100,00 | indice | promedio anual 2022, base 2022 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2022_base2022` | 100,00 | indice | promedio anual 2022, base 2022 = 100, produccion de la cuenca |
| `idx_exp_2022_base2023` | 79,82 | indice | promedio anual 2022, base 2023 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2022_base2023` | 79,48 | indice | promedio anual 2022, base 2023 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2022_base2023` | 85,78 | indice | promedio anual 2022, base 2023 = 100, produccion de la cuenca |
| `idx_exp_2023_base2021` | 321,85 | indice | promedio anual 2023, base 2021 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2023_base2021` | 188,19 | indice | promedio anual 2023, base 2021 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2023_base2021` | 147,47 | indice | promedio anual 2023, base 2021 = 100, produccion de la cuenca |
| `idx_exp_2023_base2022` | 125,28 | indice | promedio anual 2023, base 2022 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2023_base2022` | 125,81 | indice | promedio anual 2023, base 2022 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2023_base2022` | 116,58 | indice | promedio anual 2023, base 2022 = 100, produccion de la cuenca |
| `idx_exp_2023_base2023` | 100,00 | indice | promedio anual 2023, base 2023 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2023_base2023` | 100,00 | indice | promedio anual 2023, base 2023 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2023_base2023` | 100,00 | indice | promedio anual 2023, base 2023 = 100, produccion de la cuenca |
| `idx_exp_2024_base2021` | 425,27 | indice | promedio anual 2024, base 2021 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2024_base2021` | 238,13 | indice | promedio anual 2024, base 2021 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2024_base2021` | 175,70 | indice | promedio anual 2024, base 2021 = 100, produccion de la cuenca |
| `idx_exp_2024_base2022` | 165,54 | indice | promedio anual 2024, base 2022 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2024_base2022` | 159,19 | indice | promedio anual 2024, base 2022 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2024_base2022` | 138,90 | indice | promedio anual 2024, base 2022 = 100, produccion de la cuenca |
| `idx_exp_2024_base2023` | 132,13 | indice | promedio anual 2024, base 2023 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2024_base2023` | 126,53 | indice | promedio anual 2024, base 2023 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2024_base2023` | 119,15 | indice | promedio anual 2024, base 2023 = 100, produccion de la cuenca |
| `idx_exp_2025_base2021` | 680,45 | indice | promedio anual 2025, base 2021 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2025_base2021` | 308,68 | indice | promedio anual 2025, base 2021 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2025_base2021` | 212,64 | indice | promedio anual 2025, base 2021 = 100, produccion de la cuenca |
| `idx_exp_2025_base2022` | 264,87 | indice | promedio anual 2025, base 2022 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2025_base2022` | 206,36 | indice | promedio anual 2025, base 2022 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2025_base2022` | 168,10 | indice | promedio anual 2025, base 2022 = 100, produccion de la cuenca |
| `idx_exp_2025_base2023` | 211,42 | indice | promedio anual 2025, base 2023 = 100, exportacion de crudo de la cuenca (comercio exterior) |
| `idx_vm_2025_base2023` | 164,03 | indice | promedio anual 2025, base 2023 = 100, produccion de Vaca Muerta |
| `idx_cuenca_2025_base2023` | 144,19 | indice | promedio anual 2025, base 2023 = 100, produccion de la cuenca |
| `anio_base_indice` | 2.022 | anio | primer anio con exportacion en 12 de 12 meses y exportacion >= 10% de la produccion de la cuenca |
| `ma12_exp_dic2023` | 125,21 | indice | media movil 12m a dic-2023, base 2022, exportacion de crudo de la cuenca |
| `ma12_vm_dic2023` | 125,78 | indice | media movil 12m a dic-2023, base 2022, produccion de Vaca Muerta |
| `ma12_cuenca_dic2023` | 116,56 | indice | media movil 12m a dic-2023, base 2022, produccion de la cuenca |
| `ma12_exp_dic2024` | 165,70 | indice | media movil 12m a dic-2024, base 2022, exportacion de crudo de la cuenca |
| `ma12_vm_dic2024` | 159,13 | indice | media movil 12m a dic-2024, base 2022, produccion de Vaca Muerta |
| `ma12_cuenca_dic2024` | 138,87 | indice | media movil 12m a dic-2024, base 2022, produccion de la cuenca |
| `ma12_exp_dic2025` | 264,63 | indice | media movil 12m a dic-2025, base 2022, exportacion de crudo de la cuenca |
| `ma12_vm_dic2025` | 206,21 | indice | media movil 12m a dic-2025, base 2022, produccion de Vaca Muerta |
| `ma12_cuenca_dic2025` | 168,00 | indice | media movil 12m a dic-2025, base 2022, produccion de la cuenca |
| `exp_2026_usd_millones` | 4.793 | millones de USD | enero-agosto de 2026 (anio parcial), monto FOB declarado |
| `exp_2026_meses` | 8 | meses | meses de 2026 con datos de comercio exterior |
| `exp_2026_usd_bbl` | 83,07 | USD/bbl | enero-agosto de 2026, monto declarado / volumen |
| `exp_usd_total_2020_2025_millones` | 13.752 | millones de USD | 2020-2025, monto FOB declarado de crudo de la cuenca Neuquina |
| `contr_comex_sobre_terminales_2020` | 0,97 | razon | 2020: exportacion de comercio exterior / exportacion de Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_comex_sobre_term_mas_oleo_2020` | 0,97 | razon | 2020: comercio exterior / (terminales + oleoducto a Chile de la planilla 20) |
| `contr_comex_sobre_terminales_2021` | 0,99 | razon | 2021: exportacion de comercio exterior / exportacion de Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_comex_sobre_term_mas_oleo_2021` | 0,99 | razon | 2021: comercio exterior / (terminales + oleoducto a Chile de la planilla 20) |
| `contr_comex_sobre_terminales_2022` | 0,99 | razon | 2022: exportacion de comercio exterior / exportacion de Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_comex_sobre_term_mas_oleo_2022` | 0,99 | razon | 2022: comercio exterior / (terminales + oleoducto a Chile de la planilla 20) |
| `contr_comex_sobre_terminales_2023` | 1,14 | razon | 2023: exportacion de comercio exterior / exportacion de Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_comex_sobre_term_mas_oleo_2023` | 0,88 | razon | 2023: comercio exterior / (terminales + oleoducto a Chile de la planilla 20) |
| `contr_comex_sobre_terminales_2024` | 1,35 | razon | 2024: exportacion de comercio exterior / exportacion de Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_comex_sobre_term_mas_oleo_2024` | 0,75 | razon | 2024: comercio exterior / (terminales + oleoducto a Chile de la planilla 20) |
| `contr_comex_sobre_terminales_2025` | 1,15 | razon | 2025: exportacion de comercio exterior / exportacion de Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_comex_sobre_term_mas_oleo_2025` | 0,78 | razon | 2025: comercio exterior / (terminales + oleoducto a Chile de la planilla 20) |
| `contr_term_2020_m3` | 1.080.303 | m3 | 2020: Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_oleo_2020_m3` | 0,00 | m3 | 2020: oleoducto a Chile, planilla 20 (sin dato antes de mayo de 2023) |
| `contr_term_2021_m3` | 1.645.332 | m3 | 2021: Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_oleo_2021_m3` | 0,00 | m3 | 2021: oleoducto a Chile, planilla 20 (sin dato antes de mayo de 2023) |
| `contr_term_2022_m3` | 4.247.905 | m3 | 2022: Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_oleo_2022_m3` | 0,00 | m3 | 2022: oleoducto a Chile, planilla 20 (sin dato antes de mayo de 2023) |
| `contr_term_2023_m3` | 4.615.529 | m3 | 2023: Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_oleo_2023_m3` | 1.364.821 | m3 | 2023: oleoducto a Chile, planilla 20 (sin dato antes de mayo de 2023) |
| `contr_term_2024_m3` | 5.166.186 | m3 | 2024: Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_oleo_2024_m3` | 4.132.626 | m3 | 2024: oleoducto a Chile, planilla 20 (sin dato antes de mayo de 2023) |
| `contr_term_2025_m3` | 9.642.378 | m3 | 2025: Oiltanking + Refineria Bahia Blanca (planilla 21) |
| `contr_oleo_2025_m3` | 4.642.336 | m3 | 2025: oleoducto a Chile, planilla 20 (sin dato antes de mayo de 2023) |
| `contr_acum_comex_sobre_term_mas_oleo_2020_2025` | 0,83 | razon | 2020-2025 acumulado: comercio exterior / (terminales + oleoducto a Chile) |
| `contr_chile_comex_sobre_p20_2023` | 0,86 | razon | 2023: exportacion a Chile de comercio exterior / oleoducto a Chile de la planilla 20 |
| `contr_chile_comex_sobre_p20_2024` | 0,75 | razon | 2024: exportacion a Chile de comercio exterior / oleoducto a Chile de la planilla 20 |
| `contr_chile_comex_sobre_p20_2025` | 0,81 | razon | 2025: exportacion a Chile de comercio exterior / oleoducto a Chile de la planilla 20 |
| `val_precios_meses` | 9 | meses | meses 2020-2021 con precio implicito y precio FOB oficial |
| `val_precios_corr` | 0,99 | correlacion | precio implicito (monto / volumen) vs precio FOB oficial Medanito, 2020-2021 |
| `val_precios_dif_pct` | -1,63 | % | diferencia media del precio implicito frente al FOB oficial, 2020-2021 |
| `comex_registros_n` | 125.532 | registros | registros de exportacion de crudo por cuenca (comercio exterior, 2020-agosto 2026) |
| `comex_pais_total_m3` | 39.384.296 | m3 | 2020-agosto 2026, exportacion de crudo de la cuenca (comercio exterior) |
| `comex_eeuu_pct` | 45,94 | % | 2020-agosto 2026, destino Estados Unidos / exportacion de crudo de la cuenca |
| `comex_chile_pct` | 26,98 | % | 2020-agosto 2026, destino Chile / exportacion de crudo de la cuenca |
| `comex_sin_pais_pct` | 5,94 | % | 2020-agosto 2026, volumen sin pais de destino ('no aplica') / exportacion de crudo de la cuenca |
| `conc_exp_top3_pct` | 58,64 | % | 2020-2025, 3 mayores empresas exportadoras de crudo de la cuenca (agrupando variantes de razon social) / total |
| `conc_exp_top1_pct` | 28,59 | % | 2020-2025, mayor empresa exportadora (VISTA (Vista Oil & Gas / Vista Energy, variantes de razon social)) |
| `conc_exp_top3_sin_agrupar_pct` | 54,91 | % | 2020-2025, 3 mayores razones sociales exportadoras sin agrupar variantes |
| `vol_exp_pct` | 29,20 | % | desvio estandar de la variacion mensual, 2022-2025, exportacion de crudo de la cuenca |
| `vol_cuenca_pct` | 1,71 | % | desvio estandar de la variacion mensual, 2022-2025, produccion de la cuenca |
| `vol_ratio` | 17,04 | veces | cociente de los dos desvios anteriores |
| `sep24_shale_sobre_vm_pct` | 8,60 | % | septiembre de 2024: serie oficial 'shale' sobre Vaca Muerta por pozo (unico mes 2022-2025 con diferencia relevante) |
| `sep24_dif_cuenca_m3` | 157.933 | m3 | septiembre de 2024: produccion oficial de la cuenca menos la suma por pozo |
| `sep24_dif_vm_anual_pct` | 0,70 | % | efecto de esa diferencia sobre la produccion anual 2024 de Vaca Muerta |
| `exp_neu_2022_bbl_dia` | 73.201 | bbl/dia | 2022, promedio de 12 meses, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `exp_neu_2023_bbl_dia` | 79.536 | bbl/dia | 2023, promedio de 12 meses, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `exp_neu_2024_bbl_dia` | 88.782 | bbl/dia | 2024, promedio de 12 meses, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `exp_neu_2025_bbl_dia` | 166.161 | bbl/dia | 2025, promedio de 12 meses, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `chile_2023_bbl_dia` | 35.039 | bbl/dia | 2023: oleoducto Puesto Hernandez - Buta Mallin (planilla 20), promedio de los 8 meses con dato |
| `chile_2023_meses` | 8 | meses | 2023: meses con dato del oleoducto a Chile (planilla 20) |
| `chile_2024_bbl_dia` | 71.020 | bbl/dia | 2024: oleoducto Puesto Hernandez - Buta Mallin (planilla 20), promedio de los 12 meses con dato |
| `chile_2024_meses` | 12 | meses | 2024: meses con dato del oleoducto a Chile (planilla 20) |
| `chile_2025_bbl_dia` | 79.998 | bbl/dia | 2025: oleoducto Puesto Hernandez - Buta Mallin (planilla 20), promedio de los 12 meses con dato |
| `chile_2025_meses` | 12 | meses | 2025: meses con dato del oleoducto a Chile (planilla 20) |
| `exp_neu_ultimo_mes_bbl_dia` | 258.874 | bbl/dia | jun-2026, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `exp_neu_ultimo_mes_m3` | 1.234.735 | m3 | jun-2026, crudo exportado por los terminales neuquinos (Oiltanking + Refineria Bahia Blanca, planilla 21); no incluye el oleoducto a Chile |
| `exp_nacional_total_m3` | 53.755.750 | m3 | 2018-jun 2026, 6 operadores de terminal de todo el pais (planilla 21) |
| `exp_neuquina_total_m3` | 33.414.168 | m3 | 2018-jun 2026, Oiltanking + Refineria Bahia Blanca |
| `exp_neuquina_pct_del_nacional` | 62,16 | % | volumen neuquino / volumen de los 6 operadores, 2018-jun 2026 |
| `conc_top3_operadores_pct` | 94,25 | % | 2020-2025, 3 mayores operadores de terminal / 6 operadores (planilla 21; mide quien opera el puerto, no quien exporta) |
| `conc_op1_pct` | 61,08 | % | 2020-2025, operador de terminal n.1 (Oiltanking EBYTEM S.A.) / total de los operadores |
| `conc_op2_pct` | 27,94 | % | 2020-2025, operador de terminal n.2 (TERMAP S.A.) / total de los operadores |
| `conc_op3_pct` | 5,23 | % | 2020-2025, operador de terminal n.3 (COMPAÑÍA GENERAL DE COMBUSTIBLES S.A.) / total de los operadores |
| `ductos_petroleo_n` | 83 | ductos | ductos logicos con volumen de petroleo > 0 en la planilla 20 (los dos id del mismo ducto cuentan una vez) |
| `ductos_ranking_n` | 44 | ductos | ductos de petroleo con capacidad informada valida tras las reglas R1, R3, R4, R5 y D2 |
| `ductos_sin_capacidad_n` | 34 | ductos | ductos de petroleo sin fila en el Anexo 2A |
| `ductos_cap_dudosa_todos_n` | 5 | ductos | ductos de petroleo con capacidad dudosa en todos los anios |
| `ductos_sin_cap_utilizable_n` | 39 | ductos | ductos de petroleo sin capacidad utilizable (sin Anexo 2A o dudosa en todos los anios) |
| `ductos_sobre_100_n` | 3 | ductos | ductos del ranking con utilizacion del segmento mas cargado > 100% en su anio mas reciente valido |
| `ductos_ranking_parcial_n` | 7 | ductos | ductos del ranking cuyo anio mas reciente tiene menos de 12 meses |
| `ductos_ranking_a_revisar_n` | 4 | ductos | ductos del ranking marcados a revisar (R2 o R6) |
| `ducto_anios_excluidos_n` | 36 | ducto-anios | ducto-anios con capacidad dudosa presentes en el modelo |
| `ductos_con_anio_excluido_n` | 18 | ductos | ductos con al menos un anio excluido |
| `regla_r1_veces` | 5,00 | veces | R1: salto de la capacidad operativa entre anios consecutivos |
| `regla_r3_veces` | 2,00 | veces | R3: caudal liquido observado / capacidad empleada informada |
| `regla_r5_dias` | 90 | dias | R5: dias operativos informados en el Anexo 2A |
| `ducto_sobre100_1_pct` | 129,70 | % | Allen - Puerto Rosales 2024 (12 meses), segmento mas cargado de liquidos / capacidad operativa informada |
| `ducto_sobre100_2_pct` | 111,10 | % | LINDERO ATRAVESADO- CENTENARIO 2023 (2 meses), segmento mas cargado de liquidos / capacidad operativa informada |
| `ducto_sobre100_3_pct` | 106,90 | % | Centenario - Allen L14 2024 (12 meses), segmento mas cargado de liquidos / capacidad operativa informada |
| `cobertura_capacidad_ducto_mes_pct` | 45,38 | % | ducto-mes con fila en el Anexo 2A / ducto-mes con transporte (todos los productos) |
| `cobertura_capacidad_ducto_anio_pct` | 39,81 | % | ducto-anio con capacidad operativa > 0 / ducto-anio con transporte (todos los productos) |
| `proxy_pct_producto_neuquino` | 99,52 | % | 2018-jun 2026: volumen exportado por Oiltanking y Refineria Bahia Blanca cuyo producto se rotula Neuquen / Rio Negro (Medanito) / Neuquino |
| `rbb_pct_2024` | 7,53 | % | 2024: Refineria Bahia Blanca / exportacion de los terminales neuquinos (no informa desde febrero de 2026) |
| `rbb_pct_2025` | 2,98 | % | 2025: Refineria Bahia Blanca / exportacion de los terminales neuquinos (no informa desde febrero de 2026) |
| `ductos_ranking_cap_constante_n` | 11 | ductos | ductos del ranking con la misma capacidad operativa en todos sus anios validos (3 o mas anios) |
| `ductos_ranking_un_anio_n` | 4 | ductos | ductos del ranking con un solo anio de capacidad valida |
| `ductos_sobre_100_a_revisar_n` | 2 | ductos | ductos sobre 100% con capacidad marcada a revisar (R2 o R6) |
| `integridad_ductos_con_dato_n` | 34 | ductos | ductos del ranking con caudal de referencia (campo caudal_nominal) informado en Tramos de Integridad (mayor valor entre sus tramos, unidad inferida m3/h, > 100 m3/dia) |
| `integridad_dentro_15pct_n` | 12 | ductos | de esos, ductos con capacidad operativa del Anexo 2A dentro de +-15% del caudal de referencia x 24 |
| `allen_cap_anexo_2024` | 36.000 | m3/dia | Allen - Puerto Rosales, 2024, capacidad operativa del Anexo 2A |
| `allen_cap_anexo_2023` | 50.052 | m3/dia | Allen - Puerto Rosales, 2023, capacidad operativa del Anexo 2A |
| `allen_cap_prensa_2022` | 42.000 | m3/dia | capacidad del tramo Allen - Puerto Rosales tras el proyecto Vivaldi, segun nota de Econojournal de abril de 2022 |
| `allen_util_con_cap_prensa_pct` | 111,17 | % | Allen - Puerto Rosales 2024, mismo volumen del tramo mas cargado sobre 42.000 m3/dia |
| `allen_util_con_cap_2023_pct` | 93,29 | % | Allen - Puerto Rosales 2024, mismo volumen sobre la capacidad operativa que el Anexo 2A informa para 2023 |
| `l14_util_con_nominal_pct` | 53,02 | % | Centenario - Allen L14 2024, mismo volumen sobre el caudal de referencia de Tramos de Integridad x 24 (unidad inferida m3/h) |
| `hallazgos_n` | 19 | hallazgos | auditoria de 2026-10-05, F1 a F19 |
| `bbl_por_m3` | 6,29 | bbl/m3 | factor de conversion usado en todo el proyecto |
| `umbral_km` | 30 | km | script 13: distancia a la mediana de las coordenadas de su yacimiento a partir de la cual se omite un pozo del mapa |
| `umbral_exp_pct` | 10 | % | script 11: exportacion / produccion de Vaca Muerta minima para elegir el anio base del indice |
| `operadores_n` | 6 | operadores | operadores de terminal en la planilla 21 |
