# Eventos Nova — Documentación final del PIA

Equipo 16 · Componentes de Lógica de Negocios · Prof. Miguel Ángel Gómez Marroquín  
Lesly Adamaris Cotlame Nieto (2226958) · Christopher Bethancourt Contreras (2226948) · Francisco Mora Ruiz (2226912)

Entrega oficial del PIA: 06/11/2026. Repositorio: <https://github.com/leslynieto64-del/eventos-nova-cln> (`main` con 37 commits: la Pull Request #2 —Bloque A, 11 commits— se fusionó el 05/11/2026 con un merge commit, `0b16cf3`; el CI de `main` terminó correctamente). El sistema no está desplegado.

## Estructura

| Carpeta | Contenido |
|---|---|
| `01_ANALISIS/` | BRD v2.0, historias de usuario v2.0 (con la matriz de trazabilidad BN-US-CA-BPMN), especificación Gherkin y 10 archivos `.feature`, BPMN (maestro y SP01 a SP10: editables y exportaciones) y glosario v2.0 |
| `02_ARQUITECTURA/` | Mapa DDD, diagramas UML de clases y de secuencia, arquitectura, modelo relacional, patrones y SOLID, registro ADR e índice (11 ADR en tablas), decisiones técnicas y matriz de trazabilidad (Excel, Word y PDF) |
| `03_IMPLEMENTACION/` | Manual técnico, OpenAPI y documentación de la API, README, CI, CD y despliegue, diagrama CI/CD, Docker y variables (sin `.env`), repositorio, manuales de instalación y de usuario, seguridad |
| `04_CALIDAD_Y_PRUEBAS/` | Guía de pruebas manuales, informe general de pruebas, evidencias vigentes (con índice), reporte de cobertura y matriz de roles y permisos |
| `05_ENTREGA_Y_DEFENSA/` | Reporte final y presentación de defensa (17 diapositivas), cada uno con su PDF |

## Inventario breve de documentos

| Documento | PDF |
|---|---|
| `01_ANALISIS/01_BRD/BRD_Eventos_Nova_Final.docx` | Sí (36 p.) |
| `01_ANALISIS/02_HISTORIAS_USUARIO/Historias_Usuario_Eventos_Nova_Final.docx` | Sí (30 p.) |
| `01_ANALISIS/03_GHERKIN/Especificacion_Gherkin_Eventos_Nova.docx` | Sí (41 p.) |
| `01_ANALISIS/05_GLOSARIO/Glosario_Eventos_Nova_Final.docx` | Sí (15 p.) |
| `02_ARQUITECTURA/04_MODELO_RELACIONAL/Modelo_Relacional_Eventos_Nova.docx` | Sí (19 p.) |
| `02_ARQUITECTURA/05_PATRONES_SOLID/Patrones_Diseno_SOLID_Eventos_Nova.docx` | Sí (6 p.) |
| `02_ARQUITECTURA/06_ADR/Registro_ADR_Eventos_Nova.docx` | Sí (24 p.) |
| `02_ARQUITECTURA/07_DECISIONES_TECNICAS/Decisiones_Tecnicas_Eventos_Nova.docx` | Sí (8 p.) |
| `02_ARQUITECTURA/08_MATRIZ_TRAZABILIDAD/Matriz_Trazabilidad_Eventos_Nova.docx` | Sí (11 p.) |
| `03_IMPLEMENTACION/01_MANUAL_TECNICO/Manual_Tecnico_Eventos_Nova.docx` | Sí (14 p.) |
| `03_IMPLEMENTACION/03_DOCUMENTACION_API/Documentacion_API_Eventos_Nova.docx` | Sí (28 p.) |
| `03_IMPLEMENTACION/05_CI/Manual_Integracion_Continua_Eventos_Nova.docx` | Sí (5 p.) |
| `03_IMPLEMENTACION/06_CD_DESPLIEGUE/Manual_Entrega_Continua_Despliegue_Eventos_Nova.docx` | Sí (5 p.) |
| `03_IMPLEMENTACION/09_REPOSITORIO/Repositorio_GitHub_Eventos_Nova.docx` | Sí (4 p.) |
| `03_IMPLEMENTACION/10_MANUAL_INSTALACION/Manual_Instalacion_Eventos_Nova.docx` | Sí (5 p.) |
| `03_IMPLEMENTACION/11_MANUAL_USUARIO/Manual_Usuario_Eventos_Nova.docx` | Sí (4 p.) |
| `03_IMPLEMENTACION/12_SEGURIDAD/Documentacion_Seguridad_Eventos_Nova.docx` | Sí (4 p.) |
| `04_CALIDAD_Y_PRUEBAS/01_GUIA_PRUEBAS/Guia_Pruebas_Manuales_Eventos_Nova.docx` | Sí (40 p.) |
| `04_CALIDAD_Y_PRUEBAS/02_INFORME_PRUEBAS/Informe_General_Pruebas_Eventos_Nova.docx` | Sí (10 p.) |
| `04_CALIDAD_Y_PRUEBAS/04_COBERTURA/Reporte_Cobertura_Eventos_Nova.docx` | Sí (3 p.) |
| `04_CALIDAD_Y_PRUEBAS/05_MATRIZ_PERMISOS/Matriz_Roles_Permisos_Eventos_Nova.docx` | Sí (7 p.) |
| `05_ENTREGA_Y_DEFENSA/Reporte_Final_PIA_Eventos_Nova.docx` | Sí (14 p.) |
| `05_ENTREGA_Y_DEFENSA/Presentacion_Defensa_PIA_Eventos_Nova.pptx` | Sí (17 p.) |

Además de lo anterior, el paquete incluye 53 archivos BPMN (editables `.drawio`/`.bpmn` y exportaciones PDF/PNG/SVG), 10 archivos `.feature`, 11 ADR individuales, diagramas DDD, UML, arquitectura, relacional y CI/CD (editables y exportaciones), OpenAPI, workflows de CI, archivos de configuración Docker, reporte HTML de cobertura y evidencias vigentes.

## Inventario real del paquete (verificado el 05/11/2026)

El paquete tiene **368 archivos**: 366 de contenido y los dos de la raíz (`LEEME.md` y `REGISTRO_DE_CAMBIOS.md`). Antes de crear el registro había 367.

| Carpeta | Archivos |
|---|---|
| `01_ANALISIS/` | 71 |
| `02_ARQUITECTURA/` | 108 |
| `03_IMPLEMENTACION/` | 41 |
| `04_CALIDAD_Y_PRUEBAS/` | 142 (85 de ellos son el reporte HTML de cobertura) |
| `05_ENTREGA_Y_DEFENSA/` | 4 |
| Raíz (`LEEME.md`, `REGISTRO_DE_CAMBIOS.md`) | 2 |
| **Total** | **368** |

Por tipo: 55 PDF, 22 DOCX, 3 XLSX, 1 PPTX, 29 `.drawio`, 9 `.bpmn`, 14 `.puml`, 10 `.feature`, 46 PNG, 29 SVG, 80 HTML y 32 Markdown (incluido este `LEEME.md` y `REGISTRO_DE_CAMBIOS.md`). Las páginas de la tabla anterior se contaron en los propios PDF con dos métodos independientes.

## Lo que no está hecho y no se presenta como hecho

| ID | Pendiente |
|---|---|
| P-01 | ~~Fusionar la Pull Request #2~~ — **Resuelto el 05/11/2026**: fusionada en `main` con un merge commit (`0b16cf3`; 37 commits en `main`); el CI de `main` (run 42109720404) terminó correctamente con 1,677 pruebas OK. La rama `fix/cierre-bloque-a` se conserva |
| P-02 | **Resuelto en la documentación.** CI sobre el commit 9c72bc7 (run 42104865505) y sobre `main` 0b16cf3 (run 42109720404), 05/11/2026: 1,677 pruebas OK; 1 omitida en el trabajo de pruebas y 8 en el de Docker (motivos en `REGISTRO_DE_CAMBIOS.md`); cobertura de sentencias 98.21 % (6,573 de 6,693). Los DOCX, PDF y PPTX se actualizaron (sección 4.5 del registro) |
| P-03 | **Resuelto** en el commit 9c72bc7 (`tests/referencias/*.json -text` en .gitattributes). Comprobado en un clon nuevo con core.autocrlf=true (Windows: 1,677 OK) y en el CI de Linux. Los documentos que lo describían como pendiente ya se actualizaron |
| P-04 | Despliegue en Render (u otra plataforma) con render.yaml revisado y aprobación de costos |
| P-05 | Registrar la URL pública del sistema y de Swagger UI (/docs con EVENTOSNOVA_DOCS=1) en README, reporte final y presentación |
| P-06 | Evidencias de la aplicación desplegada: /health, /ready, /docs, inicio de sesión, registros del preDeploy y del worker |
| P-07 | Pruebas finales sobre el entorno publicado (recorrido de los tres roles y reglas principales) |
| P-08 | Ejecución humana de los casos manuales de la interfaz web y archivo de sus capturas |
| P-09 | Decisiones pendientes del Bloque A: COR-08, COR-07 como restricción, COR-11/COR-19 como bloqueo, COR-09 |
| P-10 | La cobertura del código actual quedó registrada por el CI (98.21 % de sentencias, 6,573 de 6,693; commit 9c72bc7 y `main` 0b16cf3). Falta archivar su coverage.json: el que contiene este paquete es de la medición del 03/11/2026, anterior al Bloque A |
| P-11 | Retirar o sustituir en el repositorio los documentos de entrega antiguos de docs/entrega/ (PDF y presentación generados el 29/10/2026); no forman parte de esta entrega |
| P-12 | ZIP definitivo del proyecto y manifiesto SHA-256, después de los bloques C y D |

La medición archivada de 98.19 % (03/11/2026) y la del CI sobre `main` 4be166b (98.21 %) son anteriores al Bloque A; las del CI sobre el commit 9c72bc7 y sobre `main` 0b16cf3 (98.21 %) ya incluyen el Bloque A. Este paquete no incluye un manifiesto SHA-256 definitivo.

El detalle de los cambios de esta versión, las verificaciones y las limitaciones conocidas están en `REGISTRO_DE_CAMBIOS.md`.

## Ubicación de cada carpeta del paquete en el repositorio

Este documento describe el paquete tal como se preparó (carpetas `01_ANALISIS/` a `05_ENTREGA_Y_DEFENSA/`). En el repositorio, el contenido quedó así (integración del 05/11/2026, rama `docs/integracion-bloque-b`):

| Carpeta del paquete | Ubicación en el repositorio |
|---|---|
| `01_ANALISIS/` BRD, historias, Gherkin (y sus `.feature`), glosario | `docs/analisis/` (`brd/`, `historias_usuario/`, `gherkin/`, `glosario/`) |
| `01_ANALISIS/04_BPMN/` | BPMN maestro y SP01 a SP08, idénticos a los ya publicados: siguen en `diagramas/bpmn/`. SP09 y SP10 (nuevos): `diagramas/definitivos/bpmn/` |
| `02_ARQUITECTURA/01_DDD/` | `diagramas/definitivos/ddd/` |
| `02_ARQUITECTURA/02_DIAGRAMAS_UML/` | `diagramas/definitivos/clases/` y `diagramas/definitivos/secuencia/`; los PDF de conjunto en `docs/architecture/definitivo/` |
| `02_ARQUITECTURA/03_ARQUITECTURA_SISTEMA/` y `03_IMPLEMENTACION/07_CI_CD_DIAGRAMAS/` | `diagramas/definitivos/arquitectura/` |
| `02_ARQUITECTURA/04_MODELO_RELACIONAL/` | Documento: `docs/architecture/definitivo/`; diagrama: `diagramas/definitivos/modelo_relacional/`; `esquema-relacional-postgresql.md` actualiza el existente en `docs/architecture/` |
| `02_ARQUITECTURA/05_PATRONES_SOLID/`, `07_DECISIONES_TECNICAS/` | `docs/architecture/definitivo/` |
| `02_ARQUITECTURA/06_ADR/` | `docs/ADR/` (Registro, índice y ADR-001 a ADR-004). Los ADR-005 a ADR-011 se conservan sin cambios: son los originales del repositorio |
| `02_ARQUITECTURA/08_MATRIZ_TRAZABILIDAD/` | `docs/trazabilidad/Matriz_Trazabilidad_Eventos_Nova.*` (no sustituye a `matriz-trazabilidad.xlsx`) |
| `03_IMPLEMENTACION/02_OPENAPI/`, `03_DOCUMENTACION_API/` | `docs/api/` (`openapi.json` ya existía y es idéntico) |
| `03_IMPLEMENTACION/04_README/README.md` | `README.md` en la raíz (versión actualizada) |
| `03_IMPLEMENTACION/06_CD_DESPLIEGUE/docs_architecture/ci-cd-y-despliegue.md` | `docs/architecture/ci-cd-y-despliegue.md` (actualizado) |
| Resto de `03_IMPLEMENTACION/` (manuales, repositorio, seguridad, Docker y variables) | `docs/manuales/` |
| `03_IMPLEMENTACION/05_CI/workflows/`, `08_DOCKER_VARIABLES/archivos_configuracion/` | No se copian: son copias de archivos que el repositorio ya tiene (`.github/workflows/`, raíz) |
| `04_CALIDAD_Y_PRUEBAS/` | `docs/calidad/` (`evidencias/`, `cobertura/`, `matriz_permisos/`) |
| `04_CALIDAD_Y_PRUEBAS/03_EVIDENCIAS/02_INTERFAZ_CAPTURAS_AUTOMATICAS/` y `08_BLOQUE_A_CHROME/` | Las capturas ya publicadas siguen en `tests/evidencias/pruebas_manuales_web/_automaticas/` y `.../bloque_a/` |
| `05_ENTREGA_Y_DEFENSA/` | `docs/entrega_final/` |
| `LEEME.md`, `REGISTRO_DE_CAMBIOS.md` | `docs/documentacion_final/` |

**No incluidos en el repositorio:** el `coverage.json` de la medición del 03/11/2026 (archivo generado, 2.7 MB; sus cifras están en `docs/calidad/cobertura/VERIFICACION_COBERTURA.md` y `coverage_reporte.txt`), los ocho `cobertura_grupo*.log` (el `.gitignore` ignora `*.log`) y el reporte HTML de cobertura (85 archivos generados). Los textos que mencionan esos archivos se refieren al paquete original.
