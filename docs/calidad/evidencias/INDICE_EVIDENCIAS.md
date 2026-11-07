# Índice de evidencias de Eventos Nova

Organizado el 03/11/2026 por tipo de prueba y actualizado el 05/11/2026 (Bloque A). Los archivos se copiaron sin modificar desde el paquete de fuentes; su procedencia y SHA-256 están en `INDICE_EVIDENCIAS.xlsx`. No se inventaron capturas. Los registros históricos no vigentes (ejecuciones y coberturas anteriores al 03/11/2026) no forman parte del paquete final.

| Carpeta | Contenido | Archivos | Vigencia |
|---|---|---|---|
| `01_AUTOMATIZADAS_MEDICION_20261103/` | Registros de la medición: 8 grupos, consola, reporte y verificación del 80 % | 12 | Vigente |
| `02_INTERFAZ_CAPTURAS_AUTOMATICAS/` | Capturas automáticas de la interfaz (ingreso, paneles, diálogos, menú) | 10 | Vigente; no sustituye la prueba manual |
| `03_PAQUETE_OFICIAL_F2/` | Resultados del paquete oficial del PIA (120 casos, 20 transiciones) | 6 | Vigente |
| `05_PRUEBAS_MANUALES/administrador/` | Capturas de los casos A-01 a A-22 (Guía de pruebas manuales). | 0 | Pendiente |
| `05_PRUEBAS_MANUALES/coordinador/` | Capturas de los casos C-01 a C-24. | 0 | Pendiente |
| `05_PRUEBAS_MANUALES/proveedor/` | Capturas de los casos P-01 a P-12. | 0 | Pendiente |
| `05_PRUEBAS_MANUALES/transversal/` | Capturas de los casos T-01 a T-11. | 0 | Pendiente |
| `05_PRUEBAS_MANUALES/swagger_T14_T24/` | Capturas de Swagger de T-14 a T-24 que conserva el equipo. | 0 | Pendiente |
| `06_CI_CD/` | URL y número de la ejecución de CI, captura de los jobs «pruebas» y «docker» en verde y artefacto coverage.json. | 0 | Pendiente (la ejecución vigente es la 42268272652; falta guardar su captura y su `coverage.json`) |
| `08_BLOQUE_A_CHROME/` | Capturas del recorrido en Chrome del Bloque A: búsqueda y filtros de cuentas, advertencia de excedente, precarga del cambio y vista del proveedor sin condiciones (1440 y 390 px) | 5 | Vigente (05/11/2026) |
| `07_DESPLIEGUE/` | URL pública, capturas de /health, /ready y /docs en producción, registro del preDeploy y del worker, commit o etiqueta desplegada. | 5 (`capturas_20261106/`) | Parcial (06/11/2026): hay capturas reales de /docs, /redoc, /health, /ready y /app/; faltan registros del preDeploy y del worker y la captura del commit desplegado en el Dashboard Pendiente |



## Actualización del 05/11/2026

- CI: existen ejecuciones correctas sobre `main` (`4be166b`: 1,654 pruebas; run 41901496391), sobre el commit `9c72bc7` de la PR #2 (1,677 pruebas; run 42104865505) y sobre `main` tras la fusión (`0b16cf3`; 1,677 pruebas; run 42109720404; cobertura 98.21 %), pero sus capturas y artefactos **no se entregaron** en las fuentes: `06_CI_CD/` sigue pendiente.
- Despliegue: *(estado del 05/11/2026; ver la actualización del 06/11/2026 más abajo)* Render no estaba desplegado.
- Las 5 capturas del Bloque A son del entorno manual (127.0.0.1:8001) con datos de prueba.


## Actualización del 06/11/2026

- Despliegue: Render tiene desplegados `eventosnova-api` y `eventosnova-worker` (más la base `eventosnova-db`). GitHub registra el despliegue del commit `1dfcfdd` en ambos servicios con estado `success` (consulta del 06/11/2026). Swagger UI, ReDoc y OpenAPI responden 200 en <https://eventosnova-api.onrender.com/docs>, `/redoc` y `/openapi.json`; `/health`, `/ready` y `/app/` también responden 200.
- Capturas reales de producción, tomadas el 06/11/2026 con Edge sin cabeza, solo con GET y sin sesión: `07_DESPLIEGUE/capturas_20261106/` (`07-01` a `07-05`). No muestran la barra de direcciones; la URL consta en esta nota y en el nombre del archivo.
- CI vigente: ejecución 42268272652 sobre `main` (`1dfcfdd`): los dos trabajos aprobados; 1,787 pruebas; cobertura de sentencias 98.12 % (6,751 de 6,880), ramas 93.36 %, TOTAL combinado 97.3 %. Su captura y su `coverage.json` **siguen sin archivarse** en `06_CI_CD/`.
- **Pendiente (no verificado):** registros recientes del Worker, estado del Outbox, estado de los servicios en el Dashboard de Render, capturas de la aplicación con sesión por rol, capturas de Swagger autenticado (200, 401 y 403) y capturas de los eventos CL-DEMO-01, 02 y 03. La lista numerada está en `docs/INFORME_CIERRE_PIA_20261106.md`, sección 6.
- Nuevas carpetas de evidencia del 06/11/2026 (todas reales, ninguna ilustrativa):
  - `06_CI_CD/capturas_20261106/04_actions_ci_verde_1dfcfdd_20261106.png`: resumen de la ejecución de CI sobre `1dfcfdd` con los dos trabajos en verde. La página muestra «2 errors» en *Annotations*: son mensajes «fallo técnico simulado» que escribe a propósito la prueba `tests/test_d3_llegada_de_t.py` (línea 174, simula un fallo con `mock`); no son fallos del CI.
  - `09_DOCKER_COMPOSE/docker_compose_20261106.txt`: comandos y resultados reales de Docker Compose local (configuración válida; `db`, `api` y `worker` activos; `/ready` 200; suite en contenedor: 1,787 pruebas OK, 9 omitidas, contra la base `eventosnova_test`; nota sobre errores transitorios de arranque del worker).
  - `11_GITHUB/capturas_20261106/`: `02_github_prs_fusionadas_20261106.png` (PR #1 a #8 cerradas y fusionadas) y `03_github_commits_main_20261106.png` (commits de `main`, con `1dfcfdd` a la cabeza). Las capturas de la estructura del repositorio (`01`) y de `.env.example` (`12`) **siguen pendientes**.
