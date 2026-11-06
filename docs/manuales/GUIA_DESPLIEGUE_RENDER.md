# Guía de despliegue de Eventos Nova en Render

**Estado al 06/11/2026: NO desplegado.** Esta guía y `render.yaml` dejan todo preparado para revisar el costo y autorizar el *Apply*. Nada de lo que sigue se ha ejecutado en Render: las
pruebas de la sección 1 se hicieron en un equipo local con la imagen Docker real. No hay URL pública hasta que alguien aplique el Blueprint y se complete la
[matriz de pruebas](../calidad/MATRIZ_PRUEBAS_DESPLIEGUE_RENDER.md).

Convenciones: `<...>` es un dato que debe poner la persona que despliega; **nunca** escriba contraseñas, tokens ni cadenas de conexión en el repositorio, en mensajes o en capturas.

## 1. Qué crea el Blueprint y qué se verificó en local

| Recurso | Tipo | Región | Plan | Notas |
|---|---|---|---|---|
| `eventosnova-db` | PostgreSQL 18 | Ohio | `0.1c-256mb` (antes `basic-256mb`) | Disco de 1 GB, sin acceso externo (`ipAllowList: []`) |
| `eventosnova-api` | Web (Docker) | Ohio | `0.5c-512mb` (antes `starter`) | Etapa final `runtime` del `Dockerfile`; `healthCheckPath: /ready`; `preDeployCommand: python -m alembic upgrade head` |
| `eventosnova-worker` | Worker (Docker) | Ohio | `0.5c-512mb` | `python -m infrastructure.persistencia.trabajador_outbox --intervalo 2` |

Comprobado **en local** (imagen construida con `docker build .`, base PostgreSQL desechable; no equivale a Render):

| Comprobación | Resultado |
|---|---|
| El Dockerfile, sin `--target`, construye la API (usuario sin privilegios, uvicorn en `0.0.0.0:$PORT`) | Correcto |
| `python -m alembic upgrade head` dentro de la imagen (preDeployCommand) | Correcto; una sola cabeza de Alembic en el repositorio |
| API con `EVENTOSNOVA_ENTORNO=produccion` y `PORT=10000` | `/health` 200, `/ready` 200 con `persistencia: postgresql` y `base_de_datos: ok` |
| `/docs`, `/redoc`, `/openapi.json` por omisión | 404 (ocultos) |
| Con `EVENTOSNOVA_DOCS=1` | `/docs` 200 y `/openapi.json` 200 (77 operaciones) |
| Cabeceras de seguridad | `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Cache-Control: no-store` |
| `scripts/crear_administrador.py` con `--servidor-remoto` (como en el Shell de Render) | Administrador creado |
| Detrás de un proxy TLS simulado (`X-Forwarded-Proto: https`, `FORWARDED_ALLOW_IPS=*`) | Inicio de sesión 200; cookie `Secure`, `HttpOnly`, `SameSite=Strict`; POST con CSRF y Origin correctos 201; Origin ajeno 403; sin token CSRF 403 |
| La misma API **sin** `FORWARDED_ALLOW_IPS` | El inicio de sesión devuelve 403 (por eso la variable es obligatoria) |
| Reinicio de la API | Los datos y el inicio de sesión persisten |
| Worker (`dockerCommand` del Blueprint) | Se conecta, queda activo y al recibir SIGTERM termina con código 0 |

## 2. Validar el Blueprint antes de usarlo

`render.yaml` se validó contra el esquema JSON oficial que publica Render (`https://render.com/schema/render.yaml.json`): **0 errores**. Para repetirlo (usa carpetas temporales, no
modifica el proyecto):

```text
python -m pip install --target <carpeta-temporal> jsonschema pyyaml
curl -o <carpeta-temporal>/render.schema.json https://render.com/schema/render.yaml.json
python - <<'FIN'      # en PowerShell, guarde el fragmento en un archivo .py y ejecútelo
import sys, json
sys.path.insert(0, "<carpeta-temporal>")
import yaml, jsonschema
esquema = json.load(open("<carpeta-temporal>/render.schema.json", encoding="utf-8"))
documento = yaml.safe_load(open("render.yaml", encoding="utf-8"))
errores = list(jsonschema.Draft202012Validator(esquema).iter_errors(documento))
print("errores de esquema:", len(errores))
FIN
```

Las invariantes del Blueprint (tres recursos, Ohio, planes vigentes, base privada, migraciones solo en la API, worker real, sin secretos) también se comprueban en CI con
`tests/test_render_blueprint.py`.

## 3. Costos: revisar ANTES del Apply

| Concepto | Cantidad | Precio mensual | Estado de la cifra |
|---|---|---|---|
| Web service `0.5c-512mb` | 1 | 7 USD | Página de precios de Render; **confirmar en el Dashboard** |
| Background worker `0.5c-512mb` | 1 | 7 USD | Ídem |
| PostgreSQL `0.1c-256mb` (instancia) | 1 | 6 USD | Página de precios de Render y un artículo de Render. La página de tipos heredados indica 7 USD para el plan «Starter» antiguo, **no disponible para bases nuevas**; **confirmar en el Dashboard** |
| Almacenamiento PostgreSQL | 1 GB | 0.30 USD por GB-mes → 0.30 USD | Página de precios de Render; se elige 1 GB o múltiplos de 5 GB; **confirmar** |
| Workspace Hobby | 1 | 0 USD (sin cuota mensual, solo uso) | Documentación oficial de Render |
| **Total estimado** | | **≈ 20.30 USD/mes** | Presupuesto del equipo: ≈ 20 USD |

- Con el disco por omisión de ese plan (15 GB, que Render propone si no se indica `diskSizeGB`) el almacenamiento costaría 4.50 USD y el total subiría a ≈ 24.50 USD. El disco se fijó en
  **1 GB** tras medir el tamaño real: 9 MB con el esquema vacío y 12 MB con 105 eventos, 110 cuentas y 604 sesiones de las pruebas manuales. Puede ampliarse después (no reducirse).
- **No cuantificados** (no se encontraron cifras verificables): ancho de banda saliente, minutos de *pipeline* usados por builds y por el `preDeployCommand`, y cargos por exceso.
- El workspace **Hobby** admite **un solo miembro**. Si varias personas del equipo necesitan acceso al Dashboard hará falta el plan Pro (precio no verificado), lo que cambia el presupuesto.
  Hobby conserva 3 días de recuperación a un punto en el tiempo; Pro, 7.
- **Regla:** si el Dashboard muestra un total distinto del esperado, no aplique el Blueprint y consulte al equipo.
- Al terminar la revisión académica, suspenda o elimine los recursos desde el Dashboard para dejar de pagar (consulte en la documentación vigente de Render cómo factura cada estado).
  Eliminar una base de datos **no conserva copias**.

## 4. Procedimiento paso a paso

Los nombres exactos de menús y botones del Dashboard pueden variar; lo importante es lo que se verifica en cada paso.

1. **Conectar el repositorio.** En el Dashboard de Render: *New* → *Blueprint* → conectar la cuenta de GitHub y autorizar a Render para `leslynieto64-del/EventosNova-PIA`.
2. **Seleccionar el Blueprint.** Repositorio `EventosNova-PIA`, rama `main` (debe contener la versión de `render.yaml` aprobada). Render lee `render.yaml` de la raíz.
3. **Revisar región y costo.** La vista previa debe mostrar **tres** recursos (`eventosnova-db`, `eventosnova-api`, `eventosnova-worker`), todos en **Ohio**, y un total consistente con la sección 3. Si
   aparece otra región, un plan gratuito, otro número de recursos o un total distinto: **detenerse**.
4. **Autorización.** El *Apply* crea recursos de pago: solo debe pulsarlo quien tenga la autorización del equipo.
5. **Comprobar la creación.** Esperar a que la base esté disponible, que la API termine su primer despliegue (el `preDeployCommand` aplica las migraciones) y que el worker quede activo.
   Es posible que el worker falle en los primeros minutos si arranca antes de que terminen las migraciones (el proceso se niega a iniciar con un esquema desactualizado; no se ha
   comprobado en Render cuántas veces lo reintenta la plataforma). Debe estabilizarse cuando la API termine su despliegue; si sigue fallando después, revise sus logs (sección 6).
6. **Confirmar variables** (sección 5) en *Environment* de cada servicio.
7. **Comprobar PostgreSQL.** En la base: región Ohio, versión 18, sin direcciones permitidas para conexiones externas. Los servicios usan la URL **interna**.
8. **Migraciones.** Ver la sección 6.
9. **Salud.** `GET https://<dominio-de-la-api>/health` → 200 y `GET https://<dominio-de-la-api>/ready` → 200 con `base_de_datos: ok`.
10. **Administrador inicial.** Sección 7.

## 5. Variables de entorno

| Variable | Servicio | Origen | Secreta |
|---|---|---|---|
| `DATABASE_URL` | API y worker | Automática (`fromDatabase`, URL interna) | **Sí** (incluye la contraseña; no la copie ni la publique) |
| `EVENTOSNOVA_PERSISTENCIA=postgresql` | API y worker | `render.yaml` | No |
| `EVENTOSNOVA_ENTORNO=produccion` | API y worker | `render.yaml` | No |
| `FORWARDED_ALLOW_IPS=*` | Solo API | `render.yaml` | No |
| `EVENTOSNOVA_DOCS=1` | Solo API | **Manual**, temporal (sección 8) | No |

No defina nunca `EVENTOSNOVA_AUTENTICACION=desactivada`, `EVENTOSNOVA_COOKIE_SEGURA=0` ni `EVENTOSNOVA_DISPONIBILIDAD_ARCHIVO`: la aplicación se niega a arrancar con ellas. Las
demás variables (`EVENTOSNOVA_ORIGENES_PERMITIDOS`, tiempos de sesión y de bloqueo) tienen valores por omisión adecuados; `EVENTOSNOVA_ORIGENES_PERMITIDOS` solo haría falta para un
origen distinto del de la propia API.

## 6. Migraciones, logs y salud

- **Migraciones.** Las ejecuta el `preDeployCommand` de la API en cada despliegue, **antes** de arrancar la nueva versión; si fallan, el despliegue se cancela y sigue la versión anterior
  (el límite de tiempo del comando es de 30 minutos). Solo la API migra: así se evitan carreras con el worker. La última revisión del repositorio es **`0009`** (una sola cabeza). Para
  comprobarlo en Render: Shell de la API → `python -m alembic current` debe mostrar `0009 (head)`.
- **Logs.** Dashboard → servicio → *Logs*. Busque en la API los registros de arranque y del `preDeployCommand`; en el worker, `Trabajador detenido` solo debe aparecer al reiniciar. No
  debe haber trazas de error repetidas ni contraseñas en ningún log.
- **Salud.** `/health` solo confirma que el proceso responde; `/ready` además consulta la base (503 si no responde) y es el *health check* del Blueprint.

## 7. Crear el administrador inicial

No hay credenciales predeterminadas. Desde el **Shell** del servicio `eventosnova-api` (disponible en servicios web de pago):

```text
python scripts/crear_administrador.py --base eventosnova --servidor-remoto --correo <correo-del-administrador> --nombre "<Nombre Apellido>"
```

El script pide la contraseña con `getpass` (sin eco, dos veces; mínimo 12 caracteres). Compruebe que la terminal **no muestra** lo que escribe; si lo muestra, no continúe. No use
`--contrasena-desde-entorno` en producción. Solo crea un administrador si todavía no hay ninguno.

Probar el inicio de sesión: abra `https://<dominio-de-la-api>/app/`, entre con ese administrador y compruebe que ve el panel; después cierre sesión. Si el inicio de sesión devuelve 403,
revise que `FORWARDED_ALLOW_IPS` exista en la API.

## 8. Swagger para la revisión académica

Activar (temporal): *Environment* de `eventosnova-api` → añadir `EVENTOSNOVA_DOCS` = `1` → guardar y esperar el redespliegue. Comprobar `GET /docs` → 200 y `GET /openapi.json` → 200.
Swagger muestra la estructura de las 77 operaciones, no datos ni credenciales; probar operaciones desde él exige iniciar sesión y el token CSRF.

Desactivar: eliminar la variable (o dejarla distinta de `1`) → guardar y esperar el redespliegue. Comprobar `GET /docs` y `GET /openapi.json` → 404.

## 9. Persistencia tras reiniciar

1. Cree un dato inocuo con la interfaz (por ejemplo un proveedor `[DEMO] Prueba de persistencia`).
2. Reinicie `eventosnova-api` desde el Dashboard (reinicio manual) y espere a que `/ready` vuelva a responder 200.
3. Compruebe que puede iniciar sesión de nuevo y que el dato sigue.
4. Repita con `eventosnova-worker`.

## 10. Datos de demostración (después de verificar el despliegue)

Solo cuando las pruebas DEP-01 a DEP-13 de la matriz estén aprobadas y el administrador exista. Desde una copia del repositorio en su equipo (no en Render), con las dependencias
instaladas, y **en este orden**:

```text
python scripts/sembrar_datos_demo.py --base-url https://<dominio-de-la-api> --entorno produccion --admin-correo <correo-del-administrador>                       # --simular
python scripts/sembrar_datos_demo.py --base-url https://<dominio-de-la-api> --entorno produccion --admin-correo <correo-del-administrador> --verificar-estado    # pide VERIFICAR ESTADO EN <host>
python scripts/sembrar_datos_demo.py --base-url https://<dominio-de-la-api> --entorno produccion --admin-correo <correo-del-administrador> --aplicar             # pide SEMBRAR DEMO EN <host>
```

Revise la salida de cada paso antes de continuar. Las contraseñas del administrador, del coordinador y del proveedor de demostración se piden con `getpass`; guárdelas en un gestor de
contraseñas. La respuesta del proveedor a la asignación de Banquete queda **pendiente** para responderla en vivo con la cuenta del proveedor. Al terminar la demostración, desactive las
cuentas de demostración (`POST /usuarios/{id}/estado` con `activo: false`).

## 11. Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| El Apply muestra otra región, un plan gratuito o un total inesperado | Blueprint distinto del aprobado | No aplicar; comparar `render.yaml` con `main` |
| El despliegue de la API se cancela en el pre-despliegue | Fallo en las migraciones (ver el log) | Corregir y volver a desplegar; la versión anterior sigue activa |
| `/ready` devuelve 503 | La base no responde o el esquema no está al día | Revisar la base y los logs de la API |
| El inicio de sesión devuelve 403 | Falta `FORWARDED_ALLOW_IPS=*` en la API | Añadirla y redesplegar |
| El worker se reinicia sin parar | Esquema sin migrar o `DATABASE_URL` ausente | Esperar el despliegue de la API; revisar variables y logs |
| `/docs` devuelve 404 | Swagger desactivado (valor por omisión) | Ver la sección 8 |
| La API no arranca con un error de configuración | Se definió autenticación desactivada o cookie insegura | Eliminar esa variable |

## 12. Fuentes consultadas (6 de noviembre de 2026)

- Esquema JSON oficial del Blueprint: https://render.com/schema/render.yaml.json · Referencia: https://render.com/docs/blueprint-spec
- Planes de cómputo y nombres heredados: https://render.com/docs/compute-plans · Regiones: https://render.com/docs/regions
- Render Postgres: https://render.com/docs/postgresql-creating-connecting · copias: https://render.com/docs/postgresql-backups
- Pre-despliegue y despliegues: https://render.com/docs/deploys · Planes de workspace: https://render.com/docs/platform-features-by-plan · Precios: https://render.com/pricing
