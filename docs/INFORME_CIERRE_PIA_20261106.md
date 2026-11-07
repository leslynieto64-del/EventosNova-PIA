# Informe de cierre del PIA — Eventos Nova (2026-11-06)

Documento nuevo, de **solo lectura sobre el sistema**: no modifica la aplicación, los permisos, Render ni los workflows, y no sustituye ningún documento existente. Las correcciones que propone **no están aplicadas**: esperan autorización (sección 12).

Referencia obligatoria: `PIA_CLN_Proyecto_Integrador_AD2026.pdf` (carpeta `PAQUETE_FUENTES_EVENTOS_NOVA/00_PIA_Y_CRITERIOS/criterios_PIA/`). Origen de los datos: **[E]** observado por mí en esta sesión; **[G]** consultado en GitHub; **[U]** informado por la persona usuaria; **[D]** comprobado en un archivo del repositorio.

> **Fecha límite (según el PDF): entrega de documentos y repositorio el 06 de noviembre de 2026; defensa del 9 al 20 de noviembre.** «No se aceptarán proyectos después de la fecha de entrega.» Es el riesgo principal (sección 11).

## 1. Verificaciones completadas
| Verificación | Resultado |
|---|---|
| `.env.example` existe, está versionado y no tiene secretos | **Sí** [D][E]. Raíz del repositorio, rastreado por Git. Contraseñas de ejemplo con el valor `cambiar_esta_contrasena`; las variables de Render/seguridad están como comentarios |
| `.env` excluido | **Sí**: `.gitignore` línea 5; ningún `.env` está rastreado [E] |
| Credenciales en archivos versionados | **No se encontraron** claves privadas, tokens (`ghp_`, `github_pat_`, `AKIA`, `xox`, `sk-`) ni URLs de base de datos con contraseña real entre los 649 archivos rastreados [E]. Solo aparecen contraseñas ficticias de prueba en scripts de navegador (`scripts/probar_*_navegador.mjs`) y pruebas (`tests/test_seguridad.py`, `tests/test_decisiones_s1_s9.py`): variable `contrasena`, valor tipo `una-contrasena-larga-1`. Riesgo bajo |
| Estructura mínima del PDF | **Completa**: `docs/BRD.md`, `docs/architecture/`, `docs/api/`, `src/domain|application|infrastructure|api/`, `tests/`, `.github/workflows/`, `docker-compose.yml`, `.env.example`, `README.md` [E]. No hay equivalencias que documentar |
| CI sobre `1dfcfdd` | Ejecución 42268272652: los dos trabajos aprobados; **1 787 pruebas**; cobertura de sentencias **98,12 %** (6 751 de 6 880), ramas **93,36 %**, TOTAL combinado 97,3 %; mínimo del PIA 80 % [G] |
| Docker Compose | `docker compose config -q` sin errores (sintaxis válida) [E]. El trabajo «Docker Compose (DB + App + Tests)» del CI pasó (construye imágenes, ejecuta la suite en contenedor y comprueba `/ready`, `/health` y `/docs`) [G] |
| Producción (solo GET, sin sesión) | `/docs`, `/redoc`, `/openapi.json`, `/health`, `/ready`, `/app/` → 200; 77 operaciones; `/auth/yo` y `POST /eventos` sin sesión → 401 en español [E] |
| Capturas reales de producción | 5 capturas nuevas (sección 5) [E] |
| Secreto `DEPLOY_HOOK_URL` | Existe (creado hoy); lo lee solo `publicar-imagen.yml` (etiqueta `v*` o ejecución manual); Render no consume la imagen y ya despliega solo. **No se ejecutó** ese workflow [G] |

**Pruebas locales de esta sesión.** No se ejecutó la suite completa con PostgreSQL: el equipo no tiene PostgreSQL ni el motor de Docker activo (Docker Desktop está instalado pero apagado). La suite corrió antes sin PostgreSQL (1 427 pruebas, 49 omitidas, solo falla el artefacto `src.ejecucion_paquete`, que ya fallaba en `main`). No se modificaron datos.

## 2. Verificaciones pendientes
| Pendiente | Motivo |
|---|---|
| Estado de `eventosnova-api` y `eventosnova-worker` en Render, reinicios y registros posteriores a `1dfcfdd` | No hay acceso al Dashboard ni a la CLI de Render. **No se simula ningún resultado.** Lo único objetivo: GitHub registra ambos despliegues de `1dfcfdd` como `success` [G] |
| Estados del Outbox (`SELECT estado, COUNT(*) FROM outbox_evento GROUP BY estado;`) | Requiere el Shell de Render o la base; ninguna ruta de la API lo expone. Pasos manuales en la sección 2.1 |
| Comprobación de Docker Compose en este equipo | El motor de Docker está apagado; arrancarlo y levantar contenedores toca volúmenes de desarrollo. Queda cubierto por el CI, no por una ejecución local |
| Información visible por rol, estados de CL-DEMO-01/02/03, datos del proveedor y asignaciones **en producción** | Requiere sesión; no hay credenciales y no se piden por el chat. Solo hay confirmación [U] de que administrador y coordinador entraron y de que el proveedor vio su asignación |
| Defensa técnica y presentación en vivo | No verificable de forma previa |

### 2.1 Lo que debes consultar tú en Render (solo lectura)
1. Dashboard → `eventosnova-worker` → *Logs*: filtra desde el despliegue de `1dfcfdd` (18:15 UTC del 06/11). Busca «ERROR», «Traceback», reinicios y mensajes de conexión. **Captura** con el estado *Live* visible. Nombre: `07-06_render_worker_logs_20261106.png`.
2. Dashboard → `eventosnova-api` → *Events* (o *Deploys*): captura que muestre el commit `1dfcfdd` y *Live*. Nombre: `07-07_render_api_deploy_1dfcfdd.png`. Repite para el Worker: `07-08_render_worker_deploy_1dfcfdd.png`.
3. Shell de `eventosnova-api` (solo lectura): `SELECT estado, COUNT(*) FROM outbox_evento GROUP BY estado;`. Esperado: solo `PROCESADO`. Captura: `07-09_outbox_estados.png`. Oculta cualquier cadena de conexión.
4. Settings de `eventosnova-api`: confirma que `EVENTOSNOVA_DOCS=1` existe (**oculta su valor si hubiera otros secretos en pantalla**) y que Auto-Deploy dice *After CI Checks Pass*. Captura: `07-10_render_api_config.png`, sin la sección de variables que muestre secretos.

## 3. Problemas encontrados
1. **`README.md` sin la URL del sistema desplegado.** El PDF pide expresamente «colocar en el README la URL del repositorio y del sistema desplegado». No aparece ninguna URL de Render [D].
2. **URL del repositorio desactualizada** en `README.md` (líneas 23 y 34), `docs/architecture/ci-cd-y-despliegue.md`, `docs/documentacion_final/LEEME.md` y `docs/manuales/GUIA_DESPLIEGUE_RENDER.md`: `github.com/leslynieto64-del/EventosNova-PIA`. El repositorio real es `https://github.com/leslynieto64-del/eventos-nova-cln` (público, rama `main`); la URL antigua redirige hoy porque se renombró, pero no es la canónica [G].
3. **Cifras de calidad desactualizadas en `README.md`:** declara 98,21 % y 1 677 pruebas (CI de `9c72bc7` y `0b16cf3`). El CI vigente sobre `1dfcfdd` es 98,12 % de sentencias, 93,36 % de ramas y 1 787 pruebas [G].
4. **`docs/calidad/evidencias/INDICE_EVIDENCIAS.md`** dice «Render no está desplegado» y deja `06_CI_CD/` y `07_DESPLIEGUE/` como pendientes. Hoy ya existe el despliegue y ya hay capturas de producción (sección 5) [D].
5. **Reporte final PDF y presentación desactualizados:** `docs/entrega/Reporte_Final_PIA_Eventos_Nova.pdf` y `Presentacion_Defensa_Eventos_Nova.pptx` son del 29/10/2026, no mencionan Render ni la URL pública (0 coincidencias) y son anteriores a las PR #2 a #8 [D][E].
6. **Archivos sin versionar.** Varios documentos de cierre y la carpeta `docs/entrega/` están sin seguimiento en Git; el PDF exige que el repositorio corresponda a la versión presentada [E].
7. **Historial de commits:** 60 commits desde el 2026-10-19; 52 de un solo autor (`Lesly`) y 8 fusiones de GitHub. El PDF pide «historial de commits del equipo»; si la rúbrica espera varias personas, habría que explicarlo [E].
8. **Dato cosmético:** `scripts/sembrar_datos_demo.py` (línea 1004) usa en su ayuda el ejemplo `eventosnova.onrender.com`, que no es el dominio real (`eventosnova-api.onrender.com`). No afecta la ejecución.
9. **Worker/Outbox sin verificación posterior a la siembra** (sección 2).

## 4. Correcciones necesarias (propuestas, no aplicadas)
| # | Archivo | Cambio |
|---|---|---|
| C1 | `README.md` | Añadir tabla de enlaces verificados (sección 8) con URL del repositorio, aplicación, Swagger, ReDoc y OpenAPI |
| C2 | `README.md` y otros 3 documentos | Sustituir la URL antigua del repositorio por la canónica |
| C3 | `README.md` | Actualizar la fila de CI/cobertura al run 42268272652 sobre `1dfcfdd` (1 787 pruebas; 98,12 % / 93,36 %; combinado 97,3 %) y añadir PR #6, #7 y #8 |
| C4 | `docs/calidad/evidencias/INDICE_EVIDENCIAS.md` | Registrar las capturas de `07_DESPLIEGUE/capturas_20261106/`, el run de CI y la ejecución verificada |
| C5 | Reporte final PDF y presentación | Regenerarlos con URL pública, Swagger, resultados del CI, cobertura y evidencias. Requiere el entorno temporal de generación (`C:\pia_env_tmp`) |
| C6 | Git | Versionar el reporte de Render, este informe y las capturas nuevas (solo con tu autorización) |

## 5. Evidencias existentes e inventario de capturas
**Nuevas, tomadas hoy con Edge sin cabeza, solo GET, sin sesión [E]** — carpeta `docs/calidad/evidencias/07_DESPLIEGUE/capturas_20261106/`:
| Archivo | Contenido | Estado |
|---|---|---|
| `07-01_swagger_docs_produccion_20261106.png` | Swagger UI de `https://eventosnova-api.onrender.com/docs`: «Eventos Nova API 0.1.0 OAS 3.1», botón Authorize, operaciones por grupo | Correcta, reutilizable |
| `07-02_redoc_produccion_20261106.png` | ReDoc de `/redoc` | Correcta, reutilizable |
| `07-03_health_produccion_20261106.png` | `/health` | Correcta |
| `07-04_ready_produccion_20261106.png` | `/ready`: `{"estado":"ok","persistencia":"postgresql","base_de_datos":"ok"}` | Correcta |
| `07-05_app_ingreso_produccion_20261106.png` | Pantalla de ingreso de `/app/` | Correcta |

No muestran la barra de direcciones (modo sin cabeza): la URL consta en el nombre del archivo y en esta tabla. Para la entrega conviene volver a tomar 07-01 con el navegador normal, de modo que se vea la URL.

**Clasificación del resto del inventario**
| Clase | Elementos |
|---|---|
| Correctas y reutilizables | Registros de cobertura y consola del 03/11 (`docs/calidad/evidencias/01_*`); artefacto `coverage.json` del run 42268272652 (descargado en el scratchpad de la sesión, fuera del repositorio) [G]; 13 capturas automáticas de interfaz en `tests/evidencias/pruebas_manuales_web/_automaticas/` (locales, no sustituyen la prueba manual); 5 capturas del Bloque A (entorno manual, no producción) |
| Desactualizadas | `docs/entrega/Reporte_Final_PIA_Eventos_Nova.pdf` y `Presentacion_Defensa_Eventos_Nova.pptx` (29/10); `INDICE_EVIDENCIAS.md` (dice «Render no está desplegado»); cifras del README |
| Incompletas | `05_PRUEBAS_MANUALES/` (administrador, coordinador, proveedor, transversal, Swagger T-14 a T-24): solo `.md`, 0 capturas; `06_CI_CD/` y `07_DESPLIEGUE/` solo con `LEEME_PENDIENTE.md` (esta última ahora tiene las 5 capturas nuevas) |
| Faltantes | Lista de la sección 6 |

## 6. Capturas que todavía necesitas tomar
Todas con sesión real y datos de demostración; **oculta** contraseñas, cookies, tokens, cadenas de conexión y el valor de cualquier variable de entorno.
| N.º | Pantalla y ruta | Qué debe verse | Archivo sugerido |
|---|---|---|---|
| 1 | GitHub → `https://github.com/leslynieto64-del/eventos-nova-cln` | Estructura de carpetas, README, rama `main` | `01_github_repositorio_estructura.png` |
| 2 | GitHub → Pull requests → Closed (#6, #7, #8) | Las tres fusionadas | `02_github_prs_fusionadas.png` |
| 3 | GitHub → Commits de `main` | `1dfcfdd` y los anteriores, con autor y fecha | `03_github_commits_main.png` |
| 4 | Actions → CI → ejecución 42268272652 | Los dos trabajos en verde sobre `1dfcfdd` | `04_actions_ci_verde_1dfcfdd.png` |
| 5 | Esa ejecución → paso «Cobertura mínima del PIA» | «Cobertura de sentencias: 98.12 %… OK: cumple el mínimo de 80 %» | `05_cobertura_98_12.png` |
| 6 | Esa ejecución → trabajo «Docker Compose» | Construcción, pruebas y comprobaciones en verde | `06_actions_docker_compose.png` |
| 7 | Terminal local: `docker compose ps` | Servicios `db` y `app` (y `trabajador`, si aplica) sanos | `07_docker_compose_ps.png` |
| 8 | Render → `eventosnova-api` y `eventosnova-worker` | Estado *Live*, commit `1dfcfdd` (secciones 2.1.1 a 2.1.4) | `07-06` a `07-10` |
| 9 | `https://eventosnova-api.onrender.com/app/` con cada rol | Panel del administrador, del coordinador y del proveedor (una por rol, mostrando el rol en pantalla) | `09_app_admin.png`, `09_app_coordinador.png`, `09_app_proveedor.png` |
| 10 | `/docs` con sesión | `GET /proveedores` → 200 con el aviso «Información…»; un 403 por rol (p. ej. coordinador en `GET /usuarios`); un 401 sin sesión | `08_swagger_get_200.png`, `08_swagger_403_rol.png`, `08_swagger_401.png` |
| 11 | `/app/` con coordinador → eventos CL-DEMO-01, 02 y 03 | Estado de cada evento, contrato, anticipo y asignación | `10_demo_cl_demo_01.png`, `…_02.png`, `…_03.png` |
| 12 | `/app/` con proveedor → «Mis asignaciones» | La asignación de Banquete de CL-DEMO-02 (pendiente) y, tras responder en la demostración, el estado nuevo | `10_demo_proveedor_asignacion_pendiente.png` |
| 13 | `.env.example` en GitHub (o editor) | Valores `cambiar_esta_contrasena`, sin secretos | `12_env_example_sin_secretos.png` |

## 7. Demostración funcional (CL-DEMO-01, 02 y 03)
Fuente: archivo de progreso de la siembra [P], `scripts/sembrar_datos_demo.py` [D], `tests/test_sembrar_datos_demo.py` [D] y confirmaciones [U]. **No se hizo ninguna escritura en producción.**
| Elemento | Estado |
|---|---|
| Administrador | Inicio de sesión en producción confirmado [U]; consultas autenticadas y permisos confirmados [U] |
| Coordinador | Consultas autenticadas y permisos confirmados [U]; sin detalle ni capturas |
| Proveedor | Inicio de sesión y visualización de su asignación de CL-DEMO-02 confirmados [U] |
| CL-DEMO-01 | Evento y propuesta sembrados |
| CL-DEMO-02 | Evento, propuesta, aceptación, contrato (política y firma) y anticipo de 3,000.00 MXN sembrados; asignación de Banquete **pendiente de respuesta a propósito** |
| CL-DEMO-03 | Evento, propuesta, aceptación, contrato, anticipo, cancelación y revisión administrativa; pagos 3,000.00, saldo pendiente 7,000.00 |
| ¿CL-DEMO-02 ya fue atendida? | **No consta.** Según la siembra estaba pendiente y [U] indica que se reserva para la demostración; no hay evidencia posterior. Verificarlo requiere iniciar sesión (solo lectura, `GET /mis-asignaciones` como proveedor) |
| Reglas del negocio | Cubiertas por pruebas automatizadas (1 787 en el CI) y por los flujos de la siembra; no auditadas en vivo |

## 8. Enlaces definitivos comprobados
| Recurso | URL | Resultado |
|---|---|---|
| Repositorio (canónica) | https://github.com/leslynieto64-del/eventos-nova-cln | Público, rama `main` [G] |
| Aplicación web | https://eventosnova-api.onrender.com/app/ | 200 [E] |
| Swagger UI | https://eventosnova-api.onrender.com/docs | 200 [E] |
| ReDoc | https://eventosnova-api.onrender.com/redoc | 200 [E] |
| OpenAPI | https://eventosnova-api.onrender.com/openapi.json | 200, 77 operaciones [E] |
| Salud / disponibilidad | https://eventosnova-api.onrender.com/health · `/ready` | 200 [E] |

## 9. Requisitos del PDF
Criterio: **CUMPLE** solo con existencia o funcionamiento comprobados; la calidad del contenido de los documentos no se audita línea por línea.
### Análisis
| Requisito | Estado | Evidencia |
|---|---|---|
| BRD completo | CUMPLE | `docs/BRD.md` (158 líneas) y `docs/analisis/brd/` (DOCX y PDF). Completitud sustantiva no auditada |
| ≥ 15 User Stories | CUMPLE | US-001 a US-033 (33) y CA-001 a CA-114 [D] |
| Criterios en Gherkin | CUMPLE | 10 archivos `.feature`, 132 escenarios (`docs/analisis/gherkin/features/`) [E] |
| BPMN completo | CUMPLE | `diagramas/bpmn/`: proceso principal y subprocesos SP01 a SP05, en `.bpmn`, `.drawio`, PDF, PNG y SVG [E] |
| Glosario de dominio | CUMPLE | `docs/analisis/glosario/` (DOCX y PDF) [D] |
### Arquitectura
| Requisito | Estado | Evidencia |
|---|---|---|
| Diagramas DDD | CUMPLE | `diagramas/dominio/`, `Diagramas_Clases_Eventos_Nova.pdf` |
| Diagramas UML | CUMPLE | `diagramas/clases/`, `diagramas/secuencia/`, 19 archivos PlantUML |
| Patrones justificados y SOLID | PARCIAL | Existe `Patrones_Diseno_SOLID_Eventos_Nova` (DOCX/PDF). La aplicación de SOLID en el código no se auditó; defender con ejemplos concretos |
| ADRs y decisiones técnicas | CUMPLE | `docs/ADR/` (ADR-001 a ADR-011, índice y registro), `Decisiones_Tecnicas_Eventos_Nova`. Estructura contexto/decisión/alternativas/consecuencias no verificada ADR por ADR |
| Estructura de carpetas | CUMPLE | Sección 1 |
| README técnico | **PARCIAL** | Existe con instalación, ejecución y pruebas, pero sin URL del despliegue, con URL antigua del repositorio y cifras viejas (problemas 1 a 3) |
| `.env.example` sin secretos | CUMPLE | Sección 1 |
| Trazabilidad análisis-arquitectura-implementación | CUMPLE | `docs/trazabilidad/` (matriz DOCX, PDF y XLSX), `docs/architecture/trazabilidad-api-persistencia.md`; escenarios etiquetados `@US-… @CA-…`. Alineación no auditada |
| Historial de commits | PARCIAL | 60 commits (2026-10-19 a hoy), pero un solo autor humano |
### Implementación
| Requisito | Estado | Evidencia |
|---|---|---|
| DDD | CUMPLE | `src/domain/` (entidades, valores, eventos de dominio, servicios) |
| Specification | CUMPLE | `src/domain/especificacion.py` y `especificaciones.py` |
| State Machine | CUMPLE | `src/domain/maquina_estados.py` |
| API REST | CUMPLE | 77 operaciones (19 GET, 58 POST), OpenAPI 3.1; en producción [E] |
| Persistencia y base de datos | CUMPLE | PostgreSQL 18 con Alembic 0001–0009; `/ready` en producción: `postgresql`, `base_de_datos: ok` [E] |
| OpenAPI/Swagger | CUMPLE | `docs/api/openapi.json` y Swagger activo en producción [E] |
| Casos de uso principales | CUMPLE (automatizado) / NO VERIFICABLE por mí en producción | Pruebas automatizadas; en producción solo la confirmación [U] |
### Calidad y defensa
| Requisito | Estado | Evidencia |
|---|---|---|
| Pruebas unitarias y de integración | CUMPLE | 1 787 pruebas en el CI, con PostgreSQL [G] |
| Cobertura ≥ 80 % | CUMPLE | 98,12 % de sentencias; 93,36 % de ramas [G] |
| Pipeline CI/CD activo | CUMPLE | `ci.yml` en `push` a `main` y `pull_request`; ejecuciones en verde [G] |
| Docker Compose reproducible (DB + App + Tests) | CUMPLE (por CI) | Trabajo Docker en verde; `docker compose config` válido. No ejecutado localmente hoy |
| Variables de entorno | CUMPLE | `.env.example`; `render.yaml` sin secretos |
| Despliegue funcional | CUMPLE | Render (API y Worker), `/ready` 200 con PostgreSQL |
| Swagger UI/OpenAPI en producción | CUMPLE | 200 en `/docs`, `/redoc` y `/openapi.json`; capturas 07-01 y 07-02 |
| Demostración de reglas y estados | PARCIAL | Datos sembrados; falta el recorrido de roles con capturas y responder CL-DEMO-02 en vivo |
| Defensa técnica | NO VERIFICABLE | Es un acto futuro |
### Entregables
| Requisito | Estado | Evidencia |
|---|---|---|
| Reporte final PDF | PARCIAL | Existe `docs/entrega/Reporte_Final_PIA_Eventos_Nova.pdf` (29/10), pero sin despliegue ni resultados recientes |
| Repositorio GitHub | CUMPLE | Público; `main` = `1dfcfdd`. Falta versionar los archivos sin seguimiento |
| Documentación | CUMPLE | Manuales, API, calidad, ADR, trazabilidad |
| Presentación de apoyo | PARCIAL | `Presentacion_Defensa_Eventos_Nova.pptx` (29/10), desactualizada |
| URL del despliegue | CUMPLE (verificada) | https://eventosnova-api.onrender.com; **falta en el README** |

## 10. Documentos revisados y modificados
- **Revisados (sin cambios):** `.env.example`, `.gitignore`, `README.md`, `render.yaml`, `docker-compose.yml`, los tres workflows, `docs/BRD.md`, `docs/ADR/`, `docs/analisis/`, `docs/trazabilidad/`, `docs/calidad/evidencias/`, `docs/entrega/`, `docs/manuales/`, el PDF de la actividad y `scripts/sembrar_datos_demo.py`.
- **Creados (nuevos, sin sobrescribir nada):**
  - `docs/INFORME_CIERRE_PIA_20261106.md` (este documento).
  - Cinco capturas reales en `docs/calidad/evidencias/07_DESPLIEGUE/capturas_20261106/`.
- **Ya existente y actualizado antes:** `docs/REPORTE_FINAL_DESPLIEGUE_RENDER.md` (sigue pendiente de aprobación).
- **No modificados, a la espera de autorización:** `README.md`, `INDICE_EVIDENCIAS.md`, los demás documentos con la URL antigua, el reporte PDF y la presentación.

## 11. Riesgos antes de la entrega
1. **Plazo: el PDF fija hoy (06/11/2026) para documentos y repositorio.** Sin versionar lo pendiente, el repositorio no corresponde a la versión presentada.
2. **README incompleto** (sin URL del despliegue): incumple una instrucción expresa del PDF.
3. **Reporte final y presentación desactualizados** respecto al despliegue.
4. **Un solo autor en el historial.**
5. **Sin verificación del Worker ni del Outbox** tras las últimas fusiones.
6. **Demostración:** CL-DEMO-02 sigue pendiente a propósito; conviene ensayarla antes de la defensa. Si el servicio de Render estuviera en un plan que se suspende por inactividad, la primera carga podría tardar: conviene abrirlo unos minutos antes de la defensa (el plan vigente no se verificó en el Dashboard).
7. **Secreto `DEPLOY_HOOK_URL`** presente sin uso: no es un riesgo técnico; si la rúbrica lo exige, el workflow nunca se ha ejecutado y publicaría en GHCR sin compuerta de CI.

## 12. Acciones que requieren tu autorización
1. Aplicar C1 a C4 (README, URL canónica en 4 documentos, índice de evidencias).
2. Regenerar el reporte final PDF y la presentación (C5).
3. Hacer commit y push de los archivos sin versionar (informe, reporte de Render, capturas), por una rama y PR, con identidad Lesly y sin `git add .` (C6).
4. Iniciar sesión yo mismo en producción para una verificación de solo lectura (necesitaría que tú escribas las credenciales en una terminal oculta, no en el chat).
5. Levantar Docker Desktop y Docker Compose localmente para una ejecución real de la suite.
6. Ejecutar una vez `publicar-imagen.yml` (publica en GHCR y redespliega la API) si la rúbrica lo exige.
7. Responder CL-DEMO-02 como proveedor (escritura en producción), solo durante la demostración.

## 13. Actualización posterior a la autorización (06/11/2026, tarde)
**Correcciones documentales aplicadas** (copias de los originales en `scratchpad/respaldo_docs_20261106/`, carpeta ignorada por Git; además Git conserva los originales):
| Archivo | Cambio |
|---|---|
| `README.md` | URL canónica del repositorio; URL de la aplicación, de Swagger, de OpenAPI y de `/health` y `/ready` (comprobadas hoy); estado del código y del despliegue actualizados; nueva fila de CI vigente (run 42268272652: 1,787 pruebas, sentencias 98.12 %, ramas 93.36 %, combinado 97.3 %); pendientes reescritos sin afirmar lo no verificado |
| `docs/calidad/evidencias/INDICE_EVIDENCIAS.md` | Corregido «Render no está desplegado»; filas `06_CI_CD` y `07_DESPLIEGUE`; notas del 06/11 con lo pendiente |
| `docs/architecture/ci-cd-y-despliegue.md`, `docs/documentacion_final/LEEME.md` | URL antigua del repositorio sustituida |
| `docs/manuales/GUIA_DESPLIEGUE_RENDER.md` | Nombre del repositorio en los pasos 1 y 2 |
No se modificó código de la aplicación. Quedan con la URL antigua los PDF/DOCX ya generados (p. ej. `docs/informe/informe-arquitectura-eventos-nova.pdf`): se corrigen al regenerarlos. `scripts/sembrar_datos_demo.py` conserva en su texto de ayuda un dominio de ejemplo (`eventosnova.onrender.com`) porque es código y no se tocó.

**Docker Compose local** (evidencia en `docs/calidad/evidencias/09_DOCKER_COMPOSE/docker_compose_20261106.txt`):
| Comando | Resultado |
|---|---|
| `docker compose config -q` | Sin errores |
| Arranque de Docker Desktop | Los contenedores existentes arrancaron solos (política `unless-stopped`): `eventosnova-db` (healthy), `eventosnova-api-1` (healthy) y `eventosnova-worker-1` |
| `curl http://127.0.0.1:8000/ready` | `{"estado":"ok","persistencia":"postgresql","base_de_datos":"ok"}`, HTTP 200 |
| `docker compose run --rm --build tests` | **1,787 pruebas, OK, 9 omitidas** (1,129 s), contra `eventosnova_test`; coincide con el trabajo Docker del CI |
| Worker local | Al arrancar Docker registró errores transitorios «failed to resolve host 'db'» y se reinició 3 veces; luego estable. Es una condición de arranque, no un defecto de las pruebas |
No se ejecutó `docker compose up` completo ni el servicio `migrate`, para no migrar la base de desarrollo `eventosnova`; las pruebas solo escriben en `eventosnova_test`. Los contenedores `db`, `api` y `worker` quedaron **en ejecución**; deténlos con `docker compose stop` (nunca con `down -v`) si no los necesitas.

**Capturas obtenidas hoy (reales):** `07_DESPLIEGUE/capturas_20261106/07-01` a `07-05` (producción), `06_CI_CD/capturas_20261106/04_…` (CI), `11_GITHUB/capturas_20261106/02_…` y `03_…` (PR y commits) y el texto de Docker Compose. **No se obtuvieron** la estructura del repositorio (`01`) ni `.env.example` en GitHub (`12`): Edge sin cabeza no completó esas páginas. Siguen pendientes, junto con las que requieren sesión o el Dashboard de Render (sección 6, números 5 a 13 y 2.1).

**Enlaces públicos verificados hoy:** repositorio, `/app/`, `/docs`, `/redoc`, `/openapi.json`, `/health` y `/ready`, todos con respuesta 200.
