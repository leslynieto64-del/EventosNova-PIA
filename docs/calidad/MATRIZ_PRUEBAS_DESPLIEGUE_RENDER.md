# Matriz de pruebas del despliegue en Render

**Estado al 06/11/2026: ninguna prueba se ha ejecutado en Render (todas PENDIENTES).** El sistema no está desplegado. Esta matriz se completa después del *Apply* (ver
[`docs/manuales/GUIA_DESPLIEGUE_RENDER.md`](../manuales/GUIA_DESPLIEGUE_RENDER.md)). No marque una prueba como aprobada sin guardar su evidencia; una prueba local no sustituye a la prueba en Render.

- `<api>` es la URL pública real de `eventosnova-api` (se anota aquí solo después de comprobarla).
- Cuentas: administrador (creado con `scripts/crear_administrador.py`), coordinador y proveedor (creados por la siembra de demostración o desde `/app/`). Nunca anote contraseñas en la evidencia.
- Evidencia: capturas de pantalla o texto copiado **sin** contraseñas, cookies, tokens ni la cadena `DATABASE_URL`; guárdela en `docs/calidad/evidencias/07_DESPLIEGUE/` (carpeta que ya existe para este fin).
- Resultado: `PENDIENTE` → `APROBADA` / `FALLIDA` (con fecha, quién la ejecutó y enlace a la evidencia).

## A. Infraestructura y seguridad de transporte

| ID | Operación | Pasos | Resultado esperado | Evidencia | Criterio de aprobación | Estado |
|---|---|---|---|---|---|---|
| DEP-01 | Recursos creados | Tras el Apply, abrir el Dashboard y listar los recursos del Blueprint | Existen `eventosnova-db`, `eventosnova-api`, `eventosnova-worker`, los tres en Ohio y con los planes de `render.yaml` | Captura del Dashboard (región y plan de cada recurso) | Tres recursos, todos en Ohio, ninguno en plan gratuito | PENDIENTE |
| DEP-02 | API disponible | `GET <api>/health` | 200 con `{"estado":"ok","aplicacion":"Eventos Nova",...}` | Respuesta copiada | Código 200 y cuerpo esperado | PENDIENTE |
| DEP-03 | Base de datos conectada | `GET <api>/ready` | 200 con `persistencia: postgresql` y `base_de_datos: ok` | Respuesta copiada | Código 200 y ambos valores | PENDIENTE |
| DEP-04 | Migraciones correctas | Shell de la API: `python -m alembic current`; revisar el log del último despliegue | `0009 (head)`; el pre-despliegue terminó sin errores | Texto del comando y del log | Revisión `0009` y despliegue exitoso | PENDIENTE |
| DEP-05 | Worker activo | Dashboard → worker → *Logs* | Proceso en ejecución, sin trazas de error repetidas | Captura del estado y de los últimos logs | Estado activo durante 10 minutos sin reinicios | PENDIENTE |
| DEP-06 | Base sin acceso externo | Dashboard → base → acceso externo; intentar conectar desde un equipo externo con la URL externa (si existe) | Ninguna dirección permitida; la conexión externa es rechazada | Captura de la configuración y del rechazo | Sin acceso externo | PENDIENTE |
| DEP-07 | HTTPS y cabeceras | `GET <api>/health` por HTTPS; revisar cabeceras | Certificado válido; `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Cache-Control: no-store` | Captura de las cabeceras | Todas presentes | PENDIENTE |
| DEP-08 | Swagger oculto por omisión | `GET <api>/docs`, `/redoc`, `/openapi.json` sin `EVENTOSNOVA_DOCS` | 404 en las tres | Respuestas copiadas | Tres 404 | PENDIENTE |
| DEP-09 | Swagger habilitado y vuelto a deshabilitar | Definir `EVENTOSNOVA_DOCS=1`, esperar el despliegue, consultar `/docs` y `/openapi.json`; eliminar la variable y repetir | Con la variable: 200 (77 operaciones). Sin ella: 404 | Capturas de ambas fases | Ambos estados correctos | PENDIENTE |

## B. Autenticación y seguridad de sesión

| ID | Operación | Pasos | Resultado esperado | Evidencia | Criterio de aprobación | Estado |
|---|---|---|---|---|---|---|
| DEP-10 | Inicio de sesión del administrador | En `<api>/app/` iniciar sesión con el administrador | Acceso al panel de administración; opciones propias del rol | Captura del panel (sin la contraseña) | Entra y ve el panel | PENDIENTE |
| DEP-11 | Inicio de sesión del coordinador | Igual, con la cuenta de coordinador | Acceso al panel de coordinación | Captura | Entra y ve el panel | PENDIENTE |
| DEP-12 | Inicio de sesión del proveedor | Igual, con la cuenta de proveedor | Acceso a «Mis asignaciones» | Captura | Entra y ve sus asignaciones | PENDIENTE |
| DEP-13 | Cookie, CSRF y Origin | Con las herramientas del navegador revisar la cookie de sesión; intentar una operación de escritura sin token CSRF y con un `Origin` ajeno (en un entorno de pruebas del equipo) | Cookie `Secure`, `HttpOnly`, `SameSite=Strict`; sin token CSRF u Origin ajeno: 403 | Captura de la cookie y de los 403 | Atributos presentes y 403 en ambos casos | PENDIENTE |
| DEP-14 | Cuenta inválida o desactivada | Intentar entrar con una contraseña incorrecta una vez; con una cuenta desactivada (`[DEMO]`) | Rechazo con mensaje genérico, sin revelar si el correo existe. **No repita intentos**: tras 5 intentos fallidos la cuenta se bloquea temporalmente (15 minutos) | Captura del mensaje | Rechazo sin detalles | PENDIENTE |

## C. Flujos de negocio (con la interfaz o la API)

El Cliente no tiene cuenta: «registro de clientes» se refiere al identificador `cliente_id` con el que el Coordinador registra un evento.

| ID | Operación | Pasos | Resultado esperado | Evidencia | Criterio de aprobación | Estado |
|---|---|---|---|---|---|---|
| DEP-15 | Registro de un evento y de su cliente | Coordinador: registrar un evento (`cliente_id`, tipo, fecha, lugar, invitados, servicios) | Evento «En gestión» con su identificador | Captura del evento | Se crea y aparece en la consulta de eventos | PENDIENTE |
| DEP-16 | Gestión de proveedores | Coordinador o administrador: registrar, buscar, editar, desactivar y reactivar un proveedor `[DEMO]` | Cada acción se refleja en el catálogo; el nombre repetido se rechaza | Capturas del catálogo | Todas las acciones correctas | PENDIENTE |
| DEP-17 | Propuesta: elaboración y aceptación | Coordinador: crear la propuesta del evento y aceptarla | Propuesta «En revisión del Cliente» y luego «Aceptada» | Capturas de ambos estados | Estados correctos | PENDIENTE |
| DEP-18 | Contrato y política de no reembolso | Coordinador: preparar el contrato, comunicar la política y firmarlo | Contrato «Firmado» | Captura del contrato y de su estado | Contrato firmado | PENDIENTE |
| DEP-19 | Anticipo | Administrador: registrar y verificar el anticipo (30 %) | Pago «Verificado»; contrato «Contratación confirmada»; evento «En organización» | Capturas de pagos y del evento | Estados correctos | PENDIENTE |
| DEP-20 | Consulta de pagos | Administrador y coordinador: consultar el estado de pagos y los pagos pendientes | Anticipo «Liquidada»; saldo pendiente visible | Captura | Importes coherentes | PENDIENTE |
| DEP-21 | Asignación de un servicio | Coordinador: asignar el proveedor de Banquete al servicio contratado | Servicio «Pendiente de confirmación del proveedor» | Captura | Estado correcto | PENDIENTE |
| DEP-22 | Asignación visible y respuesta del proveedor | Proveedor: consultar «Mis asignaciones» y responder que está disponible | La asignación aparece; tras responder: «Confirmado por el proveedor» | Capturas antes y después | Estados correctos; no puede responder por otro proveedor | PENDIENTE |
| DEP-23 | Cancelación con no reembolso | Coordinador: cancelar un evento con contratación confirmada; administrador: revisión administrativa | Evento «Cancelado»; revisión con constancia de no reembolso (pagos realizados y saldo pendiente) | Capturas | Estados y constancia correctos | PENDIENTE |
| DEP-24 | Validaciones de reglas de negocio | Probar al menos: cancelar sin contratación confirmada; registrar un evento con datos incompletos; proveedor no registrado en una asignación | Rechazos con mensaje de negocio (HTTP 422) y sin cambios en los datos | Respuestas copiadas | Rechazos esperados | PENDIENTE |
| DEP-25 | Restricciones por rol | Con cada cuenta intentar lo que no le corresponde (p. ej. administrador registrando un evento; coordinador creando cuentas; proveedor listando cuentas) | 403 en todos los casos | Respuestas copiadas | Todos 403 | PENDIENTE |

## D. Worker, persistencia y registros

| ID | Operación | Pasos | Resultado esperado | Evidencia | Criterio de aprobación | Estado |
|---|---|---|---|---|---|---|
| DEP-26 | Procesamiento del Outbox | Tras DEP-19, revisar los logs del worker y la API | Eventos de dominio procesados sin errores (el despacho en línea de la API y el worker usan reclamo con bloqueo) | Fragmento de los logs | Sin errores y sin eventos pendientes | PENDIENTE |
| DEP-27 | Persistencia tras reiniciar la API | Crear un dato, reiniciar la API, volver a entrar | El dato sigue; el inicio de sesión funciona | Capturas antes y después | Dato presente | PENDIENTE |
| DEP-28 | Persistencia tras reiniciar el worker | Reiniciar el worker y revisar | Vuelve a estar activo sin pérdida de datos | Captura de logs | Activo y datos intactos | PENDIENTE |
| DEP-29 | Logs sin secretos ni errores críticos | Revisar los logs de los tres recursos tras las pruebas | Sin contraseñas, tokens ni `DATABASE_URL`; sin errores críticos sin resolver | Revisión firmada de los logs | Ninguno encontrado | PENDIENTE |

## E. Datos de demostración (después de DEP-01 a DEP-13)

| ID | Operación | Pasos | Resultado esperado | Evidencia | Criterio de aprobación | Estado |
|---|---|---|---|---|---|---|
| DEP-30 | Simulación | `sembrar_datos_demo.py --simular` contra `<api>` | Muestra el plan; solo consulta `/health` y `/ready`; no inicia sesión | Salida (sin secretos) | Código 0 | PENDIENTE |
| DEP-31 | Verificación de estado | `--verificar-estado` con la frase `VERIFICAR ESTADO EN <host>` | Informa qué existe y qué falta; el único POST es el login | Salida | Código 0 y sin escrituras de negocio | PENDIENTE |
| DEP-32 | Siembra | `--aplicar` con la frase `SEMBRAR DEMO EN <host>` | 2 cuentas, 6 proveedores y 3 eventos `[DEMO]` con sus estados; la asignación de Banquete queda pendiente | Salida y capturas | Código 0 y estados esperados | PENDIENTE |
| DEP-33 | Segunda ejecución | Repetir `--aplicar` | 0 creados; sin duplicados | Salida | 0 creados | PENDIENTE |

## Comprobaciones ya realizadas en local (no sustituyen a las anteriores)

Imagen Docker construida desde el `Dockerfile`, API en modo producción, worker, administrador por el script, proxy TLS simulado, Swagger y reinicio, contra una base PostgreSQL
desechable: ver la sección 1 de la guía de despliegue. Las pruebas automáticas `tests/test_render_blueprint.py` (invariantes de `render.yaml`) y `tests/test_sembrar_datos_demo.py`
(siembra) se ejecutan en CI.
