# Auditoría de integraciones externas (fase final, Etapa 6)

Ninguna integración externa es real. Este documento clasifica cada una, indica su base documental y qué haría falta para volverla real. No se inventaron credenciales ni se presentó ninguna simulación como si fuera una integración.

| Integración | Puerto (`application/puertos.py`) | Adaptador actual | Clasificación | Base documental | Para hacerla real |
|---|---|---|---|---|---|
| Verificación de pagos | `IVerificadorPagos` | `VerificadorPagosSimulado` (verdadero si hay comprobante) | **Simulación intencional** | BRD: «Realizar los pagos por parte del Cliente» está fuera del alcance; glosario: «Los pagos se efectúan fuera del sistema y Administración los registra manualmente» | Especificación de un banco o pasarela, credenciales y formato de comprobante. Hoy la verificación es un acto de Administración, que el sistema solo registra |
| Ejecución de devoluciones | `IEjecutorDevoluciones` | `EjecutorDevolucionesSimulado` (comprobante `COMP-<id>`, idempotente por referencia) | **Implementación parcial** | CA-098: Administración efectúa la devolución y el sistema registra concepto, importe, motivo, fecha y comprobante | **Hecho en esta etapa:** `POST …/devoluciones/{id}/ejecucion` acepta el `comprobante` que entrega Administración y lo registra; sin él se usa el ejecutor simulado. Una transferencia real requeriría una pasarela especificada |
| Notificaciones | `INotificadorParticipantes` | `NotificadorEnMemoria` (lista de avisos en memoria del proceso) | **Simulación intencional** | BRD: hoy se usa WhatsApp, llamadas y correo; el sistema debe registrar y comunicar (US-027, CA-087) pero no define canal ni proveedor | Elegir canal (correo, mensajería), obtener credenciales y plantillas. Los avisos no persisten: se pierden al reiniciar el proceso |
| Disponibilidad de proveedores | `IConsultaDisponibilidadProveedor` | **Catálogo real** de proveedores (`ConsultaDisponibilidadDesdeCatalogo`); la fuente simulada o de archivo solo existe para pruebas automatizadas | **Decisiones D-P2 y D-P3 (aprobadas 01/11/2026)** | US-013, US-014, CA-029 a CA-031: es candidato el proveedor registrado, activo y que ofrece el servicio; la disponibilidad en la fecha la confirma el proveedor al responder; el costo y las condiciones se capturan a mano por operación | Nada: no habrá calendarios ni integraciones externas de disponibilidad ni de precios |

## Fuente simulada de disponibilidad: solo para pruebas automatizadas

`ConsultaDisponibilidadSimulada` y `ConsultaDisponibilidadDesdeArchivo` (lee un JSON `{servicio: [{proveedor_id, disponible, costo?, condiciones?}]}`, con `src/infrastructure/datos_demo/disponibilidad_demo.json` rotulado como datos de demostración) **existen exclusivamente para las pruebas automatizadas**, que las inyectan en código (`construir(disponibilidad=...)`). **No se activan por entorno**: desde el 01/11/2026 (D-P3) la aplicación se niega a arrancar si `EVENTOSNOVA_DISPONIBILIDAD_ARCHIVO` está definida, para que nadie la deje activa por accidente, y la variable se retiró de `docker-compose*.yml` y de `.env.example`. No proporcionan candidatos, disponibilidad ni costos reales.

En operación: los **candidatos** de una asignación salen del catálogo registrado en PostgreSQL (registrados, activos y que ofrecen el servicio; D-P2) y el **costo y las condiciones** de cambios, servicios adicionales y sustituciones los captura Coordinación a mano según la cotización del proveedor (D-P3; `POST …/disponibilidad` de un servicio adicional, `POST …/viabilidad` de un cambio y `POST …/alternativa` de una sustitución). Ver `docs/ADR/ADR-010-decisiones-aprobadas-dp1-dp3.md`.

## Pruebas

`tests/test_integraciones_simuladas.py` (13): los adaptadores son simulados, la verificación solo exige comprobante, el ejecutor es idempotente, el notificador solo registra en memoria, la simulación configurable se carga y se rotula, asigna proveedores cuando hay datos y no asigna ninguno cuando no los hay, y la devolución registra el comprobante de Administración (o usa el simulado).

## Pendientes externos

Elegir la plataforma y credenciales de notificación; decidir si habrá una pasarela de pagos o si Administración seguirá registrando manualmente (lo que indican BRD y glosario); proveer una fuente real de disponibilidad de proveedores.
