# Matriz definitiva de permisos por rol (tres roles)

Derivada **del backend** (`src/application/seguridad.py`: `PERMISOS_POR_ROL`, `MATRIZ`, `autoriza`, aplicada por la dependencia `aplicar_seguridad` de `src/api/seguridad.py` a todas las rutas protegidas), no de los menús de la interfaz. Cada celda se calculó invocando `autoriza(rol, método, ruta)`. El Cliente no tiene cuenta (decisión S-1). El rol «propio» limita al proveedor a los recursos de su propia cuenta.

## Permisos por rol

| Rol | Cantidad | Permisos |
|---|---:|---|
| administrador | 12 | `devoluciones.ejecutar`, `eventos.consultar`, `eventos.revision_administrativa`, `pagos.cobranza`, `pagos.consultar`, `pagos.registrar`, `proveedores.consultar`, `proveedores.editar`, `proveedores.registrar`, `solicitudes.autorizar`, `solicitudes.importe_adicional`, `usuarios.administrar` |
| coordinador | 13 | `contratos.gestionar`, `eventos.cancelar`, `eventos.ciclo`, `eventos.consultar`, `eventos.registrar`, `pagos.consultar`, `propuestas.gestionar`, `proveedores.asignar`, `proveedores.consultar`, `proveedores.registrar`, `proveedores.responder`, `solicitudes.gestionar`, `solicitudes.registrar` |
| proveedor | 2 | `proveedores.propio`, `proveedores.responder` |

## Operaciones

| Grupo | Método | Ruta | Administrador | Coordinador | Proveedor |
|---|---|---|:-:|:-:|:-:|
| General | GET | `/` | pública | pública | pública |
| Seguridad | POST | `/auth/cambio-contrasena` | si | si | si | (cualquier sesión)
| Seguridad | POST | `/auth/cierre-sesion` | si | si | si | (cualquier sesión)
| Seguridad | POST | `/auth/inicio-sesion` | pública | pública | pública |
| Seguridad | GET | `/auth/yo` | si | si | si | (cualquier sesión)
| Propuestas y contratación (CU-01, CU-02) | POST | `/contratos/{contrato_id}/comunicacion-politica-no-reembolso` | no | si | no |
| Propuestas y contratación (CU-01, CU-02) | POST | `/contratos/{contrato_id}/confirmacion` | no | si | no |
| Propuestas y contratación (CU-01, CU-02) | POST | `/contratos/{contrato_id}/firma` | no | si | no |
| Propuestas y contratación (CU-01, CU-02) | POST | `/contratos/{contrato_id}/seguimiento-anticipo` | no | si | no |
| Consultas (solo lectura) | GET | `/devoluciones-pendientes` | si | si | no |
| Pagos y gestión financiera | POST | `/estados-cuenta/{estado_cuenta_id}/devoluciones/{devolucion_id}/ejecucion` | si | no | no |
| Pagos y gestión financiera | POST | `/estados-cuenta/{estado_cuenta_id}/pagos` | si | no | no |
| Pagos y gestión financiera | POST | `/estados-cuenta/{estado_cuenta_id}/pagos/{pago_id}/verificacion` | si | no | no |
| Pagos y gestión financiera | POST | `/estados-cuenta/{estado_cuenta_id}/protocolo-cobro` | si | no | no |
| Pagos y gestión financiera | POST | `/estados-cuenta/{estado_cuenta_id}/regularizacion` | si | no | no |
| Pagos y gestión financiera | POST | `/estados-cuenta/{estado_cuenta_id}/vencimiento-saldo-original` | si | no | no |
| Consultas (solo lectura) | GET | `/eventos` | si | si | no |
| Propuestas (CU-01) | POST | `/eventos` | no | si | no |
| Consultas (solo lectura) | GET | `/eventos/{evento_id}/administracion` | si | si | no |
| Ciclo de vida del Evento y proveedores | POST | `/eventos/{evento_id}/cancelacion` | no | si | no |
| Ciclo de vida del Evento y proveedores | POST | `/eventos/{evento_id}/cancelacion-por-falta-de-regularizacion` | no | si | no |
| Ciclo de vida del Evento y proveedores | POST | `/eventos/{evento_id}/finalizacion` | no | si | no |
| Ciclo de vida del Evento y proveedores | POST | `/eventos/{evento_id}/inicio` | no | si | no |
| Consultas (solo lectura) | GET | `/eventos/{evento_id}/pagos` | si | si | no |
| Consultas (solo lectura) | GET | `/eventos/{evento_id}/propuestas` | si | si | no |
| Propuestas (CU-01) | POST | `/eventos/{evento_id}/propuestas` | no | si | no |
| Ciclo de vida del Evento y proveedores | POST | `/eventos/{evento_id}/revision-administrativa` | si | no | no |
| Ciclo de vida del Evento y proveedores | GET | `/eventos/{evento_id}/servicios/{servicio_contratado_id}/disponibilidad` | no | si | no |
| Ciclo de vida del Evento y proveedores | POST | `/eventos/{evento_id}/servicios/{servicio_contratado_id}/proveedor` | no | si | no |
| Ciclo de vida del Evento y proveedores | POST | `/eventos/{evento_id}/servicios/{servicio_contratado_id}/respuesta-proveedor` | no | si | propio |
| Consultas (solo lectura) | GET | `/eventos/{evento_id}/solicitudes-pendientes` | si | si | no |
| General | GET | `/health` | pública | pública | pública |
| Consultas (solo lectura) | GET | `/mis-asignaciones` | no | no | propio |
| Consultas (solo lectura) | GET | `/pagos-pendientes` | si | si | no |
| Propuestas y contratación (CU-01, CU-02) | POST | `/propuestas/{propuesta_id}/aceptacion` | no | si | no |
| Propuestas y contratación (CU-01, CU-02) | POST | `/propuestas/{propuesta_id}/cierre-por-no-aceptacion` | no | si | no |
| Propuestas y contratación (CU-01, CU-02) | POST | `/propuestas/{propuesta_id}/contrato` | no | si | no |
| Propuestas y contratación (CU-01, CU-02) | POST | `/propuestas/{propuesta_id}/versiones` | no | si | no |
| Proveedores (catálogo) | GET | `/proveedores` | si | si | no |
| Proveedores (catálogo) | POST | `/proveedores` | si | si | no |
| Proveedores (catálogo) | GET | `/proveedores/{proveedor_id}` | si | si | propio |
| Proveedores (catálogo) | POST | `/proveedores/{proveedor_id}/activacion` | si | no | no |
| Proveedores (catálogo) | POST | `/proveedores/{proveedor_id}/desactivacion` | si | no | no |
| Proveedores (catálogo) | POST | `/proveedores/{proveedor_id}/edicion` | si | no | no |
| Consultas (solo lectura) | GET | `/proveedores/{proveedor_id}/eventos/{evento_id}` | si | si | propio |
| General | GET | `/ready` | pública | pública | pública |
| Consultas (solo lectura) | GET | `/servicios-pendientes-confirmacion` | si | si | no |
| Consultas (solo lectura) | GET | `/solicitudes` | si | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-cambio` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-cambio/{solicitud_id}/anexo` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-cambio/{solicitud_id}/autorizacion` | si | no | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-cambio/{solicitud_id}/cierre-por-falta-de-pago` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-cambio/{solicitud_id}/confirmacion` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-cambio/{solicitud_id}/decision-cliente` | no | si | no |
| Pagos y gestión financiera | POST | `/solicitudes-cambio/{solicitud_id}/solicitud-pago` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-cambio/{solicitud_id}/viabilidad` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-servicio-adicional` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-servicio-adicional/{solicitud_id}/anexo` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-servicio-adicional/{solicitud_id}/aprobacion-cliente` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-servicio-adicional/{solicitud_id}/autorizacion` | si | no | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-servicio-adicional/{solicitud_id}/cierre-por-falta-de-pago` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-servicio-adicional/{solicitud_id}/confirmacion` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-servicio-adicional/{solicitud_id}/decision-espera` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/solicitudes-servicio-adicional/{solicitud_id}/disponibilidad` | no | si | no |
| Pagos y gestión financiera | POST | `/solicitudes-servicio-adicional/{solicitud_id}/solicitud-pago` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/sustituciones` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/sustituciones/{sustitucion_id}/alternativa` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/sustituciones/{sustitucion_id}/anexo` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/sustituciones/{sustitucion_id}/autorizacion` | si | no | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/sustituciones/{sustitucion_id}/confirmacion` | no | si | no |
| Solicitudes: cambios, servicios adicionales y sustituciones | POST | `/sustituciones/{sustitucion_id}/decision-cliente` | no | si | no |
| Pagos y gestión financiera | POST | `/sustituciones/{sustitucion_id}/importe-adicional` | si | no | no |
| Seguridad | GET | `/usuarios` | si | no | no |
| Seguridad | POST | `/usuarios` | si | no | no |
| Seguridad | POST | `/usuarios/{usuario_id}/actualizacion` | si | no | no |
| Seguridad | POST | `/usuarios/{usuario_id}/contrasena` | si | no | no |
| Seguridad | POST | `/usuarios/{usuario_id}/estado` | si | no | no |

Operaciones protegidas permitidas por rol (incluye las de «cualquier sesión»): {'administrador': 35, 'coordinador': 53, 'proveedor': 7}.
