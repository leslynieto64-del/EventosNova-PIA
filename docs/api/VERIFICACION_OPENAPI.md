# Verificación del contrato OpenAPI de Eventos Nova

Fecha: 05/11/2026 (actualiza la verificación del 03/11/2026). Verificación documental (sin ejecutar la API) contra `docs/api/openapi.json` registrado en el commit `e3c98d9` (el commit `9c72bc7`, publicado después, solo añade una regla de `.gitattributes`).

| Comprobación | Resultado |
|---|---|
| Versión de OpenAPI | 3.1.0 |
| Título / versión de la API | Eventos Nova API / 0.1.0 |
| Operaciones en openapi.json | 77 |
| Operaciones públicas (sin requisito de seguridad) | 4: GET /, POST /auth/inicio-sesion, GET /health, GET /ready |
| Operaciones protegidas | 73 |
| openapi.yaml equivalente a openapi.json | Sí (mismo contenido al cargarlos) |
| openapi.json idéntico a docs/api/openapi.json del commit `e3c98d9` | Sí: es una copia byte a byte (SHA-256 `3b0ae6f959ce4ddc…`) |
| Cambios respecto del contrato del 03/11/2026 | Ninguno en contenido: los dos JSON cargan al mismo objeto; solo cambia el formato del archivo |
| Rutas | 73 (19 GET y 58 POST en 77 operaciones) |
| Operaciones del contrato presentes en el catálogo de operaciones | 77 de 77 |
| Operaciones del contrato presentes en la matriz de permisos | 77 de 77 |
| Esquemas de componentes | 48 |
| Esquema de seguridad | SesionCookie (apiKey en cookie `eventosnova_sesion`) |

El contrato es generado por FastAPI a partir del código y su igualdad con el archivo exportado la verifica la prueba `tests/test_openapi_exportada.py`. No se agregaron ni eliminaron operaciones.

**Observación:** todas las operaciones protegidas pueden responder 401 (sin sesión) y 403 (sin permiso, CSRF u Origin inválidos) por la dependencia global `aplicar_seguridad`, aunque algunas no declaran esos códigos en su sección `responses`. Además, cualquier operación puede responder 413 (cuerpo mayor de 256 KiB) y 409 (conflicto de concurrencia o de integridad). Esto se documenta en la Documentación de la API sin modificar el contrato generado.

**Producción:** con `EVENTOSNOVA_ENTORNO=produccion` las rutas `/docs`, `/redoc` y `/openapi.json` se ocultan salvo que se defina `EVENTOSNOVA_DOCS=1`.


**Bloque A (05/11/2026).** COR-05 dejó de devolver `condiciones` en `GET /mis-asignaciones` y `GET /proveedores/{proveedor_id}/eventos/{evento_id}` (vista del proveedor). La respuesta 200 de esas rutas se declara sin esquema (`schema: {}`), por lo que el contrato OpenAPI no cambió; el cambio está cubierto por las pruebas `test_h01_h02_proveedores` y por la verificación en Chrome del Bloque A.
