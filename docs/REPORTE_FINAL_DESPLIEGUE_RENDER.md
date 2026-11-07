# Reporte de despliegue en Render — Eventos Nova (2026-11-06)

Estado: **desplegado, migrado, con datos de demostración cargados, con la corrección visual publicada y con Swagger UI accesible en producción** (`main` = `1dfcfdd`; PR #6, #7 y #8 fusionadas; cobertura de sentencias 98,12 %). Quedan pendientes las comprobaciones que dependen del Dashboard, del Shell o de una sesión iniciada, y un paso manual de la demostración (secciones 11 y 12).

Origen de cada dato: **[E]** ejecutado y observado por mí; **[U]** informado por la persona usuaria tras ejecutarlo en su terminal o en el Shell de Render (no lo observé directamente); **[P]** archivo de progreso local, que escribió el propio script; **[G]** consultado en GitHub (API de `gh`) durante esta actualización.

Ámbito de cada prueba (se distingue en las secciones 13 a 15): **PRODUCCIÓN** (contra `https://eventosnova-api.onrender.com`), **LOCAL** (equipo del desarrollador, servidor y base aislados) y **AUTOMATIZADA** (suite de pruebas y GitHub Actions).

## 1. Despliegue
| Elemento | Resultado |
|---|---|
| Repositorio | `main` = `origin/main` = `1dfcfdd` (fusión de la PR #8), sin cambios en archivos rastreados [E][G]. En el primer despliegue era `ea59c80b61a8cf3bc863490156d5d89bb70ef6e3` |
| Servicios | `eventosnova-api`, `eventosnova-worker`, `eventosnova-db` creados, API en `Live` [U] |
| Commit desplegado | Primer despliegue: `ea59c80` [U]. Actual: `1dfcfdd` en `eventosnova-api` y `eventosnova-worker`, según los registros de despliegue que Render crea en GitHub (estado `success`, 2026-11-06 18:16:19 UTC y 18:15:58 UTC) [G]. El Dashboard de Render no se consultó |
| Worker | El registro guardado muestra que esperó el esquema y a los 6 s dio la base por lista, requiriendo `0009` [E, archivo de log] |

## 2. PostgreSQL y Alembic
| Comprobación | Resultado |
|---|---|
| `alembic current` | `0009 (head)`, una sola cabeza [U, Shell de Render] |
| Base y usuario | base `eventosnova`, usuario `eventosnova`, sin superusuario [U] |
| Registro de la base | TLS 1.3, sin fallos de autenticación en la ventana guardada [E, archivo de log] |

## 3. Seguridad
- GET públicos [E] en el primer despliegue: `/docs`, `/redoc` y `/openapi.json` daban 404. **Actualizado:** con `EVENTOSNOVA_DOCS=1` definido en el servicio, los tres responden 200 (sección 15). La variable se define a mano en el Dashboard: `render.yaml` no la contiene y una prueba del repositorio impide añadirla.
- Cabeceras [E, auditoría previa]: HSTS, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: same-origin`, `Cache-Control: no-store`.
- Cuenta de la API sin privilegios de superusuario [U].
- El archivo de progreso no contiene contraseñas, cookies ni tokens [E]: lo revisé buscando esas palabras y solo guarda identificadores de demostración, estados y marcas de tiempo.
- No se imprimió ninguna credencial ni cadena de conexión.

## 4. Administrador
El administrador inicial (`leslynieto64@gmail.com`) ya existía [U]. La siembra lo encontró (1 «encontrado»). No se creó otro. La contraseña no consta en ningún archivo.

## 5. Siembra de demostración (`scripts/sembrar_datos_demo.py --aplicar`)
- Simulación previa [E]: código 0, solo GET de `/health` y `/ready`.
- Resultado final [U y P]: **27 creados, 1 encontrado, 1 omitido intencionalmente (respuesta del proveedor), 0 pendientes**. El archivo de progreso coincide: `creados 27, encontrados 1, omitidos 1, pendientes 0`, del 2026-11-06 entre 02:48:35 y 02:49:34 (hora de negocio).
- Lo creado, con identificadores en el progreso [P]:
  - cuenta de coordinador y cuenta de proveedor (Banquete);
  - 6 proveedores [DEMO];
  - eventos E1, E2 y E3 (CL-DEMO-01 a 03) y sus 3 propuestas;
  - 2 aceptaciones y 2 contratos (E2 y E3), con política de no reembolso comunicada y firma en cada uno;
  - 2 anticipos de 3,000.00 MXN;
  - 1 asignación de Banquete para E2;
  - la cancelación de E3 y su revisión administrativa.
- Revisión de E3 [P]: pagos realizados 3,000.00 y saldo pendiente 7,000.00.
- No se ejecutaron INSERT directos, ni se importaron CSV, ni se repitió `--aplicar`.
- Un primer intento de `--aplicar` desde el Shell de Render se detuvo con código 2 porque allí no existe Git ni `.gitignore`. No creó datos [U].

## 6. Paso manual pendiente para la demostración
La asignación de Banquete del evento **CL-DEMO-02** queda **pendiente de confirmación del proveedor**, a propósito. En la presentación: inicie sesión con la cuenta de proveedor, abra la asignación y responda. La respuesta se despacha en línea y el Worker procesa el resto del Outbox.

## 7. Pendiente de verificar (no lo hice)
| Elemento | Motivo |
|---|---|
| Inicio de sesión de los tres roles | Necesita contraseñas; el script no la verifica sin `--verificar-estado` |
| Estado de eventos y asignaciones por GET | Necesita sesión |
| Estado del Outbox (`PENDIENTE`/`REVISION`) y registros recientes del Worker | Necesita Shell o Dashboard |
| Registros nuevos de API, Worker y PostgreSQL tras la siembra | No tengo acceso a Render; los archivos guardados son anteriores |
| `ipAllowList` de la base aplicado | Se ve en el Dashboard |

Sugerencia: ejecutar `--verificar-estado --incluir-proveedor` (comprueba sesiones y consulta de los datos) y la consulta de solo lectura `SELECT estado, count(*) FROM outbox_evento GROUP BY 1;` en el Shell. Debe mostrar solo `PROCESADO`.

## 8. Comprobaciones al cierre [E]
`GET /health` → 200 (`estado: ok`); `GET /ready` → 200 (`persistencia: postgresql`, `base_de_datos: ok`); `/docs` y `/openapi.json` → 404. *(Foto del cierre de la siembra; el estado vigente, con Swagger habilitado, está en la sección 15.)*

## 10. Corrección visual de «Mis datos» (proveedor) — publicada
- **Problema:** en `/app/#/proveedor` el correo de Contacto se encimaba con Identificador [U, captura en producción].
- **Causa:** `.datos` usaba `minmax(150px, 1fr)`; una celda de rejilla no baja de su texto más largo sin cortes.
- **Cambio:** solo `src/web/css/app.css` (3 líneas añadidas, 2 reemplazadas): `min-width: 0`, `overflow-wrap: anywhere` y mínimo de columna `min(100%, 190px)`. Sin cambios de JavaScript, backend, permisos ni datos.
- **Usos de `.datos` revisados:** Mis datos, Datos del proveedor, Resumen económico y obligaciones del detalle de evento. El cambio solo afecta al ajuste de texto y al número de columnas en anchos intermedios.
- **Pruebas [E]:** 44 pruebas de interfaz correctas (1 omitida). Capturas con Edge sin cabeza a 1440 y 768 px con la ventana real, y a 390 y 320 px con un contenedor de ese ancho (el navegador sin cabeza no baja de ~500 px). El traslape se reproduce con el CSS anterior a 390 px y desaparece con el nuevo. No se revisaron a ojo las pantallas de administrador y coordinador.
- **Git [E]:** rama `fix/css-datos-proveedor`, commit `c7ab6fe` (autor Lesly, solo `app.css`), PR #6, fusionada como `7ce5329` en `main`.
- **CI [E]:** PR #6: «Pruebas, migraciones y cobertura» y «Docker Compose (DB + App + Tests)» en verde. CI de `main` sobre `7ce5329`: completado con éxito.
- **Despliegue [E]:** la CSS pública de `https://eventosnova-api.onrender.com/app/css/app.css` ya contiene la corrección (`min(100%, 190px)`), lo que solo ocurre con el commit `7ce5329`. El Dashboard no se consultó.
- **Estado tras el despliegue [E]:** `/health` 200, `/ready` 200 (`postgresql`, `base_de_datos: ok`), `/docs` y `/openapi.json` 404.

## 11. Pruebas funcionales: confirmadas y no realizadas
| Elemento | Estado |
|---|---|
| Inicio de sesión del administrador | Confirmado [U] |
| Inicio de sesión del proveedor y visualización de su asignación de Banquetes (CL-DEMO-02) | Confirmado [U], en el navegador |
| Inicio de sesión y consultas del coordinador y del administrador en producción | Confirmado [U]: la persona usuaria informa que comprobó el acceso autenticado en producción con ambos roles y sus permisos. No recibí el detalle (operaciones, códigos HTTP, capturas); no lo observé yo |
| Escrituras (POST) y pruebas de CSRF desde Swagger | **Solo LOCAL y automatizadas** (sección 14). En producción únicamente se observaron los rechazos 401 sin sesión (sección 15); no consta ninguna escritura con sesión |
| Estado del Outbox (`PENDIENTE`/`REVISION`) | **No verificado** (requiere el Shell de Render) |
| Registros recientes del Worker y de PostgreSQL | **No verificados** (requieren el Dashboard); los archivos guardados son anteriores a la siembra |
| Asignación de Banquetes de CL-DEMO-02 | Pendiente de confirmación **a propósito**, para la demostración en vivo |

## 12. Pendientes reales para la presentación
1. Dashboard → `eventosnova-worker` → *Logs*: confirmar que sigue activo y sin errores desde la siembra.
2. Shell de `eventosnova-api` (solo lectura): `SELECT estado, count(*) FROM outbox_evento GROUP BY 1;` debe mostrar solo `PROCESADO`.
3. Iniciar sesión una vez como coordinador (`coordinador.demo@eventosnova.example`) y abrir los eventos CL-DEMO-01 a 03.
4. Durante la demostración: iniciar sesión como proveedor y responder la asignación de CL-DEMO-02; volver a ejecutar la consulta del punto 2.
5. Revisar a ojo el detalle de un evento y «Datos del proveedor» (administrador y coordinador) tras la corrección CSS.
6. Swagger autenticado en producción: las consultas con administrador y coordinador ya las comprobó la persona usuaria [U]. Falta, solo si se quiere evidencia de escritura en producción, una escritura con datos marcados «PRUEBA SWAGGER» (con el coordinador) y guardar capturas.
7. Guardar las evidencias de la sección 16.

## 13. PR #7 — Mensajes de resultado en español y página `/docs` propia
**Hechos verificados contra GitHub [G]**
| Elemento | Valor |
|---|---|
| PR | #7 `feat/swagger-mensajes`, **fusionada** el 2026-11-06 11:28:31 UTC |
| Fusión en `main` | `d437b99` |
| Commits | `65c317d` (funcionalidad) y `2e00216` (dos frases de consulta y prueba de documentación oculta por omisión) |
| Archivos | `src/api/mensajes.py` (nuevo), `src/api/documentacion.py` (nuevo), `src/api/main.py` (+6/−1), `tests/test_swagger_mensajes.py` (nuevo) |
| CI de `main` sobre `d437b99` | completado con éxito: «Pruebas, migraciones y cobertura» y «Docker Compose (DB + App + Tests)» |
| Despliegue | registros de despliegue en GitHub: `eventosnova-api` y `eventosnova-worker` con `d437b99` en `success` (2026-11-06 11:35 UTC) [G] |

**Qué hace.** Cada respuesta JSON de la API lleva las cabeceras `X-Mensaje` (texto en español, codificado en porcentaje) y `X-Mensaje-Tipo` (`exito`, `info`, `advertencia`, `error`) sin alterar el cuerpo ni el código HTTP. La página `/docs` muestra un aviso con ese texto tras cada *Execute*, construido con `textContent` (nunca interpreta HTML). `/app/`, `/docs`, `/redoc` y `/openapi.json` no reciben cabeceras de mensaje.

**Pruebas LOCALES (base desechable de ensayo)**
- Se ejercitaron flujos reales de la API y se registró lo que recibe cada método y ruta: **77 de 77 operaciones** obtuvieron un mensaje. 72 se observaron con éxito (200/201); las otras 5 (`POST /contratos/{id}/confirmacion`, `GET /eventos/{id}/propuestas`, `POST /proveedores/{id}/activacion`, `POST /proveedores/{id}/edicion`, `POST /usuarios/{id}/contrasena`) solo se observaron con sus errores; sus mensajes de éxito provienen del servicio y no se ejercitaron.
- 354 mensajes distintos observados: ninguno vacío y ninguno incoherente (ningún error con tipo de éxito o información).
- Revisión con Edge: aviso mostrado tras *Execute*.
- Corrección dentro de la PR: dos frases confusas («1 resultado (servicios)» y «estados cuenta»).

**Pruebas AUTOMATIZADAS.** `tests/test_swagger_mensajes.py` (en memoria, sin base de datos) cubre la redacción por método y código, que cuerpos y códigos HTTP sean idénticos con y sin el middleware, que un 500 conserve su cuerpo sin filtrar detalles, que la interfaz web no reciba mensajes y que la documentación esté oculta por omisión en producción.

**Comprobaciones en PRODUCCIÓN tras el despliegue [E]:** `/health` 200 con `X-Mensaje`; `/ready` 200 (`postgresql`, `base_de_datos: ok`); una ruta inexistente → 404 con mensaje de error; `/usuarios` sin sesión → 401 con mensaje de error; `/app/` 200 y CSS publicada. No hubo migraciones ni cambios de base de datos.

## 14. PR #8 — Swagger UI y token CSRF; mensajes de seguridad
**Hechos verificados contra GitHub [G]**
| Elemento | Valor |
|---|---|
| PR | #8 `feat/swagger-csrf`, **fusionada** el 2026-11-06 18:10:26 UTC |
| Commit final en `main` | **`1dfcfdd`** |
| Commits relacionados | `7d1444f` (interceptor CSRF, descripción del esquema, `docs/api/openapi.json` regenerado y pruebas) y `217a7c1` (mensaje del 403 por CSRF u origen) |
| Archivos de la PR | `src/api/documentacion.py`, `src/api/mensajes.py`, `src/api/seguridad.py`, `docs/api/openapi.json`, `tests/test_swagger_mensajes.py` |
| CI de `main` (ejecución 42268272652 sobre `1dfcfdd`) | **los dos trabajos aprobados**: «Pruebas, migraciones y cobertura» (18:10:32–18:15:28 UTC) y «Docker Compose (DB + App + Tests)» (18:10:32–18:15:39 UTC). Los dos trabajos también pasaron en la PR |
| Cobertura | **Sentencias: 98,12 %** (6 751 de 6 880; **129 sin cubrir**). **Ramas: 93,36 %** (1 378 de 1 476; 98 ramas sin cubrir, 90 de ellas en sentencias parcialmente cubiertas). **«TOTAL» combinado de `coverage report`: 97,3 %**, que mezcla sentencias y ramas: (6 751 + 1 378) / (6 880 + 1 476) = 97,28 %. El mínimo exigido por `ci.yml` (80 %) se mide sobre **sentencias**: 98,12 % lo cumple. Fuente: artefacto `cobertura` (`coverage.json`) de la ejecución 42268272652 y la salida de `scripts/verificar_cobertura.py` en su registro [G] |
| Despliegue | `eventosnova-api` y `eventosnova-worker` con `1dfcfdd` en `success` (2026-11-06 18:16:19 y 18:15:58 UTC) [G] |

**Qué cambia.** El `requestInterceptor` de `/docs` pide el token CSRF a `GET /auth/yo` (campo `datos.csrf` del JSON) justo antes de cada POST, PUT, PATCH o DELETE del mismo origen, excepto `POST /auth/inicio-sesion`, y lo envía como `X-CSRF-Token` solo en esa petición. No se guarda en `localStorage`, `sessionStorage`, cookies ni archivos, y `showMutatedRequest: false` evita que aparezca en los cURL. La cookie `eventosnova_sesion` sigue siendo HttpOnly (Secure y SameSite=strict en producción) y la envía el navegador; CSRF, la autenticación y los permisos por rol no se modificaron. La API solo tiene operaciones GET y POST: PUT, PATCH y DELETE se comprobaron en el interceptor, no en endpoints.

**Mensajes de seguridad (`217a7c1`).** Un 403 por token CSRF ausente o vencido, o por origen no permitido, decía «No tienes permisos…». Ahora explica la causa y qué hacer: «No se pudo validar la petición: falta el token de seguridad (CSRF) o venció. Vuelve a iniciar sesión y recarga la página; en Swagger, inicia sesión en /app/ y recarga /docs.» y «La petición se rechazó porque no proviene de este sitio…». El resto de los mensajes (401, 403 por rol, éxitos, validaciones, 500) no se tocó. La descripción del esquema `SesionCookie` ahora aclara que la cookie es HttpOnly y que no hay nada que pegar en *Authorize*.

**Pruebas AUTOMATIZADAS.** `tests/test_swagger_mensajes.py` pasó de 26 a 36 pruebas (10 nuevas): token en `/auth/yo`, GET autenticado, POST con token (201), sin token y con token alterado (403), sin sesión (401), inicio de sesión sin CSRF, atributos de la cookie, permisos del coordinador y del administrador con token válido, 77 operaciones en OpenAPI, ausencia de almacenamiento del token y mensajes de seguridad sin tokens, contraseñas, trazas ni SQL. La prueba de `docs/api/openapi.json` obligó a regenerarlo.

**Pruebas LOCALES (servidor aislado en memoria, Edge real; no es producción)**
- Inicio de sesión por la pantalla de `/app/` en una pestaña y `/docs` en otra del mismo navegador: la sesión se reconoce en `/docs`.
- Coordinador: `GET` proveedores → 200 («Información: Consulta realizada correctamente…»); `POST /eventos` → 201 («Correcto: El evento se registró correctamente»); `GET /usuarios` → 403 («No tienes permisos…»); `POST` sin token y con token incorrecto → 403 con el mensaje CSRF nuevo; tras cerrar sesión, `POST` → 401 («No has iniciado sesión o tu sesión expiró…»).
- Administrador: `GET /usuarios` → 200 (2 usuarios); `POST /eventos` → 403, según la matriz de permisos.
- El interceptor añade `X-CSRF-Token` en POST, PUT, PATCH y DELETE, y no en GET, en el inicio de sesión ni hacia otro origen; 4 escrituras → 4 consultas a `/auth/yo`, sin recursión; `localStorage` y `sessionStorage` vacíos; el cURL mostrado no contiene el token.
- El rol proveedor no se probó en el navegador; solo en las pruebas automatizadas del repositorio.
- La suite completa se ejecutó localmente **sin PostgreSQL** (no está disponible en el equipo): 1 427 pruebas, 49 omitidas; solo falla el artefacto de descubrimiento `src.ejecucion_paquete`, que también falla en `main` sin estos cambios. Las pruebas con PostgreSQL y Docker las cubre el CI.

## 15. Swagger en PRODUCCIÓN: estado observado
Comprobaciones de solo lectura, sin sesión [E], realizadas tras el despliegue de `1dfcfdd`:
| Ruta | Resultado |
|---|---|
| `/docs` | 200; contiene el interceptor CSRF y `showMutatedRequest: false` |
| `/redoc` | 200 |
| `/openapi.json` | 200; 77 operaciones; sin cadenas de conexión, `bearer` ni secretos; la descripción de `SesionCookie` trae el texto nuevo |
| `/health` | 200 |
| `/ready` | 200 |
| `/app/` | 200 |
| `GET /auth/yo` sin sesión | 401, `X-Mensaje`: «No has iniciado sesión o tu sesión expiró. Inicia sesión para continuar.» |
| `POST /eventos` sin sesión | 401, mismo mensaje |

**Acceso autenticado en producción [U].** La persona usuaria informa que comprobó en producción, con el administrador y con el coordinador, el acceso autenticado y los permisos correspondientes. Qué consta y qué no:
| Aspecto | Alcance |
|---|---|
| Consultas (GET) autenticadas en producción, administrador y coordinador, y sus permisos | Informado [U]. Yo no inicié sesión en producción ni vi las respuestas |
| Rechazos 401 sin sesión en producción | Observado por mí [E] (tabla anterior) |
| Escrituras (POST con sesión) en producción | **No consta ninguna**; no se creó ningún registro «PRUEBA SWAGGER» |
| Token CSRF ausente o incorrecto (403), POST con token (201), permisos por rol con escritura | **Solo LOCAL** (sección 14) y AUTOMATIZADAS |
| Rol proveedor desde Swagger | No probado en navegador; solo pruebas automatizadas |

`EVENTOSNOVA_DOCS=1` está activo (la documentación responde 200); su valor no se vio en el Dashboard. El `openapi.json` publicado no es idéntico byte a byte a `docs/api/openapi.json`; la diferencia no se analizó.

## 16. Evidencias que conviene conservar
- PR #6, #7 y #8 en GitHub y sus ejecuciones de Actions (en especial la 42268272652 sobre `1dfcfdd`: sentencias 98,12 %, ramas 93,36 %, TOTAL combinado 97,3 %) y su artefacto `cobertura` (`coverage.json`).
- Pestaña *Deployments* de GitHub o *Events* del Dashboard de Render con `1dfcfdd` en `eventosnova-api` y `eventosnova-worker`.
- Captura de `https://eventosnova-api.onrender.com/docs` con las 77 operaciones.
- Capturas de *Execute* autenticados en producción (GET 200 con administrador y con coordinador, y un 403 por rol), con el aviso en español, y una captura del 401 sin sesión. Si se hace una escritura de prueba, su 201 con datos «PRUEBA SWAGGER».
- `docs/api/openapi.json` del repositorio (estructura mínima del PIA).
- Este reporte.

## 17. Secreto `RENDER_DEPLOY_HOOK_URL` en GitHub [G]
Consultado con la API de `gh` (solo lectura; no se vio ni se escribió ningún valor):
| Pregunta | Resultado |
|---|---|
| ¿Existe `RENDER_DEPLOY_HOOK_URL`? | **No.** El repositorio tiene **0 secretos** de Actions y 0 variables de Actions |
| ¿Lo usa algún workflow? | **No con ese nombre.** `publicar-imagen.yml` lee un secreto llamado **`DEPLOY_HOOK_URL`** (otro nombre), que tampoco existe; el paso es opcional y se omite si no está definido. `ci.yml` no usa secretos |
| ¿Cuándo corre ese workflow? | Solo al crear una etiqueta `v*` o a mano. No tiene ejecuciones registradas |
| ¿Render despliega desde GitHub? | **Sí.** `render.yaml` define `autoDeployTrigger: checksPass` y GitHub registra los despliegues de Render (entornos `main - eventosnova-api`, `main - eventosnova-worker`, `main - eventosnova-db`); los de `d437b99` y `1dfcfdd` ocurrieron segundos después de que CI terminó en verde, sin ningún *hook* |
| ¿Es necesario? | **No; sería redundante.** El despliegue ya es automático y ligado a CI. La documentación del repositorio (`docs/architecture/ci-cd-y-despliegue.md`) lo describe como opcional |
| ¿Cumple los requisitos de la actividad? | **Depende de la rúbrica**, que no está en el repositorio y no se ha comprobado. Técnicamente no es necesario: el pipeline (CI con cobertura ≥ 80 %, imagen Docker, despliegue automático en Render) funciona sin el secreto. Si la rúbrica exigiera explícitamente un *deploy hook* o ese secreto, habría que añadirlo; no se creó |

Si más adelante se quisiera usar el *hook*, el secreto debería llamarse `DEPLOY_HOOK_URL` (no `RENDER_DEPLOY_HOOK_URL`) o habría que cambiar el workflow. No se creó nada.

## 18. Worker, PostgreSQL y Outbox: revisión de los registros disponibles
**Registros disponibles [E]:** tres archivos guardados por la persona usuaria en `C:\Users\YAZMIN\Downloads\Logs_Render_EventosNova\` (`01-api-render.txt`, `02-worker-render.txt`, `03-postgresql-render.txt`). Marcas de tiempo de 2026-11-06 entre 06:54 y 07:16 UTC; los archivos se guardaron a las 01:15–01:17 (hora local) y la siembra figura a las 02:48 (hora de negocio, sección 5): **son anteriores a la siembra y a los despliegues de las PR #6, #7 y #8**. No pude descargar registros nuevos (sin acceso a Render).
| Registro | Resultado |
|---|---|
| Worker (10 líneas) | Arranque normal. Una advertencia esperada a las 06:54:44 UTC: «Esperando a que la base de datos esté lista (EsquemaDesactualizado)… revisión «ninguna»», porque la migración aún corría; a las 06:54:50 UTC: «La base de datos está lista tras 6 s (2 intentos)». Sin errores ni trazas |
| API (49 líneas) | 50 peticiones, todas con código 200 (comprobaciones de salud). Sin errores ni respuestas 5xx |
| PostgreSQL (49 líneas) | Sin `FATAL`, `ERROR` ni fallos de autenticación |

**Conclusión:** en los registros disponibles no hay errores del Worker, pero no cubren ni la siembra ni el funcionamiento posterior. **No se verificó que el Worker siga activo y sin errores desde la siembra.**

**Estados del Outbox: no se pudieron consultar.** Los medios disponibles en este equipo no lo permiten: no hay acceso al Dashboard ni al Shell de Render, ningún endpoint de la API lo expone sin una sesión iniciada, y no se usaron credenciales de la base de datos. No se ejecutó ninguna consulta ni modificación. Sigue pendiente, desde el Shell de `eventosnova-api` y solo lectura: `SELECT estado, count(*) FROM outbox_evento GROUP BY 1;` (debe mostrar solo `PROCESADO`).

## 19. Demostración funcional: CL-DEMO-01, CL-DEMO-02 y CL-DEMO-03
**Documentación revisada [E]:** este reporte (secciones 5, 6, 11 y 12), `scripts/sembrar_datos_demo.py` (reglas, eventos con fechas fijas de 2027 y cliente CL-DEMO-01/02/03), `tests/test_sembrar_datos_demo.py` (pruebas de la siembra y del flujo de la asignación pendiente y su respuesta por el proveedor) y el archivo de progreso local. No hay otra guía de demostración rastreada en el repositorio que mencione estos eventos.
| Evento | Contenido sembrado [P][U] | Verificado |
|---|---|---|
| CL-DEMO-01 | Evento y propuesta (E1) | Creación informada en el progreso; sin consulta posterior en producción |
| CL-DEMO-02 | Evento, propuesta, aceptación, contrato (política y firma), anticipo de 3,000.00 MXN y asignación de Banquete **pendiente a propósito** | El proveedor inició sesión y vio la asignación [U]. La respuesta del proveedor **no se ha dado** (reservada para la demostración) |
| CL-DEMO-03 | Evento, propuesta, aceptación, contrato, anticipo de 3,000.00 MXN, cancelación y revisión administrativa (pagos 3,000.00; saldo pendiente 7,000.00) | Creación informada en el progreso; sin consulta posterior en producción |

**Pruebas realizadas**
- Automatizadas: la siembra (primera ejecución, idempotencia, coherencia entre eventos, propuestas, contratos y pagos, pérdida de respuestas, roles autorizados, asignación pendiente y respuesta del proveedor, sin credenciales en archivos).
- Producción [U]: inicio de sesión del administrador y del proveedor; el proveedor vio su asignación de CL-DEMO-02. Consultas autenticadas con administrador y coordinador (sección 15).
- Local [E]: corrección visual de «Mis datos» con capturas (sección 10); mensajes y Swagger (secciones 13 y 14).

**Pruebas que faltan**
1. Responder como proveedor la asignación de CL-DEMO-02 (flujo en vivo) y comprobar después el Outbox.
2. Revisar a ojo las pantallas de detalle de CL-DEMO-01, 02 y 03 con administrador y coordinador, y «Datos del proveedor» tras la corrección CSS (en las capturas locales no se revisaron las pantallas de administrador y coordinador).
3. Comprobar el estado de los tres eventos por GET en producción (el script lo permite con `--verificar-estado`, que inicia sesión y hace solo GET).
4. Estado del Outbox y registros recientes del Worker (sección 18).

## 20. Requisitos de la rúbrica sin comprobar
- La rúbrica o el enunciado de la actividad no está en el repositorio: no se pudo contrastar ningún requisito contra el texto original (por ejemplo, si exige un *deploy hook* o el secreto `RENDER_DEPLOY_HOOK_URL`, sección 17).
- Entregables de documentación (informes, diagramas, evidencias) no se revisaron en esta actualización.
- Evidencias gráficas de Swagger autenticado en producción (sección 16).

## 9. Errores encontrados
- `UnicodeEncodeError` de los scripts en la consola de Windows: resuelto con `PYTHONUTF8=1`.
- `--aplicar` en el Shell de Render: código 2 (sin Git ni `.gitignore`). Resuelto ejecutándolo desde el equipo local.
- `.gitignore` ya ignoraba `scratchpad/`, de modo que el progreso y el candado nunca se publican.
