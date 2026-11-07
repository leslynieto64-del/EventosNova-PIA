# Preparación para GitHub y Render

Estado a la fecha de este documento: **nada se ha subido ni desplegado.** No hay commit, push, merge ni despliegue; el trabajo está en la rama `fix/auditoria-integral`, solo en el directorio de trabajo.

## 1. Revisión previa a GitHub

| Verificación | Resultado |
|---|---|
| `.env`, backups y archivo de credenciales de pruebas están ignorados (`.gitignore`) | Correcto: `.env`, `backups/` y `scratchpad/credenciales_pruebas_manual.txt` figuran como ignorados |
| Archivos versionados con nombres sensibles (`.env`, credenciales, `.bak`, `.dump`, `.pem`, `.key`, `.sql`) | Ninguno |
| Búsqueda de contraseñas, claves privadas, hashes (`$argon2`, `$2b$`) y URLs de base con contraseña en los archivos modificados y nuevos | Sin coincidencias |
| Correcciones locales previas (C-03, formulario de cuentas) | Presentes y completas (el parche de respaldo se aplica en reversa sin conflictos) |
| Cambios de esta etapa | Solo presentación y la limitación de datos que la API devuelve al proveedor (COR-05); sin migraciones ni cambios de esquema |
| Variables de entorno nuevas | Ninguna (el cambio de COR-08 que las requería se revirtió) |

### Archivos sin seguimiento que hay que decidir antes del commit
Existían antes de esta etapa y **no los modifiqué**; decide si se versionan:

- Raíz: `INFORME_CIERRE_FASE_1_EVENTOS_NOVA.md`, `INFORME_FINAL_VALIDACION_DOCUMENTAL.md`, `LEEME_REVISION.txt`, `MANIFIESTO_SHA256.txt`, `NOTA_DE_ENTREGA.md`. El manifiesto de hashes quedará desactualizado en cuanto cambie cualquier archivo.
- `docs/INFORME_SINCRONIZACION_DOCUMENTAL_20261023.md` y `docs/entrega/`.
- `tests/evidencias/pruebas_manuales_web/_automaticas/*.png`: son capturas de pantalla; **revísalas antes de publicarlas** por si muestran correos o nombres reales.
- Para C-03: `tests/test_interfaz_formulario_cuentas.py` y `scripts/probar_formulario_cuentas_navegador.mjs` (deben versionarse).
- Documentos nuevos de esta etapa: los cuatro de `docs/` indicados en el reporte final.

## 2. Coherencia Docker / Render

`render.yaml` (borrador sin aplicar) y `Dockerfile` son coherentes:

- API web con `runtime: docker`, etapa final `runtime`, `healthCheckPath: /ready`, migraciones con `preDeployCommand: python -m alembic upgrade head`.
- Worker del Outbox con `python -m infrastructure.persistencia.trabajador_outbox --intervalo 2`.
- PostgreSQL 18 gestionado; `DATABASE_URL` se inyecta con `fromDatabase` (nunca está en el repositorio).
- El frontend lo sirve la propia API en `/app/`; no hay un servicio de frontend aparte.
- `EVENTOSNOVA_ENTORNO=produccion` activa cookie Secure, HSTS, autenticación obligatoria y oculta `/docs`.
- `FORWARDED_ALLOW_IPS=*` para confiar en el proxy TLS de Render.
- Imagen de pruebas manuales construida desde esa misma etapa (`eventosnova-app:cierre-integral`), con `/health`, `/ready`, `/app/` y `/docs` respondiendo 200 y Alembic en 0009.

### Variables de entorno
| Variable | Dónde | Valor |
|---|---|---|
| `DATABASE_URL` | API y worker | La inyecta Render desde la base |
| `EVENTOSNOVA_PERSISTENCIA` | API y worker | `postgresql` |
| `EVENTOSNOVA_ENTORNO` | API y worker | `produccion` |
| `FORWARDED_ALLOW_IPS` | API | `*` |
| `EVENTOSNOVA_DOCS` | API (a mano en el panel) | `1` solo si se quiere Swagger en la demostración |

La región debe ser la misma para la base, la API y el worker (se elige al crear cada recurso).

## 3. Pasos que requieren tu acción (no los hice)

1. Decidir qué archivos sin seguimiento se versionan (sección 1) y revisar las capturas.
2. Hacer el commit y el push de la rama (autorizas tú).
3. Crear la cuenta de Render y conectar el repositorio. **Los planes de la base y de los servicios tienen costo** (el plan gratuito de la base caduca y el de los servicios se duerme); necesita tu aprobación y una tarjeta. No contraté nada.
4. Revisar en https://render.com/pricing que los identificadores de plan de `render.yaml` sigan vigentes.
5. Aplicar el blueprint y, tras el primer despliegue, crear la primera cuenta de Administración con `scripts/crear_administrador.py` (ver `docs/SEGURIDAD_Y_PERMISOS.md`, «Primer administrador»; la base nueva no tiene usuarios ni credenciales predeterminadas).
6. Comprobar `/health`, `/ready` y el inicio de sesión por HTTPS, y que el worker procesa el Outbox.
7. Si se quiere Swagger en la demostración, definir `EVENTOSNOVA_DOCS=1` a mano.

## 4. Lo que no se hizo
- No se aplicó ninguna migración al entorno normal (`eventosnova`, revisión 0004) ni se tocaron los contenedores del puerto 8000.
- No se hizo commit, push, merge ni despliegue.
