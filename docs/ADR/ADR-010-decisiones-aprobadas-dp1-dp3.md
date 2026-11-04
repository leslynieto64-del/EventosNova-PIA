# ADR-010: Decisiones aprobadas D-P1 (catálogo de proveedores) y D-P3 (costos y condiciones por operación)

- **Estado:** **Aprobadas por el equipo el 2026-11-01** (alternativa A en ambas). Son decisiones del equipo del proyecto. El cierre de alcance aprobado no menciona proveedores; el respaldo documental está en el BRD (ver cotejo abajo).
- **Fecha:** 2026-11-01
- **Relacionada con:** ADR-009 (D-P2, S-7 y S-8, ya aprobadas), `../architecture/DECISIONES_PROVEEDORES.md`, `../SEGURIDAD_Y_PERMISOS.md`
- **Estado:** D-P1 ya estaba implementada. **D-P3 se implementó el 01/11/2026** tras las tres decisiones de detalle de la sección «Implementación». S-5 y S-6 se aprobaron e implementaron después, el mismo día (ADR-011).
- **Aprobadas después (ADR-011):** S-1, S-2, S-3, S-4, S-5, S-6 y S-9.

## D-P1 · Catálogo de proveedores

- **Decisión aprobada:** el sistema conserva el catálogo con estas funciones: registrar proveedores, consultar el listado y las fichas, editar, desactivar y reactivar.
- **Regla definitiva:**
  - **No existe eliminación definitiva** de proveedores (no hay, ni habrá, operación de borrado).
  - **Desactivar** conserva todos sus datos y el historial de asignaciones; el proveedor desactivado deja de ser candidato para asignaciones nuevas (D-P2) pero conserva y puede responder lo que ya tiene asignado.
  - **No se añaden tarifas ni condiciones permanentes al catálogo.** El proveedor sigue siendo: nombre (único), servicios que ofrece, contacto y estado.
  - **Permisos (S-8):** Administración registra, consulta, edita, desactiva y reactiva; Coordinación registra y consulta; Proveedor solo consulta sus propios datos y asignaciones y responde sus servicios.
- **Justificación:** el BRD pide conocer los proveedores asignados (BN-004) y que el Coordinador coordine proveedores; el catálogo mínimo lo permite, y la edición y la desactivación evitan datos erróneos sin perder historial.
- **Consecuencias:** corregir o dar de baja un proveedor es tarea de Administración; Coordinación debe pedírselo. Un proveedor nunca desaparece: solo deja de proponerse.
- **Funcionalidades afectadas:** `POST /proveedores`, `GET /proveedores`, `GET /proveedores/{id}`, `POST /proveedores/{id}/edicion|desactivacion|activacion`, pantalla Proveedores y ficha, columna `proveedor.activo` (migración 0007). **Sin cambios de código necesarios**: ya está implementado.
- **Pruebas necesarias:** las existentes (`test_catalogo_proveedores.py`, `test_decisiones_dp2_s7_s8.py`, `probar_catalogo_proveedores_playwright.mjs`) y una prueba que fije que **la API no expone ninguna operación de borrado de proveedores** (pendiente de añadir con la implementación conjunta).

## D-P3 · Costos y condiciones de proveedores: captura manual por operación

- **Decisión aprobada:** el costo y las condiciones de un proveedor se **capturan manualmente para cada operación**, según la cotización que el proveedor comunique. No hay tarifas permanentes en el catálogo ni fuentes externas de precios.
- **Procedimiento aprobado:**
  1. Coordinación recibe la información del proveedor.
  2. Coordinación registra manualmente el costo y las condiciones de la solicitud.
  3. Administración revisa y autoriza el importe cuando corresponda.
  4. El sistema conserva los datos registrados para su seguimiento.
- **Alcance:** cambios, servicios adicionales y sustituciones de proveedor, **respetando las reglas particulares de cada flujo** (plazos, aprobación del Cliente, autorización de Administración, anexo, pago).
- **Regla de negocio que se mantiene (BN-004):** Eventos Nova **no cobra por gestionar servicios adicionales**; el importe del servicio adicional es únicamente el costo establecido por el proveedor (`SolicitudServicioAdicional.importe_a_cobrar`, H-06).
- **Justificación:** el BRD supone que los proveedores informan su disponibilidad, costos y condiciones al Coordinador y que este los registra (SE-004, BN-003, BN-004); el equipo no cuenta con tarifas aprobadas ni con integraciones.
- **Consecuencias:** el costo es tan fiable como la cotización que se capture; no hay validación contra una tarifa. En servicios adicionales la «consulta de disponibilidad» deja de depender de una fuente y pasa a ser un registro de lo que el proveedor respondió (coherente con D-P2: la disponibilidad la confirma el proveedor).
- **Funcionalidades afectadas (ver informe de impacto técnico):** evaluación de disponibilidad del servicio adicional (`POST /solicitudes-servicio-adicional/{id}/disponibilidad`), visibilidad de costo y condiciones para Administración al autorizar (cambio, servicio adicional y sustitución), formularios de la interfaz, pruebas que usan la fuente simulada, guía de pruebas manuales.
- **Pruebas necesarias:** captura manual con costo y condiciones obligatorios (CA-075) en servicios adicionales; costo > 0; proveedor del catálogo, activo y que ofrece el servicio; Coordinación captura y Administración autoriza; Administración y Proveedor no capturan; datos conservados tras recargar y reiniciar; el importe a pagar es exactamente el costo capturado y sin cargo propio de Eventos Nova; plazos y rechazos existentes sin cambios.

## Relación con las decisiones ya aprobadas

| Decisión | Relación |
|---|---|
| **D-P2** (candidato = registrado + activo + ofrece el servicio; la disponibilidad la confirma el proveedor) | D-P1 define el catálogo del que salen los candidatos. D-P3 completa el flujo: el costo y las condiciones también los comunica el proveedor y los registra Coordinación; ninguno de los dos se calcula en el sistema. |
| **S-8** (quién registra, edita, desactiva y reactiva) | D-P1 adopta ese reparto sin cambios. |
| **S-7** (ciclo del evento y cierres por falta de pago) | Sin conflicto: D-P3 no cambia plazos ni cierres. |
| **S-6** (pendiente: quién integra el importe adicional de una sustitución) | D-P3 dice que Administración «revisa y autoriza el importe»; eso ya lo cubre `solicitudes.autorizar`. Quién *integra* el importe al saldo sigue pendiente en S-6 y no se da por aprobado aquí. |

## Cotejo con el BRD y las reglas existentes

No se encontró contradicción: BN-004 y SE-004 ya piden determinar el costo y las condiciones con el proveedor y excluyen un cargo propio; BN-003 y SE-003 registran el costo adicional del proveedor por separado del cargo por cambio tardío; SE-001 prevé que la alternativa cambie costos y condiciones; la autorización obligatoria de Administración (BN-003/BN-004) no cambia. Aplicar D-P3 no modifica ninguna regla de negocio, plazo ni permiso.

## Implementación de D-P3 (01/11/2026)

**Decisiones de detalle aprobadas por el equipo**
1. **Fuente simulada o de archivo:** se conserva **solo para pruebas automatizadas**; no puede activarse por entorno (la aplicación se niega a arrancar si `EVENTOSNOVA_DISPONIBILIDAD_ARCHIVO` está definida) y no proporciona candidatos, disponibilidad ni costos reales. Sus métodos de servicio quedaron rotulados de uso exclusivo de pruebas y la API ya no los invoca.
2. **Cambios:** campo **opcional** `condiciones_proveedor` (texto, máximo 1000 caracteres) junto al costo adicional; puede quedar vacío. Se guarda en PostgreSQL (`solicitud_cambio.condiciones_proveedor`, **migración 0008**, aditiva y reversible) y Administración lo ve antes de autorizar.
3. **Servicios adicionales:** el costo registrado es **obligatorio y estrictamente mayor que cero**; el servidor rechaza cero, negativos y ausencia, también por llamada directa a la API. Se mantiene BN-004: Eventos Nova no cobra por gestionarlo; el importe de la solicitud de pago debe ser exactamente ese costo.

**Qué cambió**
- `POST /solicitudes-servicio-adicional/{id}/disponibilidad` recibe `{disponible, proveedor_id?, costo?, condiciones?}` (captura manual) en lugar de consultar una fuente. Con `disponible = true` son obligatorios proveedor del catálogo, costo > 0 y condiciones; con `false` no se envía nada más y la búsqueda continúa (CA-076).
- `POST /sustituciones/{id}/alternativa` recibe `proveedor_id` (obligatorio), condiciones y costo adicional opcional; el proveedor ya no sale de una fuente.
- `POST /solicitudes-cambio/{id}/viabilidad` acepta `condiciones_proveedor` opcional.
- **Validación de proveedores** (servicio adicional y sustitución): registrado en el catálogo, **activo** y que **ofrece el servicio**; en una sustitución, además, distinto del proveedor original.
- **Visibilidad para Administración:** `GET /solicitudes` incluye `datosProveedor` (`proveedorId`, `costo`, `condiciones`) de cada solicitud; la interfaz lo muestra en la columna «Proveedor, costo y condiciones» y en el diálogo de autorización («Registrado por Coordinación: …»).
- **Interfaz:** formulario de captura con lista de proveedores del catálogo (activos que ofrecen el servicio) para el servicio adicional y la sustitución; campo opcional de condiciones en la evaluación de viabilidad del cambio.
- **Permisos:** sin cambios. Captura Coordinación (`solicitudes.gestionar`); autoriza Administración (`solicitudes.autorizar`); Administración y Proveedor reciben 403 al capturar. En el momento de implementar D-P3 **no se amplió** ningún permiso para responder en nombre del proveedor (S-5) ni se dio por resuelta la integración del importe adicional (S-6); ambas se aprobaron después en ADR-011.

**Pruebas:** `tests/test_decisiones_dp1_dp3.py` (memoria y PostgreSQL), `tests/test_api_operaciones.py`, `tests/test_integraciones_simuladas.py`, `tests/test_catalogo_proveedores.py`, `tests/test_migraciones_ciclo.py`, `tests/test_esquema_postgresql*.py` y `scripts/probar_costos_condiciones_playwright.mjs`.
