# Informe final de validación documental — Eventos Nova, fase 1

**Fecha:** 24/10/2026
**Referencia de alcance:** `Cierre_Alcance_Eventos_Nova_FINAL_APROBADO_20261023.md` (decisiones A, B y C; reglas C-01 a C-15). SHA-256 `b67d2f47…45487a`, idéntico al adjunto y sin modificar.
**Antecedente:** `docs/INFORME_SINCRONIZACION_DOCUMENTAL_20261023.md` (se conserva sin cambios como registro histórico).
**Paquete de entrada:** `EventosNova_Documentacion_ClaudeChat.zip` (85 archivos). Se trabajó sobre una copia; los adjuntos originales no se modificaron.

## Resultado

**La documentación operativa de requisitos queda sincronizada con el cierre aprobado, con una sola decisión de negocio abierta y con las exportaciones de diagramas pendientes.**

- BRD, historias con Gherkin, glosario y matriz: coherentes con A, B, C y C-01 a C-15; sin identificadores duplicados ni referencias rotas. Sus PDF se regeneraron.
- BPMN y mapa de dominio: se añadieron las transiciones que faltaban, y se validaron su estructura y su coherencia con draw.io. **No hay validación visual en draw.io** (ver 10).
- Queda **una decisión de negocio** sin resolver: qué estado toma un contrato **ya firmado** al llegar T sin contratación confirmada (sección 8).
- **Ninguna exportación de diagrama (PDF, PNG o SVG) se regeneró**. Las afectadas están listadas como desactualizadas (sección 6).
- El informe de arquitectura, el resumen U3, el README y el diagrama de secuencia 1 describen el prototipo anterior a B y A. No se modificaron porque son documentos de implementación (sección 7).

---

## 1. Archivos revisados (inventario)

| Ruta | Formato | Función | Estado encontrado | Acción |
|---|---|---|---|---|
| `Cierre_Alcance_…_FINAL_APROBADO_20261023.md` | MD | Fuente de verdad (A, B, C, C-01–C-15) | Íntegro (SHA-256 igual al adjunto) | Ninguna |
| `LEEME_REVISION.txt` | TXT | Nota del paquete | — | Ninguna |
| `README.md` | MD | README del repositorio de código (etapas E1–F2, máquinas de estados implementadas) | Describe el código actual; no cubre A ni B | Ninguna (documento de implementación, ver 7) |
| `Resumen_EventosNova_U3_Equipo16.docx` / `Resumen_Eventos_Nova_Equipo16.pdf` | DOCX/PDF | Resumen entregable de la Unidad 3 | «anticipo del 30 %» (sin «al menos») | Ninguna (ver 7) |
| `docs/unidad 2/Reporte_BRD_Corregido.docx` | DOCX | BRD (BN-001–010, SE-001–012) | Sincronizado en la fase anterior; faltaba que la contratación no se confirme tras T | **Modificado** |
| `docs/unidad 2/Reporte_BRD_Corregido.pdf` | PDF | Exportación | Desactualizado (21/10) | **Regenerado** |
| `docs/unidad 2/User_Stories_corregido.docx` | DOCX | US-001–033 y CA-001–114 | Sincronizado; faltaban precisiones en CA-070, CA-071, CA-101 y CA-110 | **Modificado** |
| `docs/unidad 2/User_Stories_corregido.pdf` | PDF | Exportación | Desactualizado | **Regenerado** |
| `docs/unidad 2/Glosario_Corregido.docx` | DOCX | GL-001–GL-062 | Sincronizado; definiciones parciales en GL-004, GL-032, GL-052, GL-053 y GL-056 | **Modificado** |
| `docs/unidad 2/Glosario_Corregido.pdf` | PDF | Exportación | Desactualizado | **Regenerado** |
| `docs/trazabilidad/matriz-trazabilidad.xlsx` | XLSX | Matriz BN ↔ reglas ↔ US/CA ↔ CU ↔ arquitectura ↔ ADR | Filas 17, 27 y 28 desfasadas; US omitidas en las filas 6, 14, 24 y 28 | **Modificado** |
| `docs/trazabilidad/matriz-trazabilidad.pdf` | PDF | Exportación | Desactualizado | **Regenerado** |
| `docs/informe/informe-arquitectura-eventos-nova.docx` / `.pdf` | DOCX/PDF | Entregable U3 (arquitectura del prototipo) | Contradice B y A en varios pasajes | Ninguna (ver 7) |
| `docs/ADR/ADR_Eventos_Nova.docx` / `.pdf` | DOCX/PDF | Registro de decisiones | Histórico; sin contradicciones con A, B o C | Ninguna |
| `docs/bitacora ia/Bitacora_IA_Eventos_Nova.docx` / `.pdf` | DOCX/PDF | Bitácora de IA | Histórico | Ninguna |
| `docs/planificacion/Plan_E3D_Final.docx` / `.pdf` | DOCX/PDF | Plan de la etapa E3D | Histórico | Ninguna |
| `docs/INFORME_SINCRONIZACION_DOCUMENTAL_20261023.md` | MD | Informe de la fase anterior | Histórico | Ninguna |
| `diagramas/bpmn/BPMN_Eventos_Nova.bpmn` / `.drawio` | BPMN/Draw.io | Proceso maestro | Faltaban la rama de C-14 en SP-04 y el pago posterior al cierre; desfases draw.io ↔ BPMN | **Modificado** |
| `diagramas/bpmn/…SP02_Contratacion.bpmn` / `.drawio` | BPMN/Draw.io | Contratación | Pago posterior al cierre solo en nota; desfases de etiquetas en draw.io | **Modificado** |
| `diagramas/bpmn/…SP04_Servicio_adicional.bpmn` / `.drawio` | BPMN/Draw.io | Servicio adicional | Precondición C-14 solo en una etiqueta | **Modificado** |
| `diagramas/bpmn/…SP01`, `SP03`, `SP05`–`SP08` (`.bpmn` / `.drawio`) | BPMN/Draw.io | Subprocesos | Correctos | Conservados |
| `diagramas/bpmn/*.pdf`, `*.png`, `*.svg` (28) | PDF/PNG/SVG | Exportaciones bpmn-js | Las de maestro, SP01, SP02, SP04 y SP08 están desfasadas | Conservadas, marcadas (6) |
| `diagramas/dominio/mapa-dominio.drawio` | Draw.io | Mapa de dominio (6 páginas) | Faltaban transiciones por T, B en textos, devolución A en EstadoDevolucion y C-04 | **Modificado** |
| `diagramas/dominio/mapa-dominio.pdf` | PDF | Exportación | Desfasada | Conservada, marcada (6) |
| `diagramas/clases/*.puml/.png/.pdf` | PlantUML | Diseño de clases U3 | Sin reglas en conflicto | Ninguna |
| `diagramas/secuencia/*.puml/.png/.pdf` | PlantUML | Secuencias U3 | `secuencia_1` dice «importe distinto del 30 % pactado» | Ninguna (ver 7) |

Archivos nuevos: `INFORME_FINAL_VALIDACION_DOCUMENTAL.md`, `diagramas/LEEME_EXPORTACIONES.txt` y la carpeta `validacion/`, que contiene renders esquemáticos no oficiales, scripts de validación y un manifiesto SHA-256.

Se conservaron la estructura de carpetas y los nombres. El ZIP de entrada usaba `\` como separador; el nuevo usa `/`, que es lo que exige el formato ZIP. Con eso se abre igual en Windows, macOS y Linux.

## 2. Archivos modificados y motivo

### 2.1 `User_Stories_corregido.docx` (4 nodos de texto; estructura XML idéntica)
| Id | Cambio | Fuente |
|---|---|---|
| CA-110 | Añade: un pago de anticipo registrado antes de T y verificado después de T se verifica sin confirmar ni reactivar la contratación y se devuelve; la fecha de referencia es el día del cierre y la verificación tardía no reinicia el plazo (CA-104) | C-02, A-3, A-6; prueba T-57 del cierre |
| CA-101 | «Dado que el Evento está En gestión…» → «Dado que la contratación del Evento no está confirmada (el Evento está En gestión o Cerrado sin contratación)» | C-14, GL-033 |
| CA-070, CA-071 | Añade «(si el pago se registra después del cierre, el plazo corre desde su registro)» | C-11 (SE-012) |

### 2.2 `Glosario_Corregido.docx` (6 nodos de texto)
| Id | Cambio | Fuente |
|---|---|---|
| GL-052 | En el anticipo el importe es correcto si cubre al menos el 30 %; superarlo no genera por sí mismo una devolución ni aplica el excedente a otra obligación | B-1 a B-4 |
| GL-032 | Si en T el Evento sigue En gestión, no inicia: pasa a Cerrado sin contratación y la contratación ya no puede confirmarse. Plazo SE-012 desde el registro si el pago es posterior al cierre | C-01, C-02, C-11 |
| GL-004, GL-053, GL-056 | Plazo de la devolución SE-012 contado desde el registro del pago cuando este es posterior al cierre | C-11 |

### 2.3 `Reporte_BRD_Corregido.docx` (1 nodo de texto)
- **BN-010.** Añade: la contratación tampoco puede confirmarse después de T. Un anticipo registrado antes de T y verificado después no la confirma ni la reactiva, y se devuelve conforme a BN-009 (C-02, A-3, T-57).

### 2.4 `matriz-trazabilidad.xlsx` (7 celdas; hoja, estilos, filtros, área de impresión, paneles y combinaciones intactos)
| Celda | Cambio |
|---|---|
| E17 | La precondición de C-14 ya está representada como compuerta y rama propia en SP-04 y en el maestro (antes: «solo en la etiqueta, sin rama de rechazo»). |
| E27 | El pendiente se reduce al estado del contrato ya firmado. El anticipo sin verificar en T se resuelve sin confirmar y con devolución A (C-02, A-3, T-57). |
| E28 | Fuentes documentales completas: BN-010, el maestro y los Detalles C y D del mapa. Se mantiene «Pendiente de implementación». |
| C28 | `US-032; CA-102–CA-105` → `US-009, US-032, US-033; CA-102–CA-106, CA-110` |
| C6, C14, C24 | Se añaden las US a las que pertenecen los CA ya citados: US-016 (CA-035), US-017 (CA-038, CA-039) y US-024/US-025 (CA-070, CA-071). Sustituye la referencia informal «las historias de la solicitud cerrada». |

Ninguna fila afirma que una regla esté implementada o probada. Las filas 28 y 29 siguen indicando «Pendiente de implementación».

### 2.5 PDF regenerados
`Reporte_BRD_Corregido.pdf` (43 p.), `User_Stories_corregido.pdf` (46 p.), `Glosario_Corregido.pdf` (25 p.) y `matriz-trazabilidad.pdf` (6 p., A3).

Se generaron con LibreOffice 24.2, la misma herramienta que produjo los originales. Los PDF nuevos usan los mismos tipos de letra que los originales.

## 3. Archivos correctos que se conservaron sin cambios
- **Fuentes de diagramas:** SP01, SP03, SP05, SP06, SP07 y SP08 (`.bpmn` y `.drawio`). El validador no encontró errores en ellos.
- **Diagramas UML:** `clases/*` y `secuencia/*`.
- **Documentos históricos:** ADR, bitácora, plan E3D, informe de la fase anterior, `LEEME_REVISION.txt` y el cierre aprobado.
- **Documentos de implementación:** informe de arquitectura, resumen U3 y README (ver 7).
- **Cambios de la fase anterior que se verificaron y mantuvieron:**
  - US-032, US-033, CA-101 a CA-114, GL-061 y GL-062.
  - Las ediciones del BRD de la fase anterior.
  - Las filas 28 y 29 de la matriz.
  - Los subprocesos de evento de T en SP-01 y SP-02.
  - La ruta de la devolución A en SP-02.

  Se aplicaron solo las precisiones de la sección 2.

## 4. Identificadores afectados
- **Modificados:** CA-070, CA-071, CA-101, CA-110; GL-004, GL-032, GL-052, GL-053, GL-056; BN-010; filas 6, 14, 17, 24, 27 y 28 de la matriz.
- **No se crearon US, CA, GL, BN ni SE nuevos.** Las reglas que faltaban cabían en criterios y definiciones existentes.
- **Identificadores BPMN nuevos.** Se usó el siguiente número libre de cada serie y se comprobó que no existía:
  - SP-04: `SP04_GwContr`, `SP04_NoRegistrar`, `SP04_FinNoRegistrada`; flujos `SP04_F67`–`F69`; mensaje `SP04_M14`.
  - SP-02: `SP02_PagoPost`, `SP02_RegPost`, `SP02_DevPost`, `SP02_FinDevPost`; flujos `SP02_F31`–`F33`; mensaje `SP02_M08`.
  - Maestro: los mismos nodos; flujos `MAE_F324`–`F329`; mensajes `MAE_M61` y `MAE_M62`.
- **Mapa de dominio:** `vA-l35` y `vA-t50` (transición de Contrato), `vC-t50` y `vC-t51` (etiquetas), cada uno con su copia `v2-`/`v4-` en la página 00.

## 5. Cambios estructurales en los diagramas

**SP-04 y maestro (C-14, GL-015, CA-101).**
- Se añadió la compuerta «¿La contratación está confirmada?» antes de «Registrar la solicitud».
- Con «No»: tarea «No registrar la solicitud e informar al Cliente…», fin «Solicitud no registrada (contratación no confirmada)» y mensaje al Cliente.
- `SP04_F01` (maestro: `MAE_F182`) ahora apunta a la compuerta.
- Se desplazaron el inicio, «Registrar», la compuerta del Evento, «No procedente» y su fin. El fin pasa debajo de la tarea para dejar espacio.
- La etiqueta de «Registrar» deja de llevar la precondición, que ahora está en la compuerta.

**SP-02 (A-2, A-3, A-6, CA-103, CA-106).**
- **Flujo nuevo.** Evento de inicio de mensaje «Pago de anticipo después del cierre» → «Registrar y verificar el pago sin aplicarlo a la contratación cerrada ni reabrirla» → «Devolver el importe recibido (devolución A) en 5 días hábiles desde el día del registro» → fin.
- **En el maestro** el fragmento está en el nivel superior del proceso, debajo del subproceso de contratación. Un subproceso embebido no admite un inicio con disparador.
- **Subproceso de evento de T.** La tarea pasa a «Dejar sin efecto el anticipo pendiente y devolver lo recibido (devolución A), aunque se verifique después de T» (C-02, C-04, T-57). La documentación de «Cerrar» limita el pendiente al contrato firmado.
- **Cabeceras de SP-02 y SP-04:** se completaron sus referencias (US-032, US-033, CA-101 a CA-106, CA-110).

**Coherencia draw.io ↔ BPMN corregida** (errores previos detectados por el validador):
- `MAE_F40` y `MAE_F41` conservaban los puntos de entrada y salida anteriores a la ampliación de «Gestionar la propuesta» (desfase de 47 px).
- Faltaba o estaba mal la posición de las etiquetas de `SP02_GwRecibido`, `SP02_F28`/`F29` y `MAE_F321`/`F322`.

**Mapa de dominio** (cada cambio en su página y en la página 00).
- **Detalle A.** Nueva transición de Contrato «En preparación → Cerrado sin confirmar: llega T sin firma (C-01, CA-110)». En Evento, la transición «En gestión → Cerrado sin contratación» indica también «o llegada de T (CA-110)». Cabeceras con CA-109 y CA-110. Invariante «al menos el 30 %» y «la contratación cerrada no se reabre (A-2)».
- **Detalle C.**
  - Pendiente → Sin efecto también para el anticipo pendiente al cerrarse sin confirmar (C-04).
  - Registrado → Importe incorrecto solo para un anticipo inferior al 30 % (B-1).
  - EstadoDevolucion se crea también por la devolución A (GL-061); cabecera con GL-061 y CA-102 a CA-105.
  - ConceptoPago: «al menos el 30 %».
  - Regla nueva: solo dos devoluciones, como máximo una por pago y nunca por más de lo recibido (C-11).
- **Detalle D.** La reacción a `ProcesoContratacionCerrado` incluye la de EstadoCuenta: anticipo Sin efecto y devolución A Pendiente.
- **Pies de fuentes (10):** US-001–US-033, CA-001–CA-114 y GL-001–GL-062.

## 6. Exportaciones
- **Regeneradas y verificadas:** los 4 PDF de la sección 2.5.
  - Cada página se generó desde el DOCX o XLSX actual.
  - Todos los identificadores y textos nuevos aparecen en el PDF.
  - Se revisaron visualmente la página de CA-110 y la página 6 de la matriz.
- **No regeneradas.** No hay draw.io ni bpmn-js en este entorno, y la instalación desde el registro de paquetes fue rechazada (403). Desactualizadas, con su fuente:
  - `BPMN_Eventos_Nova.pdf`, `BPMN_Eventos_Nova_paginado.pdf`, `.png`, `.svg` ← `BPMN_Eventos_Nova.bpmn`
  - `…SP01_Propuesta.pdf/.png/.svg` ← `…SP01_Propuesta.bpmn` (cambió en la fase anterior)
  - `…SP02_Contratacion.pdf/.png/.svg` ← `…SP02_Contratacion.bpmn`
  - `…SP04_Servicio_adicional.pdf/.png/.svg` ← `…SP04_Servicio_adicional.bpmn`
  - `…SP08_Devolucion_SE-012.pdf/.png/.svg` ← `…SP08_Devolucion_SE-012.bpmn` (cambió en la fase anterior)
  - `mapa-dominio.pdf` ← `mapa-dominio.drawio` (páginas 01 a 05)
- **Sin desfase de fuente:** SP03, SP05, SP06 y SP07. Fuente y exportación tienen la misma fecha y la fuente no cambió. No se volvieron a comparar visualmente.

## 7. Pendientes que no se pudieron resolver y su razón
| Pendiente | Razón | Qué hacer |
|---|---|---|
| Estado del contrato firmado al llegar T | Decisión de negocio no definida (sección 8) | Pedir la decisión |
| Exportaciones de la sección 6 | Sin herramientas de exportación | Abrir cada fuente en draw.io (o bpmn-js) y exportar PDF/PNG/SVG con el mismo nombre |
| Revisión visual en draw.io de SP-02, SP-04, el maestro y el mapa de dominio | Sin draw.io | Abrir los `.drawio` y comprobar el ajuste de los textos en sus cajas |
| `informe-arquitectura-eventos-nova.docx`: secciones 6 (CU-02), 8 (copia del glosario: GL-009, GL-011, GL-042, GL-055, GL-057), 8.1 (Anticipo), invariantes de Contrato y EstadoCuenta, 9 (FormalizarContratacionService, GestionPagosService) y 15 (recorrido de CU-02) | Describen el prototipo: anticipo «equivalente/correspondiente al 30 %» y devoluciones solo SE-012. Cambiarlos sin cambiar el código haría que el informe describiera algo que no está implementado | Actualizarlos junto con la matriz de brechas del cierre (§8) |
| `Resumen_EventosNova_U3_Equipo16.docx` («anticipo del 30 %»), `README.md` (máquinas de estados del código) y `secuencia_1_confirmacion_contratacion.puml` (línea 41, «importe distinto del 30 % pactado») | Igual: documentan la implementación actual | Igual |

## 8. Decisión que necesita al responsable del negocio

**D-1. ¿Qué estado toma un contrato ya firmado cuando llega T sin que la contratación se haya confirmado?**

**Lo que ya está definido**, comprobado en el cierre, el BRD, las historias y el glosario:
- El Evento pasa a Cerrado sin contratación (C-01).
- Nada se confirma después de T (C-02).
- El anticipo pendiente queda Sin efecto y el liquidado conserva su estado (C-04).
- La contratación no se reabre (A-2).
- Un pago verificado después de T se verifica sin reactivarla (A-3).
- Todo lo recibido como anticipo se devuelve como devolución A, con fecha de referencia el día del cierre (A-1, A-6).

La prueba T-57 del cierre lo describe para una contratación cerrada en T con un pago liquidado y otro pendiente de verificación. **Esta parte ya no está pendiente** y se documentó en BN-010, CA-110, GL-032 y SP-02.

**Lo que falta:** C-01 solo nombra el destino del contrato **no firmado** (En preparación → Cerrado sin confirmar). Ninguna fuente dice qué pasa con un contrato en estado Firmado.

**Alternativas compatibles con las fuentes:**
1. **Firmado → Cerrado sin confirmar.** Es el mismo estado final que el cierre por anticipo no recibido (SE-010) y el único estado de cierre del contrato en el mapa de dominio.
2. **El contrato conserva Firmado** mientras el Evento queda Cerrado sin contratación. Dejaría un contrato no final en un Evento cerrado, lo que choca con A-2.
3. **Otro estado** definido por negocio.

**Si se elige la 1**, cambian:
- BN-010 y CA-110: «su contrato, firmado o no, …».
- La etiqueta de `SP02_EvT_Cerrar` en SP-02 y en el maestro.
- La transición Firmado → Cerrado sin confirmar por T en el mapa de dominio (Detalle A, páginas 02 y 00).
- La fila 27 de la matriz.
- Más adelante, la máquina de estados de Contrato del código (README, E3B).

**Si se elige la 2 o la 3**, cambian además GL-010 o el estado nuevo y su transición.

**Ya no es una decisión pendiente:** el punto 7.2 del informe anterior, «devolución A cuando el cierre ocurre al llegar T». El encabezado de A la define para toda contratación que queda Cerrada sin contratación, C-01 produce ese estado en T, y T-57 lo expresa literalmente («Contratación cerrada en T … Una devolución A por cada pago»). No hace falta otra aprobación.

**Tampoco son decisiones de negocio:** la rama de rechazo de SP-04 (decisión de modelado, ya aplicada) ni la actualización de los documentos de implementación (decisión de planificación del equipo, sección 7).

## 9. Validaciones ejecutadas y resultados

| Validación | Alcance | Resultado |
|---|---|---|
| Integridad de DOCX y XLSX | 3 DOCX y 1 XLSX: `testzip`, mismas entradas en el mismo orden y con la misma compresión, todas las partes XML bien formadas | Correcto. Solo cambió `word/document.xml` o `xl/worksheets/sheet1.xml`; el resto de partes (estilos, numeración, tema, relaciones) es idéntico byte a byte |
| Solo cambió texto | Comparación del XML vaciando los nodos `w:t` / `t` | Estructura idéntica; nodos de texto cambiados: BRD 1/277, historias 4/818, glosario 6/267, matriz 7/159 |
| Matriz (openpyxl) | Hoja, dimensión A1:F29, autofiltro A4:F29, área de impresión, paneles en A5, 3 rangos combinados, anchos de columna, configuración de página, estilos por celda | Igual que el original. 0 fórmulas, 0 hipervínculos y 0 validaciones antes y después |
| Identificadores | BN 10, SE 12, US 33, CA 114, GL 62 | Sin duplicados y numeración continua; todas las US tienen criterios |
| Referencias cruzadas | Referencias sueltas y rangos en el BRD, las historias, el glosario, la matriz, los 9 BPMN, los 9 draw.io BPMN y el mapa de dominio | 0 referencias a identificadores inexistentes |
| Pertenencia CA → US | Tabla «Validación y trazabilidad» y columna C de la matriz | 0 incoherencias. Había 5 avisos previos en las filas 6, 14 y 24 y 1 causado por la primera versión del cambio en C28; todos se corrigieron en C6, C14, C24 y C28 |
| Coherencia de reglas | Búsqueda de «30 %» sin «al menos» o «mínimo», 7 días hábiles, 5 días naturales aplicados a devoluciones, festivos | 0 casos en los documentos operativos y diagramas. Los casos restantes están en los documentos de implementación de la sección 7 |
| PDF frente a DOCX | Identificadores y vocabulario del DOCX presentes en el PDF | 0 identificadores faltantes. Las páginas aumentan por el contenido de la fase anterior (US 38→46, BRD 40→43, glosario 21→25) |
| Estructura BPMN (validador propio, 9 archivos) | Ids únicos, referencias, incoming/outgoing simétricos, inicio y fin, carriles, DI completo, extremos de aristas sobre su nodo, solapes de nodos, aristas que atraviesan nodos, hijos dentro de su subproceso | **0 errores** en los 9. Mismos avisos que los originales: eventos de borde sin carril y subprocesos que ocupan dos carriles, propios del diseño |
| Etiquetas | Solapes etiqueta-nodo y etiqueta-etiqueta | Los mismos pares que en los originales; ningún solape nuevo |
| Coherencia draw.io ↔ BPMN | Posición y tamaño de cada nodo, puntos intermedios, puntos de entrada y salida, origen y destino, textos, posición de las etiquetas | **0 diferencias** en los 9 pares. En el original había 2 errores de conexión y 6 de etiquetas, todos corregidos |
| Integridad de draw.io | Padres, origen, destino e ids por página (10 archivos) | 0 referencias rotas y 0 ids duplicados |
| Mapa de dominio: páginas 01–05 frente a la página 00 | Valor, geometría y extremos de cada celda frente a su copia | 0 diferencias (también en el original) |
| Revisión visual | Renders esquemáticos propios de SP-02, el inicio de SP-04, el maestro (SP-02 y SP-04) y los Detalles A, C y D, incluidos en `validacion/` | Sin cruces ni solapes nuevos apreciables. **No equivale a draw.io** |
| Cierre aprobado | SHA-256 | Idéntico antes y después |

## 10. Limitaciones
- **No se abrió ningún archivo en Word, Excel, draw.io ni en un modelador BPMN.** La revisión visual de los PDF regenerados se hizo con LibreOffice, por muestreo de páginas. La de los diagramas se hizo con un dibujo esquemático propio. Por tanto **no está verificado** que cada texto de los diagramas quepa en su caja ni su apariencia final.
- **Las exportaciones de la sección 6 no reflejan los cambios.** No se regeneraron.
- **El validador BPMN es estructural.** No ejecuta el modelo ni evalúa toda la semántica BPMN, como la correlación de mensajes o los tokens.
- **El paquete no incluye el código ni las pruebas.** No se ejecutó ninguna prueba automatizada. Ninguna regla se declara implementada; las brechas del cierre (§8) siguen abiertas.
- **La documentación no puede declararse completamente sincronizada** mientras sigan abiertas D-1 y las exportaciones.
