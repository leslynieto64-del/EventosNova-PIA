# CI/CD y despliegue (fase final, Etapas 10 y 11)

## Estado real

| Elemento | Estado | Evidencia |
|---|---|---|
| Workflows `ci.yml` y `publicar-imagen.yml` | Escritos y validados **estáticamente** con actionlint (rc=0) | `docker run rhysd/actionlint` sobre `.github/` |
| Ejecución en GitHub Actions | **No ejecutada.** El repositorio local no tiene remoto configurado (`git remote -v` vacío) y no hay `gh` ni credenciales | — |
| Los mismos pasos, ejecutados localmente | Sí, el 24/10/2026 (cuando la cabeza de Alembic era `0004`): migraciones (una sola cabeza, SQL offline), preparación de la base de pruebas, suite con cobertura y mínimo del PIA, `docker compose config`, imágenes, suite dentro de Docker, API sana. La revisión vigente es hoy `0009` (9 migraciones); esa secuencia completa **no se repitió** con ella | `tests/evidencias/ejecucion-pruebas-fase-final-etapa7-20261024.txt`, `cobertura-fase-final-20261024.txt` |
| Despliegue en una plataforma | **No realizado.** No hay plataforma, credenciales ni permisos | — |
| URL del sistema desplegado | **No existe.** No se inventa ninguna | — |

Una validación estática (actionlint) no demuestra que el pipeline funcione en GitHub: eso solo se sabe tras la primera ejecución real.

## CI (`.github/workflows/ci.yml`)

Dos trabajos: `pruebas` (PostgreSQL 18 como servicio efímero, instala dependencias, verifica una sola cabeza de Alembic y el SQL offline, migra, prepara la base de pruebas, ejecuta TODA la suite con cobertura y exige ≥ 80 % de sentencias) y `docker` (valida Compose, construye imágenes, ejecuta la suite dentro de Docker y comprueba `/ready`, `/health` y `/docs`). `EVENTOSNOVA_REQUIERE_BD=1` hace que la falta de PostgreSQL falle las pruebas en vez de omitirlas. La contraseña del servicio es la de una base efímera del job, no un secreto real.

### Cómo validarlo en GitHub (pasos manuales)

1. Revisar y versionar los archivos (ver la lista de abajo); **no se hizo ningún commit ni push**.
2. Crear el repositorio remoto, `git remote add origin <URL>` y publicar la rama.
3. Abrir Actions → ejecutar `CI` (disparo manual `workflow_dispatch` o por `push`/`pull_request`) y confirmar que ambos trabajos terminan en verde. Si algo falla, el paso «Registros de los servicios» muestra los logs de Compose.
4. Opcional: el workflow de publicación de imagen necesita permisos de paquetes y, si se desea el disparo de un despliegue, el secreto `DEPLOY_HOOK_URL`.

### Cuándo se ejecuta cada workflow

- `ci.yml`: en `push` a `main`, en cada `pull_request` y a mano (`workflow_dispatch`, que solo aparece en Actions cuando el archivo ya está en la rama por defecto). Una rama de trabajo sin PR no lo dispara.
- `publicar-imagen.yml`: solo con una etiqueta `v*` o a mano; no se ejecuta en cada commit ni despliega por sí mismo.

### Riesgo conocido: contenedor `migrate` que termina

En `docker-compose.yml` el servicio `migrate` ejecuta `alembic upgrade head` y **termina con código 0 a propósito** (`restart: "no"`); `api` y `worker` esperan con `condition: service_completed_successfully`. El paso del CI «Levantar DB + migrate + API + worker» usa `docker compose up -d --wait --wait-timeout 180`. Con `--wait`, algunas versiones de Compose tratan un contenedor que ya terminó como un servicio que no quedó «running/healthy», y el paso podría fallar aunque la migración haya salido bien.

- **Estado:** riesgo **no confirmado ni descartado**. Localmente se verificó `docker compose up -d` (24/10/2026), no `up -d --wait`; el equipo usa Docker Compose v5.6.0, pero la versión del ejecutor `ubuntu-latest` de GitHub no se ha comprobado.
- **Qué hacer:** observar el resultado de la primera ejecución real. Si falla en ese paso (el mensaje indica que `migrate` salió), las opciones son: quitar `--wait` y esperar con un bucle que consulte `/ready`; o esperar solo a `api` (`docker compose up -d --wait api worker`). El workflow **no se cambió** a ciegas.

### Archivos que la CI necesita versionados

`.github/`, `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `.env.example`, `alembic.ini`, `migraciones/`, `scripts/`, `src/` (incluido `src/infrastructure/persistencia/` y `src/infrastructure/datos_demo/`), `tests/`, `datos/`, `docs/`, `requirements*.txt`, `.coveragerc`, `README.md` y el cierre de alcance aprobado. **No** deben subirse `.env`, `.coverage`, `htmlcov/`, `.venv/`, `backups/`, `scratchpad/` ni `tests/evidencias/pruebas_manuales_web/datos_controlados.json` (todos excluidos por `.gitignore`).

## Despliegue funcional

El PIA pide un despliegue con Swagger/OpenAPI accesible. La aplicación está lista para cualquier plataforma que ejecute contenedores y ofrezca PostgreSQL gestionado:

| Pieza | Configuración |
|---|---|
| Imagen | `Dockerfile`, etapas `app` (API), `tests` (suite) y `runtime` (**etapa final y predeterminada**, igual que `app`: sin pruebas, dependencias de desarrollo ni secretos). Una plataforma que construye el Dockerfile sin indicar etapa (Render) obtiene `runtime` y ejecuta la API, no `unittest`; CI y Compose siguen usando `app` y `tests` de forma explícita. `runtime` debe seguir siendo la última etapa. Escucha en `$PORT` (8000 por omisión) |
| Base de datos | PostgreSQL 18 gestionado. Variable `DATABASE_URL` (se aceptan `postgres://`, `postgresql://` y `postgresql+psycopg://`) |
| Modo de persistencia | `EVENTOSNOVA_PERSISTENCIA=postgresql` |
| Paso previo | `python -m alembic upgrade head` (comando de pre-despliegue o *release*) |
| Proceso web | el `CMD` de la imagen (`uvicorn api.main:app`) |
| Trabajador del Outbox | segundo proceso con `python -m infrastructure.persistencia.trabajador_outbox --intervalo 2`; con `EVENTOSNOVA_DESPACHO_EN_LINEA=1` (por omisión) la API también despacha dentro de la petición. **Es obligatorio**: además del Outbox, aplica en cada ciclo la llegada de T (inicio automático y cierre sin contratación, ADR-008); sin él no hay inicio automático |
| Comprobación de salud | `GET /ready` (200 solo con la base disponible y el esquema al día) |
| Entorno | `EVENTOSNOVA_ENTORNO=produccion` (cookie `Secure`, HSTS, autenticación obligatoria, `/docs` oculto) y `FORWARDED_ALLOW_IPS` con el proxy TLS de la plataforma |
| Swagger / OpenAPI | `/docs` y `/openapi.json` (77 operaciones: 73 protegidas y 4 públicas). **En producción están ocultos por omisión: para la demostración del PIA hay que definir `EVENTOSNOVA_DOCS=1` a mano en el servicio web** |
| **No existe** (D-P3, 01/11/2026): la disponibilidad, el costo y las condiciones de los proveedores se registran manualmente; la fuente simulada es solo para pruebas automatizadas y la aplicación se niega a arrancar si `EVENTOSNOVA_DISPONIBILIDAD_ARCHIVO` está definida | — |

`render.yaml` es un **borrador no aplicado** (web, trabajador y PostgreSQL de Render): fija `postgresMajorVersion: "18"` (igual que el CI), usa `autoDeployTrigger: checksPass` (despliega solo si pasan las comprobaciones de CI del commit) y no define `EVENTOSNOVA_DOCS` (se añade a mano en el servicio web). No elige región (Render usa `oregon` por omisión) y sus planes deben confirmarse en Render antes de usarlo. El job `docker` del CI construye el Dockerfile **sin `--target`** y comprueba que la imagen resultante inicia uvicorn (no `unittest`), con usuario sin privilegios y sin la carpeta `tests`. No se ha configurado ni desplegado nada.

### Pasos manuales exactos

1. Elegir la plataforma y crear un servicio web desde el `Dockerfile` (objetivo `app`) y una base PostgreSQL 18.
2. Definir `DATABASE_URL` (la entrega la plataforma), `EVENTOSNOVA_PERSISTENCIA=postgresql` y `EVENTOSNOVA_ENTORNO=produccion` como variables del servicio; en el servicio web, además, `EVENTOSNOVA_DOCS=1` para mostrar Swagger.
3. Configurar el comando de pre-despliegue `python -m alembic upgrade head`.
4. Crear el segundo servicio (trabajador) con la misma imagen y variables (sin `EVENTOSNOVA_DOCS`) y el comando indicado.
5. Crear el primer administrador (no hay credenciales predeterminadas) con `scripts/crear_administrador.py` ejecutado contra la base de la plataforma.
6. Verificar con la URL real que entrega la plataforma: `GET /ready` → 200, `GET /docs` carga, y un flujo de prueba (crear evento, propuesta, contrato y pago).
7. Anotar la URL real en el reporte y la presentación **solo después** de comprobarla. El HTTPS real solo puede afirmarse tras esa comprobación.

### Verificación local equivalente (realizada)

`docker compose up -d` levanta `db`, `migrate`, `api` y `worker`; la API quedó sana (`/ready` → `{"estado":"ok","persistencia":"postgresql","base_de_datos":"ok"}`), `/docs` responde 200, `/openapi.json` listó entonces 60 operaciones (la OpenAPI vigente tiene 77; esta verificación no se repitió), un evento creado por HTTP sobrevive al reinicio del contenedor `api`, la imagen respeta `PORT` (probado con `PORT=9123`) y la migración funciona con una URL `postgres://`. Falta lo que requiere recursos externos: ejecución en GitHub, plataforma, credenciales y URL pública.
