# Lista maestra de correcciones — estado final

Criterio de la etapa (aclaración del 2026-11-05): **no se modifican reglas de negocio, flujos, estructura de PostgreSQL ni datos.** Solo presentación, mensajes, formularios, búsqueda, filtros y validaciones, más el mínimo de backend necesario. Los cambios que exigían tocar una regla se dejaron documentados.

Estados: **Implementada**, **Parcial**, **Documentada** (decisión pendiente, sin cambios de código), **Pendiente**.

## Objetivos

| ID | Objetivo | Estado | Evidencia |
|---|---|---|---|
| OBJ-01 | Conservar lo que ya funciona | Cumplido | Suite completa aislada sin fallos (ver `REPORTE_FINAL_PRUEBAS.md`); sin migraciones; base normal en 0004 |
| OBJ-02 | Formularios y mensajes claros | Implementado (con parciales en COR-01, 04, 10, 14) | COR-02, 03, 06, 12, 16, 17 |
| OBJ-03 | Privacidad del proveedor | Implementada | COR-05 |
| OBJ-04 | Búsqueda y filtros | Implementada | COR-02, COR-13 |
| OBJ-05 | Preparación para GitHub y Render | Preparada, sin ejecutar | `PREPARACION_GITHUB_RENDER.md` |

## Correcciones

| ID | Tema | Estado | Qué se hizo / por qué no |
|---|---|---|---|
| COR-01 | Mensajes de éxito y error | Parcial | Ya existía humanización de mensajes; se añadieron avisos concretos (política, pagos). No se reescribieron los mensajes del backend |
| COR-02 | Selector de proveedores con búsqueda | Implementada | Toda lista desplegable con más de 6 opciones ofrece cuadro de búsqueda que filtra sin cambiar el valor enviado; los resúmenes muestran el nombre del proveedor, no su identificador. Usa la relación servicio–proveedor ya existente |
| COR-03 | Formulario de cuentas por rol (C-03) | Implementada y conservada | Parche local íntegro; se añadió el ojo de contraseña |
| COR-04 | Claridad de importes, pagos y saldos | Parcial | Advertencia de excedente en el resumen del pago (ver COR-07); formatos de importe ya existentes. Falta mostrar el saldo dentro de la etiqueta del importe |
| COR-05 | Separar información cliente/proveedor | Implementada | La API del proveedor (`/mis-asignaciones` y `/proveedores/{id}/eventos/{evento}`) ya no devuelve `condiciones` (texto comercial del contrato con importes). Solo `servicioContratadoId`, `servicio`, `estado`, `respuesta`. Sin cambio de esquema. Pruebas ajustadas: ver nota |
| COR-06 | Reemplazar nombres técnicos | Implementada | Los conceptos de pago (`SaldoContratoOriginal` → «Saldo del contrato original», `CargoCambioTardio` → «Cargo por cambio tardío», etc.), los tipos de solicitud y el tipo de devolución se muestran con etiquetas legibles en todas las pantallas. Los valores internos, los filtros y lo que se envía a la API no cambian. Los identificadores (EV-…, CT-…, EC-…) se conservan visibles a propósito, para trazabilidad. Las pruebas comparan contra los valores reales del dominio, de modo que un concepto nuevo sin etiqueta hace fallar la prueba |
| COR-07 | Pagos mayores al saldo | Implementada solo como advertencia, verificada en Chrome | Por las reglas B-4/B-5/X-14 el excedente se sigue permitiendo. El resumen de confirmación destaca en un bloque aparte que el importe supera el saldo y que no se devuelve automáticamente; con un importe igual al saldo no aparece. No se bloquea nada ni se cambia la política de no reembolso. Comprobado sin confirmar ningún pago |
| COR-08 | Cargo por cambio tardío | Documentada | Hoy la tarifa la envía quien registra el cambio. Hacerla venir de configuración cambiaría el contrato de la API y rechazaría cambios tardíos sin tarifa: es cambio de regla. Se intentó, se revirtió y queda solo el texto del formulario que indica usar la tarifa autorizada. Alternativa a futuro: variable de configuración con la tarifa y rechazo de tarifas distintas, con tu autorización |
| COR-09 | Cancelación del proveedor y cambios de menú | Documentada | Sin funciones nuevas: no hay flujo aprobado de cancelación por el proveedor; el proveedor solo responde mientras el servicio está «Pendiente de confirmación» |
| COR-10 | Validaciones de formularios | Parcial | Se conservaron las existentes; no se añadieron restricciones nuevas |
| COR-11 | Operaciones ya realizadas / duplicados | Parcial | Aviso preventivo en la comunicación de la política. **No** se añadió bloqueo en backend: hoy una segunda comunicación reemplaza la fecha; impedirlo cambia el comportamiento de una operación existente. Anexos duplicados ya los rechaza el backend |
| COR-12 | Mostrar/ocultar contraseña | Implementada | Login, crear cuenta, restablecer contraseña |
| COR-13 | Búsqueda y filtros en cuentas | Implementada | Texto (nombre, correo, proveedor), rol y estado; mensaje cuando no hay coincidencias |
| COR-14 | Actualización automática tras operaciones | Parcial | Las pantallas tocadas se repintan al terminar la operación; no se revisó cada pantalla |
| COR-15 | Servicios asignados al proveedor | Implementada | Vista sin condiciones comerciales, con servicio, estado y respuesta |

Nota COR-05: dos pruebas existentes (`test_h01_h02_proveedores`) afirmaban que el proveedor veía `condiciones`; se quitó solo ese campo de la comparación (el resto sigue verificándose) y se añadió la comprobación de que ya no existe. Es la única expectativa modificada.

## Hallazgos nuevos

| ID | Hallazgo | Estado |
|---|---|---|
| COR-16 | El formulario de cambio no precargaba los datos actuales del evento | Implementada | Al marcar «El cambio modifica los datos del evento» aparecen tipo, fecha y hora, lugar e invitados actuales. Por omisión la casilla está sin marcar y los datos solo se envían con esa acción explícita; abrir y cancelar no modifica el evento. Los controles de plazos, permisos y reglas siguen en el servidor |
| COR-17 | Un pago «Registrado» sin verificar no se distinguía claramente | Implementada | Cada pago muestra su estado oficial con una explicación (Registrado: pendiente de verificación y aún no se suma a lo pagado; Verificado: ya se suma). La columna «Verificado» indica «Pendiente de verificación» y un aviso cuenta los pagos sin verificar. Es solo presentación: nada se verifica automáticamente. El proveedor no ve pagos (permiso existente) |
| COR-18 | El selector de pago mostraba el concepto en bruto (`concepto — saldo`) | Resuelto con COR-06 | El selector muestra el concepto legible y el saldo |
| COR-19 | La política de comunicación puede sobrescribirse sin guardia | Documentada (ver COR-11) |

## Pruebas con fechas especiales
Se ejecutaron en la suite automatizada con fechas controladas (cambio tardío < 7 días, servicio adicional < 5 días, plazos hábiles, vencimientos).

**Escenarios con la hora real del servidor (Ronda 2 pendiente).** El «reloj controlado» del proyecto es un reemplazo de dependencia que solo existe en las pruebas automatizadas; el servidor manual usa la hora real de la Ciudad de México y no se modificó ningún reloj. Para reproducir las reglas sin tocar la boda se usaron dos eventos nuevos e independientes en la base manual, con fecha a 5 y 4 días naturales:

| Escenario | Evento | Resultado esperado (regla) | Resultado |
|---|---|---|---|
| Cambio tardío (equivale a 15/03 frente a 20/03) | 5 días naturales | Menos de 7 días: cargo por cambio tardío con la tarifa de la solicitud (500.00, valor de prueba) | Una sola obligación nueva «Cargo por cambio tardío» de 500.00 con plazo de 24 horas, un anexo, pago verificado, cambio **Confirmada** y evento de 19:00 a 20:00. Sin duplicados |
| Servicio adicional fuera de plazo (equivale a 16/03 frente a 20/03) | 4 días naturales | Menos de 5 días: «No procedente» | Solicitud **No procedente** («quedan menos de cinco días naturales»); sin obligaciones ni anexos nuevos |

La boda de la Ronda 2 no se modificó (7 pagos verificados por 12,700.00, 5 anexos, versión 8). Los dos eventos nuevos quedan en la base manual como datos de prueba. La prueba literal con las fechas de marzo de 2027 sobre la boda sigue siendo posible en esa fecha, pero las reglas ya quedaron verificadas de extremo a extremo.