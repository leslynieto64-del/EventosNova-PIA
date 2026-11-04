# ADR-009: Decisiones aprobadas D-P2, S-7 y S-8 (candidatos de proveedor, ciclo del evento y permisos del catálogo)

- **Estado:** **Aprobadas por el equipo el 2026-11-01** (D-P2, S-7 y S-8). Son decisiones del equipo del proyecto; no proceden del BRD ni del cierre de alcance, que no las definen.
- **Fecha:** 2026-11-01
- **Relacionada con:** `../architecture/DECISIONES_PROVEEDORES.md`, `../SEGURIDAD_Y_PERMISOS.md`, ADR-008 (llegada de T)
- **Aprobadas después:** D-P1 y D-P3 (ver ADR-010, 2026-11-01). **Siguen pendientes de revisión por separado:** S-1, S-2, S-3, S-4, S-5, S-6 y S-9. **Aprobar S-8 no aprueba tarifas ni condiciones en el catálogo** (eso es D-P3) ni el catálogo como tal (D-P1): solo confirma quién edita, desactiva y reactiva.

## D-P2 · Candidatos para una asignación (no disponibilidad por fecha)

- **Decisión aprobada:** un proveedor es candidato para asignarlo a un servicio cuando está **registrado en el catálogo**, **activo** y **ofrece el servicio solicitado**.
- **Regla definitiva:** el sistema **no verifica** la disponibilidad real del proveedor en la fecha del evento. La disponibilidad específica se confirma después, con la **respuesta del proveedor** a la asignación (el servicio queda «Pendiente de confirmación del proveedor» hasta entonces). No habrá calendarios ni integraciones externas de disponibilidad.
- **Justificación:** el catálogo no tiene calendario y las fuentes no definen cómo calcular la disponibilidad; la confirmación humana del proveedor ya forma parte del flujo (CA-035, CA-036).
- **Consecuencias:** dos eventos de la misma fecha pueden asignar al mismo proveedor; la responsabilidad de detectar el conflicto es del proveedor al responder y de Coordinación. La interfaz y los mensajes hablan de «candidatos», nunca de disponibilidad verificada. `fecha_evento` llega al adaptador del catálogo y se ignora a propósito.
- **Funcionalidades afectadas:** `GET …/servicios/{id}/disponibilidad` (mensaje y diálogo «Candidatos para…»), `POST …/proveedor` (motivos de rechazo: no registrado, desactivado, no ofrece el servicio), diálogo «Asignar proveedor», `ConsultaDisponibilidadDesdeCatalogo`.
- **Pruebas necesarias:** `tests/test_decisiones_dp2_s7_s8.py` (candidato válido; inactivo; no ofrece el servicio; no registrado; confirmación posterior del proveedor; la respuesta no se presenta como verificada por fecha; mismo proveedor en dos eventos de la misma fecha; reactivado vuelve a ser candidato) y `tests/test_catalogo_proveedores.py`.

## S-7 · Inicio, finalización y cierre de solicitudes por falta de pago

- **Decisión aprobada:**
  - **Inicio:** el evento inicia **automáticamente** en su fecha y hora programadas (BN-010). Coordinación conserva «Registrar inicio del evento (respaldo)» solo como mecanismo excepcional cuando el proceso automático no actualizó el estado.
  - **Finalización:** la registra Coordinación.
  - **Cierre de solicitudes por falta de pago:** lo gestiona Coordinación cuando se comprueba que el pago no se regularizó dentro del plazo.
- **Regla definitiva:** el inicio manual **nunca** adelanta un evento cuya fecha y hora no han llegado (se rechaza con 422); si el evento ya inició (por el trabajador o manualmente) un segundo inicio se rechaza y no reescribe `fecha_inicio` ni genera operaciones nuevas. Los plazos y reglas existentes (24 h del cierre por falta de pago, etc.) no cambian.
- **Justificación:** BN-010 dice que el evento inicia automáticamente y que el Coordinador registra la finalización; el respaldo manual evita dejar un evento bloqueado si el trabajador estuvo caído.
- **Verificación del proceso automático:** `trabajador_outbox.ejecutar` llama en cada ciclo a `procesar_eventos_vencidos` (intervalo de 2 s en `docker-compose*.yml`). Usa el reloj de negocio `America/Mexico_City` sin zona (`application/reloj.py`; se comprobó dentro del contenedor del worker: UTC 07:08 → 01:08 locales). La consulta es `fecha_hora <= ahora` sobre eventos En gestión o En organización, por lo que **recupera los eventos cuya hora ya pasó** tras un reinicio o una caída. Es idempotente: un evento procesado deja de aparecer. México no usa horario de verano desde 2022.
- **Consecuencias:** sin cambios de reglas de negocio ni de permisos (`eventos.ciclo` y `solicitudes.gestionar` ya eran solo de Coordinación; Administración y Proveedor reciben 403). Cambia el texto del botón manual y su ayuda.
- **Funcionalidades afectadas:** `POST /eventos/{id}/inicio`, `POST /eventos/{id}/finalizacion`, `POST …/cierre-por-falta-de-pago` (cambio y servicio adicional), trabajador de despacho.
- **Pruebas necesarias:** `tests/test_decisiones_dp2_s7_s8.py` (inicio automático a la hora y no antes; recuperación tras reinicio con la hora ya pasada, incluido el proceso real del trabajador contra PostgreSQL; sin duplicados; inicio manual excepcional; inicio manual anticipado rechazado; finalización por Coordinación; cierre por falta de pago con plazo; 403 a Administración y Proveedor) y `tests/test_d3_llegada_de_t.py`.

## S-8 · Permisos del catálogo de proveedores

| Operación | Administración | Coordinación | Proveedor |
|---|---|---|---|
| Registrar proveedores | Sí | Sí | No |
| Consultar proveedores | Sí | Sí | Solo el suyo |
| Editar proveedores | Sí | **No** | No |
| Desactivar proveedores | Sí | **No** | No |
| Reactivar proveedores | Sí | **No** | No |

- **Regla definitiva:** el permiso `proveedores.editar` es solo de Administración y se comprueba **en el servidor** (403 `sin_permiso` aunque se llame directo a la API); la interfaz además oculta los botones a quien no los puede usar. Desactivar no borra el registro ni las asignaciones existentes (el proveedor desactivado sigue viendo y respondiendo lo que ya tiene), pero no recibe asignaciones nuevas; reactivarlo lo vuelve a hacer candidato.
- **Justificación:** las bajas y correcciones del catálogo afectan a todos los eventos; se concentran en Administración. Coordinación necesita registrar proveedores nuevos para poder asignar.
- **Consecuencias:** Coordinación ya no puede corregir un dato del proveedor; debe pedirlo a Administración. Se retira `proveedores.editar` de la matriz del coordinador.
- **Funcionalidades afectadas:** `POST /proveedores/{id}/edicion|desactivacion|activacion`, ficha de proveedor (botones Editar/Desactivar/Activar), matriz de permisos generada.
- **Pruebas necesarias:** `tests/test_decisiones_dp2_s7_s8.py`, `tests/test_seguridad.py`, `tests/test_catalogo_proveedores.py` y `scripts/probar_catalogo_proveedores_playwright.mjs` (Coordinación sin botones y con 403 del servidor; PostgreSQL sin cambios).
