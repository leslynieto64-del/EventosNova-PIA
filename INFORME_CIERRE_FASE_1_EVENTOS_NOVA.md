# Informe de cierre de la fase 1 — Eventos Nova

**Fecha:** 24/10/2026
**Referencia de alcance:** `Cierre_Alcance_Eventos_Nova_FINAL_APROBADO_20261023.md`. Decisiones A, B y C y reglas C-01 a C-15. Archivo intacto: SHA-256 `b67d2f47…45487a`.
**Antecedentes conservados:**
- `docs/INFORME_SINCRONIZACION_DOCUMENTAL_20261023.md` (primera sincronización).
- `INFORME_FINAL_VALIDACION_DOCUMENTAL.md` (segunda revisión). Su apartado de exportaciones pendientes queda superado por este informe.

## 1. Estado final

**La fase 1 queda cerrada.**
- BRD, historias con Gherkin, glosario, matriz, BPMN y mapa de dominio son coherentes entre sí y con el alcance aprobado.
- Las 29 exportaciones de diagramas se regeneraron desde las fuentes finales y se revisaron.
- Las exportaciones de Word y Excel corresponden a sus fuentes.

## 2. Documentos fuente sincronizados

| Documento | Estado comprobado |
|---|---|
| `docs/unidad 2/Reporte_BRD_Corregido.docx` y `.pdf` | BN-001–BN-010 y SE-001–SE-012 coherentes con A, B, C y C-01–C-15. El PDF corresponde al DOCX actual |
| `docs/unidad 2/User_Stories_corregido.docx` y `.pdf` | 33 historias y 114 criterios, todos asignados a una historia existente. El PDF corresponde al DOCX actual |
| `docs/unidad 2/Glosario_Corregido.docx` y `.pdf` | GL-001–GL-062 sin duplicados. El PDF corresponde al DOCX actual |
| `docs/trazabilidad/matriz-trazabilidad.xlsx` y `.pdf` | 29 filas. Los criterios de cada fila pertenecen a las historias de esa fila, y las reglas pendientes de implementar se señalan como tales. El PDF corresponde al XLSX actual |
| 9 pares `.bpmn` / `.drawio` en `diagramas/bpmn/` | Coherentes con el alcance y entre sí |
| `diagramas/dominio/mapa-dominio.drawio` | 6 páginas; cada página de detalle es idéntica a su copia en la página 00 |

Los PDF de Word y Excel se generaron en la etapa anterior, después del último cambio en sus fuentes. Se comprobó que contienen todos los identificadores y los textos modificados, así que **no se regeneraron**.

## 3. Cambios de esta última etapa

Solo se corrigieron defectos de presentación detectados al revisar los diagramas con el texto medido. Ninguno cambia reglas ni identificadores.

| Archivo | Cambio | Motivo |
|---|---|---|
| SP-04 y maestro (`.bpmn` y `.drawio`) | Nota `SP04_NotaEleg`: alto de 64 a 80 px | Su texto ocupaba 72 px y desbordaba la caja |
| SP-05 y maestro (`.bpmn` y `.drawio`) | Etiqueta «En organización» de `SP05_F05` / `MAE_F263`: 8 px a la derecha | Se montaba sobre la compuerta `SP05_GwEstado` |
| Maestro (`.drawio`) | Rótulos de carril repetidos `x31`, `x32` y `x36` («Coordinador» y «Administración»): desplazados a la derecha | Los cruzaban los flujos de mensaje `MAE_M26`, `MAE_M37` y `MAE_M52` |
| Todas las exportaciones de diagramas | Regeneradas (sección 5) | Las anteriores no reflejaban las fuentes |
| `diagramas/LEEME_EXPORTACIONES.txt` | Actualizado | Relaciona cada fuente con sus exportaciones |

No se modificaron el BRD, las historias, el glosario ni la matriz. Siguen vigentes las correcciones de las dos etapas anteriores.

## 4. Revisión visual de los diagramas

**Herramienta.** No hay draw.io ni un modelador BPMN en el entorno. Se usó un renderizador propio de páginas draw.io en Chromium, que viene incluido. Este renderizador:
- dibuja cada página a partir del `.drawio`: forma, posición, colores, conectores, puntos y etiquetas;
- mide cada texto con las fuentes reales (Arial / Liberation Sans e Inter) y lo reparte en líneas como lo hace el navegador;
- calcula automáticamente cuatro comprobaciones: texto que desborda su caja, textos superpuestos, texto sobre nodos ajenos y conectores que cruzan textos o atraviesan nodos.

Después **revisé visualmente las imágenes resultantes**:
- SP-01, SP-02, SP-04 y SP-08 completos;
- las páginas 1, 3, 7, 12 y 16 del maestro paginado, que incluyen las zonas de SP-02 y SP-04;
- las 5 páginas del mapa de dominio, con ampliaciones de los Detalles A y C.

**Resultados automáticos** (comparados con los originales):

| Diagrama | Desbordes | Textos superpuestos | Texto sobre nodo | Conector que cruza texto | Conector que atraviesa nodo |
|---|---|---|---|---|---|
| Maestro | 1 → **0** | 1 → **0** | 1 → **0** | 3 → **0** | 0 → 0 |
| SP-01, SP-03, SP-06, SP-07, SP-08 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| SP-02 | 0 → 0 | 1 → **0** | 0 → 0 | 0 → 0 | 0 → 0 |
| SP-04 | 1 → **0** | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| SP-05 | 0 → 0 | 0 → 0 | 1 → **0** | 0 → 0 | 0 → 0 |
| Mapa de dominio (páginas 01–05 y 00) | 0 → 0 | 0 → 0 | — | Sin cruces nuevos | Sin cruces nuevos |

En el mapa de dominio, los textos están dentro de marcos decorativos (agregados y máquinas de estados). Por eso la columna «texto sobre nodo» no es significativa ahí. Las dos transiciones añadidas en la etapa anterior no cruzan ningún texto.

**Comprobado en la revisión visual:**
- Las etiquetas caben en sus cajas.
- Las compuertas tienen salidas etiquetadas («Sí» / «No» o la condición correspondiente).
- Los inicios y fines son coherentes: el flujo del pago posterior al cierre tiene su propio inicio de mensaje.
- Los cambios estructurales se ven como se diseñaron:
  - compuerta de contratación confirmada en SP-04;
  - flujo del pago posterior al cierre en SP-02;
  - subproceso de llegada de T;
  - en el mapa de dominio, las transiciones por T y las etiquetas de Sin efecto, Importe incorrecto y devolución A.

**Límite:** la revisión es sobre este renderizado, no sobre draw.io. Los símbolos de eventos, los grosores y algunos detalles gráficos pueden verse distintos al abrir los `.drawio`. Posiciones, tamaños, textos y conexiones son los de la fuente, y la coherencia `.drawio` ↔ `.bpmn` está validada (sección 6).

## 5. Exportaciones regeneradas y verificadas

| Exportación | Origen | Verificación |
|---|---|---|
| `BPMN_Eventos_Nova.svg` / `.png` / `.pdf` | `BPMN_Eventos_Nova.drawio` | SVG bien formado de 39 174 × 2 115; PNG del mismo tamaño; PDF de 1 página (14 000,9 × 756 pt) |
| `BPMN_Eventos_Nova_paginado.pdf` | El mismo | 19 páginas A3 con los mismos tramos, la misma escala (59 %) y el mismo índice que la versión anterior; nombres de carril en el margen |
| SP-01 a SP-08: `.svg` / `.png` / `.pdf` (8 × 3) | Su `.drawio` | SVG bien formado del tamaño de su página; PNG a 1,5×; PDF de 1 página; mismas dimensiones que las exportaciones anteriores |
| `mapa-dominio.pdf` | `mapa-dominio.drawio`, páginas 01 a 05 | 5 páginas de 1 440,96 × 1 008,96 pt, como el original |

**Comprobaciones sobre los archivos generados:**
- Todos se abren: `pdfinfo` y el análisis XML de los SVG no dan errores, y los PNG tienen las dimensiones esperadas.
- El texto extraído de los PDF contiene los cambios vigentes:
  - «¿La contratación está confirmada?» y «Solicitud no registrada» en el maestro, SP-04 y el paginado;
  - «Pago de anticipo después del cierre» y «Dejar sin efecto el anticipo pendiente y devolver…» en el maestro, SP-02 y el paginado;
  - «llega T sin firma» y «o llegada de T» en el mapa de dominio.
- Se regeneraron también SP-03, SP-05, SP-06 y SP-07 para que todo el conjunto use el mismo método y el mismo aspecto. SP-05 era además necesario por la corrección de la sección 3.

## 6. Validaciones realizadas

| Validación | Resultado |
|---|---|
| Identificadores (BN 10, SE 12, US 33, CA 114, GL 62) | Sin duplicados y numeración continua |
| Referencias cruzadas (BRD, historias, glosario, matriz, 9 BPMN, 9 draw.io BPMN, mapa de dominio) | 0 referencias a identificadores inexistentes |
| Criterios ↔ historias (tabla de trazabilidad del documento de historias y columna C de la matriz) | 0 incoherencias |
| Integridad DOCX/XLSX | ZIP válido y todas las partes XML bien formadas. Estilos, numeración, tema, filtros, área de impresión, paneles y combinaciones sin cambios (comprobado en la etapa anterior; las fuentes no se tocaron después) |
| Estructura BPMN (9 archivos): ids, referencias, entradas y salidas, inicio y fin, carriles, DI, extremos de aristas, solapes y cruces de nodos | **0 errores**. Se mantienen 23 + 3 + 3 + 3 avisos de diseño: eventos de borde sin carril y subprocesos que ocupan dos carriles |
| Coherencia `.drawio` ↔ `.bpmn`: geometría, puntos, conexiones, textos y posición de etiquetas | **0 diferencias** en los 9 pares |
| Integridad de draw.io (padres, orígenes, destinos e ids por página) | 0 referencias rotas |
| Mapa de dominio: páginas 01–05 frente a su copia en la página 00 | 0 diferencias |
| Ajuste de textos y cruces con texto medido | Sección 4: 0 incidencias en los 9 BPMN y en el mapa de dominio |
| Exportaciones frente a sus fuentes | Sección 5 |
| Archivo de alcance | SHA-256 sin cambios |

## 7. Documentación de implementación conservada sin cambios

El informe de arquitectura, el README, el resumen de la Unidad 3, los ADR, la bitácora, el plan E3D y los diagramas de clases y secuencia se mantienen como documentación de la implementación existente. Describen el prototipo actual, por ejemplo el anticipo exacto del 30 % y solo devoluciones SE-012. Se actualizarán cuando el código incorpore las reglas, en la fase siguiente; no forman parte de esta fase.

En cuanto al contrato ya firmado al llegar T, los documentos conservan la regla literal de C-01, y todo lo demás de ese caso está documentado según C-02, C-04, A-1, A-3 y A-6. Como se indicó, no se amplió el alcance.

## 8. Limitaciones

**Única limitación técnica:** no hay draw.io ni otro modelador en el entorno.
- Por eso las exportaciones se generaron con un renderizador propio en Chromium, y la revisión visual se hizo sobre ese renderizado.
- **Para resolverlo:** abrir los `.drawio` en draw.io una vez y, si se desea el aspecto exacto de draw.io, volver a exportar con los mismos nombres. No hace falta tocar ninguna fuente.

No se ejecutaron pruebas automatizadas: el paquete no incluye código, y la fase no lo requiere.
