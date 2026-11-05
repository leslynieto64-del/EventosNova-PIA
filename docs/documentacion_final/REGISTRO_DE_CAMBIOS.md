# Registro de cambios y verificación — Documentación final del PIA de Eventos Nova

**Fecha del registro:** 05/11/2026 · **Alcance:** carpeta `EVENTOS_NOVA_FINAL/` (368 archivos).

Este registro reúne **solo** lo que se pudo documentar o comprobar: los historiales de versiones que los propios documentos declaran, el resultado de comparar el paquete con lo publicado en GitHub, los ajustes aplicados al paquete el 05/11/2026 y las verificaciones realizadas, con su método. No reconstruye cambios anteriores que ningún documento registre. Lo que no se pudo comprobar figura en la sección 7.

## 1. Contenido del paquete

| Carpeta | Archivos |
|---|---|
| `01_ANALISIS/` | 71 |
| `02_ARQUITECTURA/` | 108 |
| `03_IMPLEMENTACION/` | 41 |
| `04_CALIDAD_Y_PRUEBAS/` | 142 |
| `05_ENTREGA_Y_DEFENSA/` | 4 |
| Raíz (`LEEME.md`, `REGISTRO_DE_CAMBIOS.md`) | 2 |
| **Total** | **368** |

## 2. Cambios que los propios documentos declaran

Copiados literalmente de las tablas de historial de cada documento (no se interpretaron ni se completaron).

### BRD (`01_ANALISIS/01_BRD/BRD_Eventos_Nova_Final.docx`)

| Versión | Fecha | Descripción |
|---|---|---|
| 1.0 | 08/09/2026 | BRD de la Unidad 2 (Análisis de requerimientos de negocio): necesidades BN-001 a BN-010 y situaciones especiales SE-001 a SE-012. |
| 1.1 | 23/10/2026 | Sincronización de requisitos con el cierre de alcance (decisiones A, B y C): se precisaron las necesidades BN-003 a BN-010, las restricciones, las situaciones SE-004 a SE-007 y SE-009 a SE-012, el alcance y las responsabilidades de Administración. |
| 2.0 | 06/11/2026 | Versión consolidada para la entrega del PIA. Integra en sus apartados las precisiones que el 03/11/2026 se habían documentado como adenda (ADR-007 a ADR-011), elimina la adenda como sección independiente, organiza el contenido en tablas y une dos restricciones repetidas. No se renumeraron identificadores. |

| Elemento | Versión 1.0 (Unidad 2) | Cambio posterior | Versión |
|---|---|---|---|
| Stakeholder Administración | Registra y verifica pagos, autoriza cambios y servicios adicionales y ejecuta devoluciones por solicitudes no realizadas. | Se añade la devolución del anticipo cuando la contratación se cierra sin confirmarse. | 1.1 |
| Alcance | Devoluciones por solicitudes no realizadas. | Se añade la devolución del anticipo; la reprogramación de la fecha del evento queda fuera del alcance. | 1.1 |
| Alcance | — | Catálogo de proveedores, registro de costos por operación, procedencia de respuestas e inicio automático; fuera del alcance: envío real de mensajes, cálculo de disponibilidad por fecha y cuenta del Cliente. | 2.0 |
| BN-003 y BN-004 | El plazo de 24 horas se refería al registro y la verificación del pago. | Las 24 horas son el plazo del Cliente para pagar; el registro y la verificación pueden ser posteriores. En servicios adicionales se fija el orden de las verificaciones (evento, cinco días, saldo vencido). | 1.1 |
| BN-005 | Liquidación del saldo tres días hábiles antes del evento; protocolo de cobro y regularización en 24 horas. | Cuenta la fecha en que el Cliente pagó; un pago tardío no liquida el saldo; la cancelación se registra antes del inicio; las devoluciones identifican el pago de anticipo y un pago genera como máximo una devolución. | 1.1 |
| BN-006 y BN-007 | Configuración vigente y consultas por función. | Lo confirmado antes del inicio se aplica aunque la actualización sea posterior; las consultas excluyen obligaciones Sin efecto y muestran devoluciones pendientes. | 1.1 |
| BN-008 | Cancelaciones con política de no reembolso. | Cierre de solicitudes en trámite con el motivo «Evento cancelado»; no reembolso de excedentes y pagos tardíos; constancia única; distinción con Cerrado sin contratación. | 1.1 |
| BN-009 | «El anticipo corresponde al 30 %»; si el importe no corresponde, se corrige. | Anticipo de al menos 30 % (decisión B); contacto y 24 horas; Cerrado sin contratación; devolución del anticipo (decisión A). | 1.1 |
| BN-009 | Corrección de un anticipo inferior al 30 %. | Acumulación de pagos parciales (E-3, decisión del equipo sin aprobación externa). En la versión 1.1 figuraba como nota fechada; en la 2.0 se integra en el texto. | 2.0 |
| BN-010 | Registro de la finalización y su fecha. | Inicio automático en T y cierres al llegar T (versión 1.1). El contrato Firmado no confirmado también pasa a Cerrado sin confirmar (D-3, decisión interna del equipo; integrada en la 2.0). | 1.1 y 2.0 |
| Restricciones | Anticipo del 30 %; servicios adicionales denegados con menos de cinco días; cancelación sin reembolso. | Anticipo mínimo y acumulación de pagos; registro como no procedente; no reembolso de excedentes; dos restricciones repetidas se integran. | 1.1 y 2.0 |
| SE-004 a SE-007, SE-009 a SE-012 | Situaciones especiales de la Unidad 2. | Precisiones de plazos, orden de verificaciones, devoluciones y cierres; SE-010 integra la acumulación de pagos parciales (E-3). | 1.1 y 2.0 |

### Historias de usuario (`01_ANALISIS/02_HISTORIAS_USUARIO/Historias_Usuario_Eventos_Nova_Final.docx`)

| Versión | Fecha | Descripción |
|---|---|---|
| 1.0 | 08/09/2026 | Historias de la Unidad 2: US-001 a US-031 y criterios CA-001 a CA-098. |
| 1.1 | Posterior al 08/09/2026; fecha no documentada | Se añadieron CA-099 y CA-100. |
| 1.2 | 23/10/2026 | Sincronización con el cierre de alcance: se añadieron US-032 y US-033 y los criterios CA-101 a CA-114; se modificaron CA-019, CA-021, CA-091, CA-097 y CA-098. |
| 2.0 | 06/11/2026 | Versión consolidada para la entrega del PIA. Integra la adenda del 03/11/2026 (actores y roles, trazabilidad con API, BPMN y pruebas, normalización de CA-038 y CA-091, historias complementarias HC-01 a HC-06) y las notas de revisión de CA-019, CA-109 y CA-110. |

| Elemento | Cambio | Versión | Fuente |
|---|---|---|---|
| US-032, US-033 | Historias nuevas: devolución del anticipo de una contratación cerrada e inicio automático del Evento. | 1.2 | Cierre de alcance (decisión A, C-01, C-02) |
| CA-099, CA-100 | Criterios añadidos después de la Unidad 2. | 1.1 | Fecha no documentada |
| CA-101 a CA-114 | Criterios de US-032 y US-033 y de reglas del cierre de alcance. | 1.2 | Cierre de alcance (23/10/2026) |
| CA-019, CA-021, CA-091, CA-097, CA-098 | Precisiones de anticipo, fecha efectiva del pago, no reembolso y solicitudes. | 1.2 | Cierre de alcance (23/10/2026) |
| CA-019 | Acumulación de pagos parciales del anticipo. | 2.0 | E-3, ADR-007 (decisión del equipo, sin aprobación externa) |
| CA-109 | Desde T, la solicitud de servicio adicional se registra como «No procedente». | 2.0 | Interpretación del equipo (GL-015, SE-004) |
| CA-110 | El contrato En preparación o Firmado no confirmado pasa a Cerrado sin confirmar. | 2.0 | D-3, ADR-008 (decisión interna del equipo) |
| CA-038, CA-091 | Redacción estructurada Dado / Cuando / Entonces sin cambio de contenido. | 2.0 | Revisión documental |
| HC-01 a HC-06 | Historias complementarias de funciones aprobadas por el equipo. | 2.0 | ADR-009 a ADR-011 |

### Glosario (`01_ANALISIS/05_GLOSARIO/Glosario_Eventos_Nova_Final.docx`)

| Versión | Fecha | Descripción |
|---|---|---|
| 1.0 | 08/09/2026 | Glosario de la Unidad 2: GL-001 a GL-059. |
| 1.1 | Posterior al 08/09/2026; fecha no documentada | Se añadió GL-060 (días hábiles). |
| 1.2 | 23/10/2026 | Sincronización con el cierre de alcance: se añadieron GL-061 y GL-062 y se precisaron GL-004, GL-009, GL-011, GL-012, GL-015, GL-031, GL-032, GL-033, GL-042, GL-049, GL-053, GL-055, GL-057 y GL-060. |
| 2.0 | 06/11/2026 | Versión consolidada para la entrega del PIA. |

## 3. Comparación con lo publicado en GitHub (`origin/main`, commit `4be166b`)

Método: SHA-256 de los 367 archivos (con y sin normalizar saltos de línea) frente a los 448 de `origin/main`, a los archivos locales sin seguimiento y a los del Bloque A, más comparación de contenido. La clasificación se hizo **antes** de los ajustes de la sección 4; el detalle por archivo está en `BLOQUE_B_CLASIFICACION_ARCHIVOS_20261105.csv` (fuera de este paquete).

| Clase | Significado | Archivos |
|---|---|---|
| A | Idénticos a un archivo publicado (no se vuelven a subir) | 72 |
| B | Actualizan un archivo publicado | 10 |
| C | Nuevos | 202 |
| E | Duplicados (mismo contenido que otro archivo) | 6 |
| F | Mismo tema que un archivo publicado, con contenido distinto | 77 |

Archivos que actualizan versiones publicadas (clase B):

| Archivo publicado | Diferencia | Qué cambia |
|---|---|---|
| `README.md` | +68 / −9 líneas | Estado al 05/11/2026; título y datos del PIA |
| `docs/architecture/esquema-relacional-postgresql.md` | +71 / −1 líneas | Revisiones 0005 a 0009 y esquema vigente (26 tablas) |
| `docs/architecture/ci-cd-y-despliegue.md` | +13 / −0 líneas | Sección «Estado al 05/11/2026» |
| `docs/ADR/ADR-005` a `ADR-011` (7 archivos) | formato distinto | De viñetas a tabla de 14 campos; conservan entre 96 % y 100 % de las palabras del original |

Los diagramas, la matriz de trazabilidad y `Reporte_BRD_Corregido.docx` ya publicados **no se sobrescriben**: varias pruebas automatizadas los leen (se comprobó en una copia aparte que añadir los `.puml` nuevos junto a los publicados hace fallar 3 pruebas de `test_coherencia_diagramas`).

## 4. Ajustes aplicados a este paquete el 05/11/2026

Antes de modificar nada se guardó una copia íntegra del paquete (367 archivos) en `BLOQUE_B_STAGING_ANTES_DE_AJUSTES_20261105.zip` (SHA-256 `5ddce56506cc7fec92b1f27f7baba716e81d7ac5aaa2bc74d1ed4c4892d61937`).

### 4.1 `LEEME.md`

- Páginas de los PDF: se contaron en los 55 PDF con dos métodos independientes (árbol de páginas y objetos de página) y coinciden. Cuatro cantidades del inventario eran incorrectas:

| Documento | Decía | Real |
|---|---|---|
| `BRD_Eventos_Nova_Final.docx` | 35 | 36 |
| `Historias_Usuario_Eventos_Nova_Final.docx` | 28 | 30 |
| `Especificacion_Gherkin_Eventos_Nova.docx` | 39 | 41 |
| `Glosario_Eventos_Nova_Final.docx` | 21 | 15 |

  Las demás 19 cantidades (modelo relacional 17, patrones 6, registro ADR 24, decisiones técnicas 7, matriz 10, manual técnico 13, API 27, CI 4, CD 5, repositorio 4, instalación 5, usuario 4, seguridad 4, guía de pruebas 40, informe de pruebas 8, cobertura 3, matriz de permisos 6, reporte final 14 y presentación 17) coincidían.
- Inventario: se sustituyó «368 archivos» sin desglose por una tabla por carpeta y por tipo. Había 367 archivos; con este registro son 368.
- Estado del repositorio y pendientes P-01, P-02, P-03 y P-10: actualizados con lo verificado el 05/11/2026 (11 commits en `fix/cierre-bloque-a`, Pull Request #2 abierta, CI correcto, causa y corrección del fallo LF/CRLF).

### 4.2 Excel: valores calculados

Las 11 celdas con fórmula (6 y 5) estaban guardadas **sin valor** (`<v></v>`). No había Excel ni LibreOffice en el equipo: cada fórmula (`COUNTA`, `COUNTIF`, `COUNTIFS`) se calculó con un programa propio sobre los datos de las hojas y el valor se escribió en el XML. No se cambió ninguna otra parte del archivo y se conservó `fullCalcOnLoad="1"`, de modo que Excel también recalcula al abrir.

| Archivo | SHA-256 antes | SHA-256 después |
|---|---|---|
| `Matriz_Trazabilidad_Eventos_Nova.xlsx` | e3835f8c00560188… | f85658c329e1c272… |
| `Matriz_Roles_Permisos_Eventos_Nova.xlsx` | 0ffc155f7f5a427c… | d09f6ca91aa0f6a9… |

| Celda | Indicador de `Matriz_Trazabilidad_Eventos_Nova.xlsx` › Resumen | Valor |
|---|---|---|
| B2 | Operaciones de la API trazadas | 77 |
| B3 | Operaciones con historia asociada | 56 |
| B4 | Historias aprobadas (US) | 33 |
| B5 | Historias complementarias (HC) | 6 |
| B6 | Necesidades BN implementadas | 10 |
| B7 | Situaciones especiales SE | 12 |

`Resumen!B3` = **56**: de las 77 filas de `Endpoints`, 21 tienen «-» como historia y 56 tienen una. En `Matriz_Roles_Permisos_Eventos_Nova.xlsx` › Resumen: Administrador 35, Coordinador 53, Proveedor 7, operaciones 77 y rutas públicas 4. Esos tres primeros valores coinciden con lo medido en el código (32, 50 y 4 operaciones por permiso de negocio, más las 3 de sesión que todos los roles comparten). `INDICE_EVIDENCIAS.xlsx` no tiene fórmulas.

### 4.3 Rutas locales

Diez archivos de texto contenían rutas absolutas del equipo (527 ocurrencias). Solo se sustituyó el prefijo de la ruta: la raíz del proyecto por `<RAIZ_DEL_PROYECTO>`, la carpeta de la medición por su nombre relativo `MEDICION_COBERTURA_20261103` y la instalación de Python por `<PYTHON_3.13>`. Los logs de cobertura son evidencia de una medición real: **su contenido es el original salvo ese prefijo**. No había rutas locales en los DOCX, PPTX ni XLSX.

| Archivo | Sustituciones | SHA-256 antes | SHA-256 después |
|---|---|---|---|
| `cobertura_grupo1.log` | 11 | 1df6864cc00d… | e8e9c291adad… |
| `cobertura_grupo2.log` | 113 | dff7fbada9e2… | 3e07ec026aed… |
| `cobertura_grupo3.log` | 383 | bf11487f1263… | 52b5d1fa3c07… |
| `cobertura_grupo4.log` | 5 | c009d46cf75e… | a235f03ade06… |
| `cobertura_grupo5.log` | 5 | 149fef639f53… | e1899d05a705… |
| `cobertura_grupo6.log` | 1 | d578be2dba25… | 415e0dafce48… |
| `cobertura_grupo7.log` | 1 | af542e5c867c… | c42957c8b54d… |
| `cobertura_grupo8.log` | 1 | 4fe27d4628a0… | 0b02f5790152… |
| `ejecucion_consola.txt` | 6 | b922290aa715… | a912c65aa886… |
| `INFORME_COBERTURA_REAL_20261103.md` | 1 | 718f6d93f6a2… | 2ef5a5ca9922… |

Los dos archivos `coverage_reporte.txt` y `coverage_verificacion_80.txt` de la misma carpeta no contenían rutas y no se tocaron.

### 4.4 Este registro

`REGISTRO_DE_CAMBIOS.md` no existía (el `LEEME` lo citaba). Se creó con la información de las secciones 1 a 7; la sección 4.5 se añadió después de actualizar los documentos.

### 4.5 Actualización de documentos con información obsoleta (05/11/2026)

Tras fusionar la Pull Request #2 se actualizaron, **sin reconstruirlos y conservando su formato institucional**, los documentos que describían un estado anterior. Los textos se reemplazaron en el propio XML de cada DOCX, PPTX y XLSX (los fragmentos conservan su formato); después Word y PowerPoint abrieron todos los archivos y regeneraron los PDF correspondientes. Los hechos usados son los comprobados:

- Pull Request #2 fusionada el 05/11/2026 con un merge commit (`0b16cf3`); `main` pasó a 37 commits (25 anteriores + 11 del Bloque A + el merge). La rama `fix/cierre-bloque-a` se conserva.
- CI sobre el commit `9c72bc7` (run 42104865505) y sobre `main` `0b16cf3` (run 42109720404): 1,677 pruebas OK; 1 omitida en el trabajo de pruebas; 8 omitidas en el trabajo Docker (motivos en la sección 6); cobertura de sentencias 98.21 % (6,573 de 6,693).
- El CI de `4be166b` (run 41901496391; 1,654 pruebas OK; 0 omitidas en el trabajo de pruebas y 3 en el de Docker) queda como referencia histórica, ya no como la última ejecución.
- La diferencia de saltos de línea LF/CRLF (P-03) está resuelta en `9c72bc7`. Las verificaciones del commit `e3c98d9` se anotan como válidas para `9c72bc7`, que solo añade una regla de `.gitattributes`.
- **Sin cambios de alcance:** el despliegue, la URL pública, Swagger UI en producción y las evidencias de la aplicación desplegada siguen pendientes y no se declaran como hechos.

Archivos modificados (SHA-256 después del cambio). Los 15 PDF correspondientes a los DOCX y a la presentación se regeneraron con Word y PowerPoint; sus páginas figuran en el `LEEME.md`:

| Archivo | SHA-256 |
|---|---|
| `02_ARQUITECTURA/04_MODELO_RELACIONAL/Modelo_Relacional_Eventos_Nova.docx` | `8f6e4b4b1a5e347b68ead9d461d2bc585a1e91f2e413eff7c2294f0af86c8f0a` |
| `02_ARQUITECTURA/05_PATRONES_SOLID/Patrones_Diseno_SOLID_Eventos_Nova.docx` | `d55c917699418da7d6b7366cbb80063478a46507bf37f779729ba137ab5010cb` |
| `03_IMPLEMENTACION/03_DOCUMENTACION_API/Documentacion_API_Eventos_Nova.docx` | `4d8b48c891fb9e3047b01f76e679de35aaf85412ddc3f102d77b4a862964526b` |
| `03_IMPLEMENTACION/12_SEGURIDAD/Documentacion_Seguridad_Eventos_Nova.docx` | `b2dcc118e9f2d3a9841c3dc9bf7304ea415a4087ad718b41d41741ed723ade38` |
| `04_CALIDAD_Y_PRUEBAS/05_MATRIZ_PERMISOS/Matriz_Roles_Permisos_Eventos_Nova.docx` | `89e310863cb75c1dd37bcf8eaf4151ae6818cecbe253a01eab054db282cfa011` |
| `02_ARQUITECTURA/07_DECISIONES_TECNICAS/Decisiones_Tecnicas_Eventos_Nova.docx` | `e8fb2781ce88b243f156236dc7c6c8420b7a00b903b402c02973cc630e8d98fd` |
| `02_ARQUITECTURA/08_MATRIZ_TRAZABILIDAD/Matriz_Trazabilidad_Eventos_Nova.docx` | `2409145cf0fb39ec7fae9855944e1a6b2701b58489d5f40b7989f46a8a95806a` |
| `03_IMPLEMENTACION/01_MANUAL_TECNICO/Manual_Tecnico_Eventos_Nova.docx` | `43174cc778a01f296a37989fc19b9e0527571a7578d7e130fed8c0e6c45bef78` |
| `03_IMPLEMENTACION/05_CI/Manual_Integracion_Continua_Eventos_Nova.docx` | `542cb1dbe5437fe4b3723fe6f335bed5fb833a5fbb7f53c7e38dc05905f9754c` |
| `03_IMPLEMENTACION/09_REPOSITORIO/Repositorio_GitHub_Eventos_Nova.docx` | `84f871efacf7c3d191f884e97eb9c0778a9968fe1f62b118418838794a102ab3` |
| `03_IMPLEMENTACION/10_MANUAL_INSTALACION/Manual_Instalacion_Eventos_Nova.docx` | `2ef4304a7bc055c59969043a3c312ee167387d4ae27538cbfc082cf510c9a10d` |
| `04_CALIDAD_Y_PRUEBAS/02_INFORME_PRUEBAS/Informe_General_Pruebas_Eventos_Nova.docx` | `37893a963c8b08f605c50423d9414b5fc19919e76cb895f5d03cceb479479c24` |
| `05_ENTREGA_Y_DEFENSA/Reporte_Final_PIA_Eventos_Nova.docx` | `b713a0cb61f3d5bdd761bee4840cd566e69c5f8c7e9d1e5d9599ec12b01007e9` |
| `04_CALIDAD_Y_PRUEBAS/04_COBERTURA/Reporte_Cobertura_Eventos_Nova.docx` | `d3bd0b1e110e9d2930cd76379846b95c5616ca62d4018f610ab426b740ee5dd8` |
| `05_ENTREGA_Y_DEFENSA/Presentacion_Defensa_PIA_Eventos_Nova.pptx` | `5dc17e44d53b3eacf83b34a0bbe00d1c2e276ae4cccc6311287ed8384f99fbde` |
| `03_IMPLEMENTACION/04_README/README.md` | `a1d6b9a431f9216da9fd4151cb6e0abdb7328a2a876bbbaa1700f75e9c69d6e2` |
| `03_IMPLEMENTACION/06_CD_DESPLIEGUE/docs_architecture/ci-cd-y-despliegue.md` | `86a83aa6dd4862f1cc7faf0dc71b5d2d63c8d5636fa2177460ee4a5aff2f18a9` |
| `04_CALIDAD_Y_PRUEBAS/03_EVIDENCIAS/INDICE_EVIDENCIAS.md` | `0c9e5f4f99e8a139ba5cd302033714fa70cb702a8776014a9ff07e9c6b0054b3` |
| `04_CALIDAD_Y_PRUEBAS/03_EVIDENCIAS/06_CI_CD/LEEME_PENDIENTE.md` | `d1c546aefe7c3985762eec55c2466f776a7e439e926ea345879cb8e37f4e6e95` |
| `02_ARQUITECTURA/04_MODELO_RELACIONAL/docs_architecture/esquema-relacional-postgresql.md` | `2dd1ff40e9338ef694bf03fbe9de6df9eb5959fbfcd11d3a73c203e200d80064` |
| `03_IMPLEMENTACION/02_OPENAPI/VERIFICACION_OPENAPI.md` | `73207e5adf9149a1ef18920727dbc777e1314b140ac775732e814f6f089f74f3` |
| `03_IMPLEMENTACION/08_DOCKER_VARIABLES/DOCKER_COMPOSE_Y_VARIABLES.md` | `54e56dda7da8ea6d99dd01e7d9db60e3b6d00d0f789eb65c9771edbf840ffdf7` |
| `02_ARQUITECTURA/08_MATRIZ_TRAZABILIDAD/Matriz_Trazabilidad_Eventos_Nova.xlsx` | `a8f80beb6e72e0c9a8449e4fe45d8d22acedc3fd2f1eacc5f7078cec1f79707f` |

## 5. Verificaciones del contenido (05/11/2026)

| Elemento | Resultado |
|---|---|
| BRD | Tabla «ID / Situación / Regla vigente / Proceso o implementación» con SE-001 a SE-012: 12 filas, 4 columnas, ninguna celda vacía |
| Historias de usuario | 33 historias (US-001 a US-033), 114 criterios (CA-001 a CA-114), HC-01 a HC-06 en tablas aparte; la matriz principal tiene 114 filas y ninguna es una HC |
| Excel de trazabilidad | 6 hojas (Necesidades_BN, Historias, Endpoints, Situaciones_SE, Resumen, Bloque_A); fórmulas solo en Resumen; `B3` = 56 por recálculo independiente |
| ADR | 11 ADR con tabla individual de 14 campos, sin campos vacíos; índice con ADR-001 a ADR-011. Varios campos dicen «No documentado» porque el ADR original no los contenía (ver sección 7) |
| BPMN | Maestro y SP01 a SP10 con fuente `.drawio` y exportaciones PDF, PNG y SVG; SP01 a SP08 y el maestro además con `.bpmn`; SP09 y SP10 no tienen `.bpmn` |
| OpenAPI | `openapi.yaml` y `openapi.json`: 73 rutas y 77 operaciones; `CATALOGO_OPERACIONES.csv`: 77 filas; el `openapi.json` es idéntico al publicado |
| Presentación | 17 diapositivas y PDF de 17 páginas |
| Secretos | Sin archivos `.env`; las coincidencias de contraseñas son marcadores (`cambiar_esta_contrasena`, `ci_clave_efimera`) |

## 6. Código y pruebas a los que se refiere la documentación

Rama `fix/cierre-bloque-a`, publicada el 05/11/2026 con 11 commits de `Lesly <leslynieto64@gmail.com>`; Pull Request #2 abierta hacia `main`, **sin fusionar**:

| Commit | Mensaje |
|---|---|
| `69816ed` | fix: vincula el proveedor solo a cuentas con rol proveedor |
| `97ea865` | feat: formulario de cuentas por rol con campo de proveedor condicional |
| `e2697a6` | fix: no expone al proveedor las condiciones comerciales del cliente |
| `0372f90` | feat: botón mostrar/ocultar contraseña y búsqueda en listas desplegables |
| `df5277e` | feat: búsqueda y filtros por rol y estado en la lista de cuentas |
| `4944dee` | feat: etiquetas legibles de conceptos y tipos y estados de pago explicados |
| `1a080b0` | feat: precarga de los datos actuales del evento en el formulario de cambio |
| `f2c97e3` | feat: advertencia visible de importe superior al saldo y aviso al comunicar la política |
| `233d80a` | test: pruebas de etiquetas, precarga y advertencia, y recorrido en Chrome del Bloque A |
| `e3c98d9` | test: capturas de evidencia del Bloque A |
| `9c72bc7` | fix: conserva byte a byte los JSON de referencia con .gitattributes |

| Ejecución | Entorno | Resultado |
|---|---|---|
| CI sobre `main` `4be166b` (antes del Bloque A) | Linux | Trabajo de pruebas: 1,654 OK, 0 omitidas · Trabajo Docker: 1,654 OK, 3 omitidas · cobertura 98.21 % |
| Clon nuevo de `9c72bc7` con `core.autocrlf=true` | Windows, PostgreSQL 18 | 1,677 OK, 1 omitida |
| CI sobre `9c72bc7` (run 42104865505) | Linux | Trabajo de pruebas: 1,677 OK, 1 omitida, cobertura 98.21 % (6,573 de 6,693) · Trabajo Docker: 1,677 OK, 8 omitidas |

### Pruebas omitidas

El CI imprime solo el total de omitidas, no sus nombres. Se obtuvieron ejecutando esos módulos con `unittest -v`, una vez **sin Node.js ni Chrome** (como la imagen Docker de pruebas, que no los tiene) y otra **con Node.js** (como el trabajo de pruebas del runner). Ambas reproducciones dieron exactamente los totales del CI (8 y 1).

| # | Prueba | Razón | Docker | Trabajo de pruebas |
|---|---|---|---|---|
| 1 | `test_interfaz_textos.HumanizarYSinVacios.test_conserva_el_motivo_y_los_identificadores_de_datos` | Node.js no está instalado | omitida | corre |
| 2 | `test_interfaz_textos.HumanizarYSinVacios.test_los_valores_ausentes_no_llegan_al_dom` | Node.js no está instalado | omitida | corre |
| 3 | `test_interfaz_textos.HumanizarYSinVacios.test_todos_los_mensajes_del_sistema_quedan_sin_codigos_internos` | Node.js no está instalado | omitida | corre |
| 4 | `test_interfaz_bloque_a.EtiquetasLegibles.test_cada_concepto_de_pago_tiene_etiqueta_legible` | Node.js no está disponible | omitida | corre |
| 5 | `test_interfaz_bloque_a.EtiquetasLegibles.test_cada_estado_de_pago_se_explica_y_solo_verificado_se_suma` | Node.js no está disponible | omitida | corre |
| 6 | `test_interfaz_bloque_a.EtiquetasLegibles.test_cada_tipo_de_solicitud_y_de_devolucion_tiene_etiqueta_legible` | Node.js no está disponible | omitida | corre |
| 7 | `test_interfaz_bloque_a.EtiquetasLegibles.test_un_valor_desconocido_se_muestra_tal_cual_en_lugar_de_ocultarse` | Node.js no está disponible | omitida | corre |
| 8 | `test_interfaz_formulario_cuentas.FormularioCrearCuentaEnNavegador.test_visibilidad_obligatoriedad_valor_y_carga_util_segun_el_rol` | «Prueba con navegador: defina EVENTOSNOVA_PRUEBAS_NAVEGADOR=1» (opt-in; además exige Node.js y Chrome) | omitida | omitida |

**Comparación 3 → 8 (Docker) y 0 → 1 (trabajo de pruebas).** En `4be166b` solo existía `test_interfaz_textos`, con 3 pruebas que necesitan Node.js: por eso Docker daba 3 omitidas y el trabajo de pruebas, que tiene Node.js, 0. El Bloque A añadió `test_interfaz_bloque_a` (4 pruebas que necesitan Node.js: +4 en Docker) y `test_interfaz_formulario_cuentas` (1 prueba opt-in con navegador: +1 en Docker y +1 en el trabajo de pruebas). 3 + 4 + 1 = 8 en Docker; 0 + 1 = 1 en el trabajo de pruebas. Las «3 omitidas» que varios documentos atribuyen al CI de Linux sobre `4be166b` corresponden al trabajo Docker, no al de pruebas.

## 7. Limitaciones conocidas

1. **Documentos con información obsoleta: resuelto** (sección 4.5). Quedan por actualizar únicamente los datos que dependen del despliegue (URL, capturas, Swagger en producción).
2. **Los valores de los Excel los calculó un programa propio**, no la aplicación Excel. Coinciden con un recálculo independiente y Excel volverá a calcular al abrir (`fullCalcOnLoad`).
3. **ADR con campos «No documentado»:** ADR-001 a 008 (Problema), ADR-003 (Consecuencias negativas e Implementación), ADR-004 (Implementación), ADR-009 (Contexto, Problema, Alternativas), ADR-010 (Contexto, Problema) y ADR-011 (Problema, Alternativas, Consecuencias positivas y negativas). Es fiel a los ADR originales, que no traían esos apartados.
4. **Cobertura:** el `coverage.json` y los logs de este paquete son de la medición del 03/11/2026, anterior al Bloque A. La cobertura del código actual (98.21 %) consta en la salida del CI, pero su `coverage.json` no está archivado aquí.
5. **Los logs de cobertura (`*.log`)** serían ignorados por la regla `*.log` del `.gitignore` del repositorio si se copiaran tal cual.
6. **Reporte HTML de cobertura** (85 archivos): es un artefacto generado (`htmlcov/` ya se ignora en el repositorio).
7. **Documentos de entrega antiguos** (`docs/entrega/`, generados el 29/10/2026) siguen existiendo como archivos locales sin seguimiento en el repositorio y no forman parte de este paquete.
8. **Nada de esto se ha copiado todavía al repositorio:** el paquete sigue únicamente en esta carpeta externa.

## 8. Ubicación de cada carpeta del paquete en el repositorio

El paquete se describe en este registro tal como se preparó (carpetas `01_ANALISIS/` a `05_ENTREGA_Y_DEFENSA/`). En el repositorio, el contenido quedó así (integración del 05/11/2026, rama `docs/integracion-bloque-b`):

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
