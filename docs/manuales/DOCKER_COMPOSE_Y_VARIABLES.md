# Docker Compose y variables de entorno de Eventos Nova

Este contenido está integrado en el Manual técnico (secciones 7, 9 y 11) y en el README. Aquí se conservan los archivos de configuración vigentes, copiados sin cambios del commit `e3c98d9` (el commit `9c72bc7`, publicado después, solo añade una regla de `.gitattributes`) el 05/11/2026.

## Servicios

| Servicio | Imagen | Puerto | Dependencias | Persistencia / red |
|---|---|---|---|---|
| db | postgres:18 | 127.0.0.1:5432 | — | volumen `eventosnova_pgdata`; red `eventosnova_default` |
| migrate | eventosnova-app:local | — | db (healthy) | — |
| api | eventosnova-app:local | 127.0.0.1:8000 | db (healthy), migrate (completado) | healthcheck `/ready` |
| worker | eventosnova-app:local | — | db (healthy), migrate (completado) | — |
| tests (perfil) | eventosnova-tests:local | — | db (healthy) | base `eventosnova_test` |

## Variables

| Variable | Valor de referencia | Uso |
|---|---|---|
| `POSTGRES_DB` | eventosnova | Nombre de la base de desarrollo (servicio db) |
| `POSTGRES_USER` | eventosnova | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | (obligatoria; solo en .env) | Contraseña local; Compose falla si no está definida |
| `POSTGRES_PORT` | 5432 | Puerto publicado en 127.0.0.1 |
| `API_PORT` | 8000 | Puerto publicado de la API en 127.0.0.1 |
| `DATABASE_URL` | postgresql+psycopg://usuario:clave@host:5432/base | Base de desarrollo (Alembic y API fuera de Docker); en la plataforma la inyecta el servicio de base de datos |
| `TEST_POSTGRES_DB` | eventosnova_test | Base de pruebas; debe terminar en _test |
| `TEST_DATABASE_URL` | postgresql+psycopg://...@host:5432/eventosnova_test | URL de la base de pruebas |
| `EVENTOSNOVA_REQUIERE_BD` | 1 en CI y Compose | Sin PostgreSQL las pruebas de integración fallan en lugar de omitirse |
| `EVENTOSNOVA_PERSISTENCIA` | memoria | postgresql | Modo de persistencia; Compose y la plataforma usan postgresql. No se fija en .env |
| `EVENTOSNOVA_DESPACHO_EN_LINEA` | 1 (por omisión) | Despacho del Outbox dentro de la petición; con 0 solo lo despacha el trabajador |
| `EVENTOSNOVA_ENTORNO` | local | produccion | En producción: cookie Secure, HSTS, autenticación obligatoria y /docs oculto salvo EVENTOSNOVA_DOCS=1 |
| `EVENTOSNOVA_AUTENTICACION` | activa | Solo en local y pruebas puede desactivarse; nunca con datos reales |
| `EVENTOSNOVA_COOKIE_SEGURA` | 0 local / 1 con HTTPS | Cookie Secure (obligatoria en producción) |
| `EVENTOSNOVA_SESION_INACTIVIDAD_MIN` | 30 | Caducidad por inactividad |
| `EVENTOSNOVA_SESION_DURACION_HORAS` | 8 | Caducidad absoluta |
| `EVENTOSNOVA_LOGIN_MAX_INTENTOS` | 5 | Fallos por correo e IP antes del bloqueo |
| `EVENTOSNOVA_LOGIN_BLOQUEO_MIN` | 15 | Minutos de bloqueo |
| `EVENTOSNOVA_DOCS` | 1 local / 0 producción por omisión | Publica /docs, /redoc y /openapi.json |
| `EVENTOSNOVA_ORIGENES_PERMITIDOS` | (vacía) | Orígenes adicionales aceptados en operaciones de escritura |
| `FORWARDED_ALLOW_IPS` | * (en render.yaml) | Uvicorn confía en X-Forwarded-Proto/For del proxy TLS de la plataforma |
| `PORT` | (la inyecta la plataforma) | Puerto de escucha del contenedor; 8000 si no existe |

Verificación de secretos: `.env.example` contiene solo marcadores; `ci.yml` usa el valor fijo `ci_clave_efimera` para una base PostgreSQL que solo existe durante el job (no es un secreto de la aplicación; se conserva igual que en el repositorio para que el archivo funcione si se reintegra). El paquete del 03/11/2026 lo había sustituido por `<CLAVE_EFIMERA_CI>`.
Nota: desde HEAD, el comentario de `.env.example` ya explica D-P3 (la fuente de disponibilidad por archivo no puede activarse y la aplicación no arranca si `EVENTOSNOVA_DISPONIBILIDAD_ARCHIVO` está definida).

## Imagen Docker (actualización del 05/11/2026)

| Etapa | Uso |
|---|---|
| `app` | Imagen de la API (python:3.13-slim, usuario no root `eventosnova`, uid 10001, `CMD uvicorn` con `${PORT:-8000}`) |
| `tests` | Suite `unittest`; la usa el servicio `tests` de Compose |
| `runtime` | Etapa **final y predeterminada** (`FROM app`, commit `7aee2cb`): es la que construye `docker build` sin `--target` y la que construirá Render. Debe seguir siendo la última etapa |

## Render (`render.yaml`, preparado y sin aplicar; ver `docs/manuales/GUIA_DESPLIEGUE_RENDER.md`)

| Recurso | Configuración |
|---|---|
| `eventosnova-db` | PostgreSQL gestionado, `postgresMajorVersion: "18"`, plan `0.1c-256mb`, región `ohio`, disco de 1 GB, sin acceso externo (`ipAllowList: []`) |
| `eventosnova-api` | Docker, región `ohio`, plan `0.5c-512mb`, `autoDeployTrigger: checksPass`, `healthCheckPath: /ready`, `preDeployCommand: python -m alembic upgrade head`; variables `DATABASE_URL` (fromDatabase), `EVENTOSNOVA_PERSISTENCIA=postgresql`, `EVENTOSNOVA_ENTORNO=produccion`, `FORWARDED_ALLOW_IPS=*` |
| `eventosnova-worker` | Docker, región `ohio`, plan `0.5c-512mb`, `python -m infrastructure.persistencia.trabajador_outbox --intervalo 2 --espera-esquema 900` (espera, sin migrar, a que la API aplique las migraciones), mismas variables de base y entorno |

`EVENTOSNOVA_DOCS=1` no está en `render.yaml`: se define a mano en el panel solo si se quiere Swagger en la demostración. **Render no está desplegado y no hay URL pública** (05/11/2026). El Bloque A no añadió variables de entorno.
