# Complemento de la bitácora de IA — fase final (23/10/2026 a 28/10/2026)

> **Actualización del 28/10/2026 (tarde).** Las iteraciones de este complemento (más una fila para los commits del 20 al 22/10 y la iteración 27) se **integraron en la tabla de la bitácora formal** (`Bitacora_IA_Eventos_Nova.docx`, copiada la estructura de la última fila; resto del paquete sin cambios) y el `.pdf` se regeneró con Word (7 páginas, revisadas visualmente). Este archivo se conserva como respaldo del criterio: lo que no se pudo recuperar sigue marcado como «por transcribir». Después se añadieron a la tabla formal las iteraciones 28 a 30 (corrección de D-1, análisis de D-2 y D-3, corrección de D-2 y D-3 con pruebas, imágenes y guía; PDF regenerado con Word, 7 páginas, últimas páginas revisadas visualmente). Los prompts siguen **sin transcribir**.
>
> **Actualización del 29/10/2026.** Se añadieron a la tabla formal las iteraciones 31 (vencimiento de hecho y reloj de negocio, CIERRE §P) y 32 (cierre documental con T-21, T-23 y T-24 y la última ejecución de la suite, CIERRE §Q), copiando la estructura de la última fila. El `.pdf` se regeneró con LibreOffice 24.2 (las versiones anteriores las exportó Word): conserva encabezado, logotipos, pie y estilo de la tabla, pero la distribución de filas por página cambia y ahora tiene 8 páginas; si se requiere el aspecto exacto de Word, debe volver a exportarse desde Word. Los prompts siguen sin transcribir.
>
> **Qué es este documento.** La bitácora formal (`Bitacora_IA_Eventos_Nova.docx` / `.pdf`, 18 iteraciones, última modificación 19/10/2026, con la suite en 91 pruebas) **no se modificó** y no contiene el trabajo posterior. Este complemento registra, con la información que puede comprobarse en el repositorio, lo realizado después con asistencia de IA. **No sustituye** la bitácora formal: es el borrador de las iteraciones 19 en adelante, que el equipo debe revisar antes de incorporarlas a la tabla del `.docx` (columnas *Iteración, Objetivo, Prompt o enlace, Respuesta útil, Error o supuesto, Decisión del equipo*) y de regenerar el `.pdf`.
>
> **Herramienta:** Claude Code (Anthropic), igual que en la bitácora formal.

## 1. Qué no se puede recuperar aquí

| Dato | Estado |
|---|---|
| Texto literal (prompt) de cada petición de la fase final | **No recuperable desde el repositorio.** Existe en la transcripción local de las sesiones de Claude Code (carpeta `.claude/projects/` del equipo del usuario, fuera de Git), pero no se copió aquí. Hasta que alguien del equipo lo transcriba y lo revise, la columna *Prompt* queda como «por transcribir» |
| Quién del equipo redactó cada petición | **No consta** en el repositorio. No se atribuye ninguna a una persona concreta |
| Commits entre el 20/10 y el 22/10 (State Machines, N6, E3F, F1, F2) | Constan en `git log`, pero **tampoco figuran en la bitácora formal** (que termina el 19/10) |
| Cambios del 23/10 al 28/10 | **Sin commits**: están en el árbol de trabajo (≈ 187 entradas en `git status`); su única huella son los archivos y las fechas indicadas abajo |
| Modelo exacto que respondió en cada sesión | No consta salvo para la sesión del 28/10 (Claude Sonnet 5.5); no se afirma para las anteriores |

**Forma honesta de documentar lo que falta (propuesta):** (1) que el equipo exporte los prompts de la transcripción local de cada sesión y los pegue literalmente, indicando quién los escribió; (2) marcar «no recuperable» lo que no exista; (3) conservar la columna *Decisión del equipo* solo con decisiones que consten por escrito (por ejemplo, `docs/architecture/DECISIONES_E1_E4.md`); (4) no reconstruir conversaciones de memoria.

## 2. Registro verificable (borrador de iteraciones 19 y siguientes)

La columna *Evidencia* son rutas del repositorio. *Prompt*: por transcribir (ver sección 1). *Decisión del equipo*: solo se rellena si consta por escrito; en otro caso, «no registrada».

| N.º (provisional) | Fecha (según archivos) | Objetivo | Respuesta útil / resultado verificable | Error o supuesto documentado | Decisión del equipo | Evidencia |
|---|---|---|---|---|---|---|
| 19 | 24/10 | Auditoría final del paquete: Docker, trazabilidad, cifras del informe, base de datos | Informe con tabla de auditoría, dictamen «listo con pendientes documentados» y 1250 pruebas OK | El informe previo tenía cifras erróneas y la imagen/contenedor de Docker estaba desactualizado (se corrigieron en esa auditoría) | no registrada | `docs/architecture/CIERRE_AUDITORIA_FINAL.md`, `tests/evidencias/*auditoria*-20261024.txt` |
| 20 | 25/10 | Implementar E-1 a E-4 (GL-060 en días hábiles, coherencia solicitud–contrato–evento, pagos parciales del anticipo) | Código y pruebas nuevas; suite de 1306 pruebas OK en el equipo y en Docker; cobertura 98,82 % / 95,85 % | E-2, E-3 y E-4 no tienen respaldo en las fuentes originales; el GL-011 y el BRD («realice la corrección…») admiten dos lecturas de E-3 (documentado el 28/10) | Selección de las opciones A (E-1, E-2, E-3) y B (E-4), y del método de validar el oráculo, **consta** en `DECISIONES_E1_E4.md` como «seleccionada por el equipo»; sin aprobación externa | `docs/architecture/DECISIONES_E1_E4.md`, `docs/ADR/ADR-007-…md`, `tests/evidencias/*e1-e4*-20261025.txt` |
| 21 | 25/10 | Validar el oráculo histórico sin editarlo | Esperados derivados de reglas, 12 pruebas de diferencias, recuento 1203 claves sin diferencias sin explicar | Las «1204 subpruebas» eran 1203 claves más una aserción | Método aprobado por el equipo «con condiciones» según `DECISIONES_E1_E4.md`; aprobación externa pendiente | `tests/apoyo_esperados_oraculo.py`, `tests/test_oraculo_diferencias_e1_e4.py`, `tests/evidencias/diferencias-oraculo-e1-e4-20261025.txt` |
| 22 | 25/10 | Regenerar el reporte PDF y la presentación con las cifras finales | PDF de 7 páginas y 9 diapositivas con 1306 / 98,82 % / 95,85 % | — | no registrada | `docs/entrega/` |
| 23 | 28/10 | Preparar un entorno aislado de pruebas manuales (puerto 8001, base `eventosnova_manual_test`) y su guía | `docker-compose.manual-test.yml`; guía T-14 a T-24 con cuerpos JSON comprobados en una instancia en memoria | En la ejecución manual, T-21 se hizo sobre el evento principal y T-23 con el contrato sin confirmar: son desviaciones del procedimiento que la guía sí preveía (eventos independientes y contratación previa), no un error de cálculo de la guía; la guía no incluía una comprobación explícita de «contratación confirmada» dentro de T-23 (se añadió el 28/10) | no registrada | `docker-compose.manual-test.yml`, `docs/pruebas-manuales/GUIA_PRUEBAS_MANUALES_T14_T24.md` |
| 24 | 28/10 | Diagnosticar por qué `GET /solicitudes?evento_id=` devolvió lista vacía | Causa demostrada: un carácter distinto en el `evento_id` (`…686e…` frente a `…606e…`); sin defecto de código | — | no registrada | `docs/architecture/CIERRE_AUDITORIA_FINAL.md` §I |
| 25 | 28/10 | Cierre documental de la fase 2: README, ADR-007, registro de la validación manual, mapa de dominio, `secuencia_1` | README corregido (migraciones a 0004, E-2 implementada, entorno manual); mapa de dominio y `secuencia_1` regenerados con herramientas locales; verificación cruzada de US/CA con la matriz | Primera versión del PDF del mapa sin actualizar (24/10) detectada y corregida; discrepancia GL-015 frente a la implementación del servicio adicional (hallazgo, sin cambio de código) | no registrada | `README.md`, `diagramas/LEEME_EXPORTACIONES.txt`, `docs/trazabilidad/complemento-trazabilidad-fase-final.md` |
| 26 | 28/10 | Preparar la repetición de T-21 y T-23 | Procedimiento detallado en la guía (sección 11); pruebas **no** ejecutadas | — | no registrada | `docs/pruebas-manuales/GUIA_PRUEBAS_MANUALES_T14_T24.md` |

Las ejecuciones manuales de T-14 a T-24 las hizo el equipo en Swagger; su registro y clasificación están en `docs/architecture/CIERRE_AUDITORIA_FINAL.md` §I.

## 3. Pendiente para completar la bitácora formal

1. Transcribir literalmente los prompts de cada iteración (sección 1, punto 1) y confirmar con el equipo quién los escribió.
2. Añadir las iteraciones 19 en adelante a la tabla de `Bitacora_IA_Eventos_Nova.docx` (con las mismas columnas) y regenerar `Bitacora_IA_Eventos_Nova.pdf`. Esto requiere Word o una herramienta equivalente y no se hizo aquí para no alterar un documento entregable sin poder revisar su aspecto.
3. Incorporar las iteraciones de los commits del 20/10 al 22/10, que tampoco están en la bitácora formal, con la misma regla: solo lo que pueda verificarse.
4. Después de la repetición de T-21 y T-23 por el equipo, añadir una iteración con sus resultados reales (no antes).
