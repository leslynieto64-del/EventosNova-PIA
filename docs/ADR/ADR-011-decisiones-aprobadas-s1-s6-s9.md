# ADR-011: Decisiones aprobadas S-1 a S-6 y S-9 (roles, separación de funciones y procedencia de las respuestas)

- **Estado:** **Aprobadas por el equipo el 2026-11-01** (S-1, S-2, S-3, S-4, S-5, S-6 y S-9) e **implementadas** ese mismo día.
- **Fecha:** 2026-11-01
- **Relacionada con:** ADR-009 (D-P2, S-7, S-8), ADR-010 (D-P1, D-P3), `../SEGURIDAD_Y_PERMISOS.md` y `../SEGURIDAD_MATRIZ_PERMISOS.md` (matriz generada)
- **Con esta decisión quedan formalizadas todas las decisiones de negocio y de permisos del proyecto** (D-P1 a D-P3 y S-1 a S-9).
- **Respaldo documental:** el BRD define cuatro interesados (Coordinador, Cliente, Proveedor y Administración) y sus responsabilidades; **no define cuentas, roles ni autenticación**, así que los nombres de rol, la separación de funciones y la procedencia de las respuestas son **decisiones de diseño aprobadas por el equipo**, no requisitos del BRD. Donde el BRD sí respalda la regla se indica.

## S-1 · Roles del sistema

- **Decisión:** exactamente tres roles: **Administrador** (operaciones administrativas y financieras, autorizaciones y administración de cuentas), **Coordinación** (eventos, propuestas, contratos, solicitudes y gestión de proveedores) y **Proveedor** (sus datos, sus asignaciones y su respuesta). El **Cliente no tiene cuenta**: lo gestiona Coordinación. Administración administra las cuentas.
- **Respaldo:** interesados del BRD (decisión de diseño para los nombres y las cuentas).
- **Implementación:** `ROLES = {administrador, coordinador, proveedor}`; el formulario y la API rechazan cualquier otro rol (422); ninguna ruta queda sin rol (toda ruta está en la matriz y se deniega por omisión).
- **Pruebas:** `tests/test_decisiones_s1_s9.py` (roles exactos, rechazo de roles ajenos y del Cliente, cuentas solo para Administración) y el recorrido de navegador.

## S-2 · Pagos, verificaciones, devoluciones, autorizaciones y cobranza

- **Decisión:** Administración tiene el control financiero: registrar y verificar pagos, consultar pagos y estados de cuenta, gestionar devoluciones, autorizar cambios, servicios adicionales y sustituciones, el seguimiento formal de cobranza y la regularización financiera. Coordinación **informa** al Cliente de importes, vencimientos y situación de pago, pero **no** registra ni verifica pagos ni ejecuta devoluciones.
- **Respaldo:** BRD (Administración registra y verifica pagos, autoriza y ejecuta devoluciones; Coordinación comunica el saldo al Cliente). La asignación de la cobranza (protocolo de cobro, vencimiento y regularización) a Administración es decisión del equipo: el BRD no nombra al actor.
- **Reglas que no cambian:** política de no reembolso, reglas del anticipo y del pago final, y la regla de excedentes **B-4, B-5 y X-14** del cierre de alcance (un excedente de un concepto distinto del anticipo se registra y verifica sin devolución ni aplicación a otra obligación).
- **Implementación:** permisos `pagos.registrar`, `pagos.cobranza`, `devoluciones.ejecutar`, `solicitudes.autorizar`, `solicitudes.importe_adicional` solo de Administración; Coordinación solo `pagos.consultar`.
- **Pruebas:** `test_decisiones_s1_s9.py` (11 operaciones financieras: 403 a Coordinación y Proveedor, permitidas a Administración; pago ≤ 0 rechazado; excedente sin devolución) y navegador.

## S-3 · Cancelación por falta de regularización

- **Decisión:** el procedimiento es: (1) el sistema identifica el vencimiento, (2) Administración comprueba la situación del pago y la ausencia de regularización, (3) **Coordinación** registra la cancelación y (4) el sistema conserva el motivo y el estado resultante.
- **Respaldo:** BN-005 y BN-008 (Administración revisa los pagos y comunica el resultado; «el Coordinador deberá registrar la cancelación»).
- **Implementación:** sin cambios de regla (ya exigía que Administración hubiera registrado «No regularizado»). **Endurecimiento:** con la autenticación activa el servidor registra **la cuenta de la sesión y su propio reloj** y ignora el `coordinador` y la `fecha` del cuerpo (que ahora son opcionales); así no se puede atribuir la cancelación a otra persona ni fecharla a conveniencia. No hay cancelación anticipada (422 sin la verificación de Administración), ni duplicada (la segunda llamada informa «ya estaba cancelado» sin nuevo hecho), ni con el evento ya iniciado.
- **Pruebas:** `test_decisiones_s1_s9.py` y navegador (vencimiento, protocolo de cobro, regularización y cancelación por UI).

## S-4 · Consulta de pagos por Coordinación

- **Decisión:** Coordinación consulta la información financiera necesaria: estado de cuenta, monto original de las obligaciones, pagos registrados y verificados, importes pendientes, vencimientos, estado de regularización y lo necesario para comunicar el saldo al Cliente. **No** registra, verifica, modifica importes, ejecuta devoluciones ni autoriza.
- **Respaldo:** BN-007 y la responsabilidad del Coordinador de comunicar el monto y la fecha límite (inferido; aprobado por el equipo).
- **Implementación:** permiso `pagos.consultar` de solo lectura; la interfaz no ofrece ninguna acción financiera a Coordinación y el servidor responde 403 a toda operación de escritura.
- **Pruebas:** `test_decisiones_s1_s9.py` (incluida la coincidencia de lo mostrado con PostgreSQL) y navegador.

## S-5 · Registro de respuestas del proveedor y su procedencia

- **Decisión:** la respuesta puede registrarla el **proveedor directamente** desde su cuenta o **Coordinación**, cuando el proveedor se la comunica por teléfono o mensaje. El sistema distingue claramente ambas y conserva: respuesta, **medio** de comunicación (solo si la registra Coordinación), fecha y hora, **cuenta** que la registró, y proveedor y servicio relacionados. Coordinación **nunca** suplanta la identidad ni la sesión del proveedor.
- **Respaldo:** el BRD indica que hoy la coordinación con proveedores es por WhatsApp, llamadas y correo; que Coordinación registre lo que el proveedor le comunicó es decisión del equipo.
- **Implementación:** **migración 0009** (aditiva) con columnas opcionales en `evento_servicio_contratado` (`respuesta_disponible`, `respuesta_origen`, `respuesta_medio`, `respuesta_registrada_por_id`, `respuesta_registrada_por_nombre`, `respuesta_fecha`) y tres CHECK (todo o nada; origen válido; el medio es obligatorio **solo** si el origen es «Coordinación»). El **origen y la cuenta salen de la sesión**, nunca del cuerpo (que rechaza campos desconocidos): un proveedor no puede declarar medio; Coordinación debe indicarlo (llamada telefónica, mensaje, correo u otro). Una respuesta ya dada no se reescribe, y una nueva asignación o un reemplazo borran la respuesta del proveedor anterior. Las vistas (Administración, Coordinación y el propio proveedor) muestran «respuesta directa del proveedor» o «capturada por Coordinación (medio: …)», quién la registró y cuándo; un proveedor solo ve lo suyo.
- **Pruebas:** `test_decisiones_s1_s9.py` (directa, capturada, medio obligatorio, suplantación, extra de campos, aislamiento, PostgreSQL y reinicio, CHECK) y navegador.

## S-6 · Integración de importes adicionales de sustituciones

- **Decisión:** Administración integra al saldo del contrato el importe adicional de una sustitución, en este orden: Coordinación registra la alternativa (proveedor, condiciones y costo adicional), el Cliente comunica su aceptación, Administración autoriza, Administración integra el importe autorizado y el sistema registra la operación y actualiza el estado de cuenta. No se integra antes de las autorizaciones, no se duplica, no se modifican pagos anteriores y solo se acepta el importe autorizado. Sin costo adicional **no** se crea una obligación artificial. Se conserva la trazabilidad sustitución → autorización → obligación.
- **Respaldo:** CA-052 (el costo adicional se incorpora al saldo general solo con la aprobación del Cliente y la autorización de Administración). Que lo ejecute Administración es decisión del equipo.
- **Implementación:** el servicio ya exigía las autorizaciones y el importe exacto. **Corregido:** una misma sustitución **podía integrarse dos veces** (la segunda llamada creaba otra obligación); ahora se rechaza («ya se integró»). Una sustitución sin costo adicional se rechaza con un motivo propio y no crea obligación. `GET /eventos/{id}/pagos` expone `origenId` de cada obligación adicional (trazabilidad). La interfaz propone el importe autorizado.
- **Pruebas:** `test_decisiones_s1_s9.py` (antes y después de las autorizaciones, Coordinación 403, importes distintos, una sola vez, sin costo, pagos anteriores intactos) y navegador.

## S-9 · Separación de funciones y mínimo privilegio

- **Decisión:** Administración **consulta** la información operativa necesaria (eventos, propuestas, contratos, solicitudes y estados financieros) y autoriza, pero **no crea ni gestiona** eventos, propuestas, contratos ni las solicitudes de Coordinación. Conserva las operaciones administrativas y financieras, la gestión de cuentas y las operaciones del catálogo ya aprobadas. **No existe superusuario** ni cuenta que evada los permisos; los permisos se imponen en el servidor, no solo ocultando botones.
- **Respaldo:** decisión de diseño (mínimo privilegio); el BRD le da a Administración la consulta de la información administrativa.
- **Implementación:** nueva consulta de solo lectura `GET /eventos/{id}/propuestas` (`eventos.consultar`: Administración y Coordinación; el Proveedor recibe 403), que también sustituye el registro local del navegador en la tarjeta «Propuestas» (los contratos ya figuraban en la información administrativa). La matriz se genera del código.
- **Pruebas:** `test_decisiones_s1_s9.py` (17 operaciones de Coordinación: 403 a Administración; consulta permitida; ningún rol tiene todos los permisos) y navegador.

## Funcionalidades afectadas
Registro de respuestas del proveedor; cancelación por falta de regularización; integración del importe de una sustitución; consulta de propuestas; estados de cuenta (`origenId`); tarjetas de servicios y de asignaciones; formularios de cancelación, respuesta e integración.

## Migraciones de esta etapa
0008 (condiciones del proveedor de un cambio, ADR-010) y 0009 (procedencia de la respuesta del proveedor). Ambas aditivas y reversibles; se aplicaron a la base manual tras un respaldo verificado.
