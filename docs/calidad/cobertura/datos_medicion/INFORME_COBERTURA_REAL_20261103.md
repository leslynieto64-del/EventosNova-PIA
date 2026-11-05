# Informe de cobertura REAL — 2026-11-03

Medición ejecutada el 2026-11-03 (21:37–22:04) con la versión definitiva del repositorio (rama `fix/auditoria-integral`), sin modificar código, configuración ni bases. Sustituye a `INFORME_COBERTURA_ACTUAL.md` (que declaraba «no medido»). Las cifras históricas (98,82 %, 98,40 %) **no** deben usarse.

## Resultado

| Métrica | Valor |
|---|---|
| Pruebas ejecutadas | **1654** (82 módulos de prueba, 8 grupos secuenciales, todos con código de salida 0; sin fallos, errores ni omitidas) |
| Cobertura de líneas (sentencias) | **98.19 %** (6572 de 6693; sin cubrir 121) |
| Cobertura de ramas | **93.20 %** (1303 de 1398) |
| Mínimo del PIA (80 %) | **Cumple** (`medicion_actual/coverage_verificacion_80.txt`: «OK: cumple el mínimo de 80 %») |
| Módulos de `src/` medidos | **76** (ninguno con 0 %) |
| Base de datos | **`eventosnova_regresion_test`** exclusivamente (revisión Alembic 0009, PostgreSQL 18.6; 0 conexiones previas verificadas con consultas de solo lectura) |
| Herramienta | coverage.py 7.16.2 + `unittest`; `.coveragerc` del repositorio (`source = src`, `branch = True`) |
| Script | `medir_cobertura_aislada.py` (esta carpeta) con `--repo` el repositorio y `--salida` fuera de él |

Duración por grupo (s): 73, 327, 118, 227, 349, 250, 234, 55. Pruebas por grupo: 212, 239, 180, 213, 242, 235, 179, 154 (= 1654).

Nota: el total de sentencias (6693) incluye `src/paquete_pia` y `src/ejecucion_paquete`; el total documentado en el repositorio al 28/10 (5513) no es comparable.

## Por capa

| Capa | Módulos | Líneas | Ramas |
|---|---:|---:|---:|
| `src/(raíz src)` | 1 | 100.00 % (0/0) | 100.00 % (0/0) |
| `src/api` | 17 | 98.20 % (928/945) | 89.36 % (84/94) |
| `src/application` | 8 | 96.75 % (1667/1723) | 88.81 % (357/402) |
| `src/domain` | 14 | 99.14 % (1739/1754) | 95.85 % (393/410) |
| `src/ejecucion_paquete` | 9 | 99.17 % (594/599) | 96.62 % (143/148) |
| `src/infrastructure` | 19 | 98.77 % (1288/1304) | 95.00 % (228/240) |
| `src/paquete_pia` | 8 | 96.74 % (356/368) | 94.23 % (98/104) |

## Los 76 módulos medidos

| Módulo | Cobertura % (sentencias+ramas) | Líneas sin cubrir | Ramas % |
|---|---:|---:|---:|
| `src/__init__.py` | 100.0 | 0 | 100.0 |
| `src/api/__init__.py` | 100.0 | 0 | 100.0 |
| `src/api/dependencias.py` | 100.0 | 0 | 100.0 |
| `src/api/errores.py` | 100.0 | 0 | 100.0 |
| `src/api/esquemas.py` | 100.0 | 0 | 100.0 |
| `src/api/esquemas_operaciones.py` | 100.0 | 0 | 100.0 |
| `src/api/limites.py` | 96.6 | 2 | 100.0 |
| `src/api/main.py` | 95.9 | 1 | 78.6 |
| `src/api/rutas_comunes.py` | 100.0 | 0 | 100.0 |
| `src/api/rutas_consultas.py` | 96.3 | 1 | 50.0 |
| `src/api/rutas_contratacion.py` | 100.0 | 0 | 100.0 |
| `src/api/rutas_eventos.py` | 100.0 | 0 | 100.0 |
| `src/api/rutas_pagos.py` | 100.0 | 0 | 100.0 |
| `src/api/rutas_propuestas.py` | 100.0 | 0 | 100.0 |
| `src/api/rutas_proveedores.py` | 96.8 | 1 | 90.0 |
| `src/api/rutas_seguridad.py` | 87.2 | 11 | 50.0 |
| `src/api/rutas_solicitudes.py` | 100.0 | 0 | 100.0 |
| `src/api/seguridad.py` | 98.3 | 1 | 95.8 |
| `src/application/__init__.py` | 100.0 | 0 | 100.0 |
| `src/application/cqrs.py` | 100.0 | 0 | 100.0 |
| `src/application/puertos.py` | 100.0 | 0 | 100.0 |
| `src/application/reacciones.py` | 94.7 | 2 | 84.2 |
| `src/application/reloj.py` | 100.0 | 0 | 100.0 |
| `src/application/resultados.py` | 100.0 | 0 | 100.0 |
| `src/application/seguridad.py` | 88.2 | 21 | 77.2 |
| `src/application/servicios.py` | 95.4 | 33 | 92.7 |
| `src/domain/__init__.py` | 100.0 | 0 | 100.0 |
| `src/domain/base.py` | 100.0 | 0 | 100.0 |
| `src/domain/contrato.py` | 98.2 | 1 | 95.5 |
| `src/domain/especificacion.py` | 100.0 | 0 | 100.0 |
| `src/domain/especificaciones.py` | 100.0 | 0 | 100.0 |
| `src/domain/estado_cuenta.py` | 98.8 | 2 | 96.8 |
| `src/domain/evento.py` | 93.5 | 9 | 87.1 |
| `src/domain/eventos_dominio.py` | 100.0 | 0 | 100.0 |
| `src/domain/maquina_estados.py` | 100.0 | 0 | 100.0 |
| `src/domain/propuesta.py` | 100.0 | 0 | 100.0 |
| `src/domain/proveedor.py` | 93.2 | 2 | 83.3 |
| `src/domain/servicios_dominio.py` | 98.3 | 0 | 87.5 |
| `src/domain/solicitudes.py` | 99.6 | 1 | 98.9 |
| `src/domain/valores.py` | 100.0 | 0 | 100.0 |
| `src/ejecucion_paquete/__init__.py` | 100.0 | 0 | 100.0 |
| `src/ejecucion_paquete/__main__.py` | 92.6 | 1 | 87.5 |
| `src/ejecucion_paquete/casos.py` | 97.9 | 1 | 92.9 |
| `src/ejecucion_paquete/evidencias.py` | 97.1 | 2 | 92.9 |
| `src/ejecucion_paquete/mapeo.py` | 100.0 | 0 | 100.0 |
| `src/ejecucion_paquete/oraculo.py` | 94.4 | 1 | 83.3 |
| `src/ejecucion_paquete/reglas_paquete.py` | 100.0 | 0 | 100.0 |
| `src/ejecucion_paquete/totales.py` | 100.0 | 0 | 100.0 |
| `src/ejecucion_paquete/transiciones.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/__init__.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/adaptadores.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/composicion.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/esquema_postgresql.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/persistencia/__init__.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/persistencia/codec_eventos.py` | 99.2 | 0 | 97.6 |
| `src/infrastructure/persistencia/composicion_persistente.py` | 90.5 | 3 | 75.0 |
| `src/infrastructure/persistencia/conexion.py` | 98.1 | 2 | 100.0 |
| `src/infrastructure/persistencia/configuracion.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/persistencia/errores.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/persistencia/mapeadores.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/persistencia/outbox_sql.py` | 97.4 | 3 | 95.8 |
| `src/infrastructure/persistencia/preparacion.py` | 89.7 | 4 | 66.7 |
| `src/infrastructure/persistencia/repositorios_sql.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/persistencia/trabajador_outbox.py` | 96.9 | 1 | 92.9 |
| `src/infrastructure/persistencia/unidad_trabajo_sql.py` | 98.3 | 1 | 100.0 |
| `src/infrastructure/repositorios_memoria.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/seguridad_memoria.py` | 100.0 | 0 | 100.0 |
| `src/infrastructure/unidad_trabajo.py` | 95.6 | 2 | 90.0 |
| `src/paquete_pia/__init__.py` | 100.0 | 0 | 100.0 |
| `src/paquete_pia/__main__.py` | 94.1 | 1 | 83.3 |
| `src/paquete_pia/dto.py` | 100.0 | 0 | 100.0 |
| `src/paquete_pia/errores.py` | 93.5 | 1 | 83.3 |
| `src/paquete_pia/esquema.py` | 100.0 | 0 | 100.0 |
| `src/paquete_pia/formatos.py` | 97.3 | 2 | 100.0 |
| `src/paquete_pia/lector.py` | 95.3 | 5 | 96.0 |
| `src/paquete_pia/manifiesto.py` | 93.9 | 3 | 91.7 |

La columna 2 es `percent_covered` de coverage.json (combina sentencias y ramas por archivo); las cifras globales son las de la tabla de resultados. Líneas exactas sin cubrir: `medicion_actual/coverage_reporte.txt`.

## Módulos con menor cobertura (candidatos a pruebas adicionales; no necesarios para el 80 %)
- `src/api/rutas_seguridad.py`: 87.2 % (11 líneas sin cubrir)
- `src/application/seguridad.py`: 88.2 % (21 líneas sin cubrir)
- `src/infrastructure/persistencia/preparacion.py`: 89.7 % (4 líneas sin cubrir)
- `src/infrastructure/persistencia/composicion_persistente.py`: 90.5 % (3 líneas sin cubrir)
- `src/ejecucion_paquete/__main__.py`: 92.6 % (1 líneas sin cubrir)
- `src/domain/proveedor.py`: 93.2 % (2 líneas sin cubrir)

## Archivos de esta medición (`medicion_actual/`)
- `html/index.html` y 84 archivos acompañantes (85 archivos; incluye el `.gitignore` con `*` que crea coverage.py). Más `html/Reporte_Cobertura_Eventos_Nova.html`: copia **idéntica byte a byte** de `index.html` (entregable 27), en la misma carpeta para conservar las rutas relativas; comprobado que sus 82 enlaces locales y los 3710 enlaces de las 80 páginas HTML resuelven a archivos existentes (0 rotos).
- `coverage.json`, `coverage_reporte.txt`, `coverage_verificacion_80.txt`, `ejecucion_consola.txt`, `cobertura_grupo1.log` … `cobertura_grupo8.log`.
- Son copias de los originales en `MEDICION_COBERTURA_20261103\` (no se movieron ni borraron).

## Conclusión
Con 1654 pruebas aprobadas, la cobertura de líneas (98,19 %) y de ramas (93,20 %) supera el mínimo del 80 % exigido por el PIA (criterio 4.1). Entregable 27: **completo** (`medicion_actual/html/Reporte_Cobertura_Eventos_Nova.html`). Entregable 28: **completado** (`Resumen_Cobertura_Eventos_Nova.pdf`, 8 páginas; copia idéntica con nombre alternativo `Reporte_Cobertura_Eventos_Nova.pdf`).

## Entregable 28 — PDF de cobertura (COMPLETADO)
Archivo: `04_CALIDAD_PRUEBAS/cobertura/Resumen_Cobertura_Eventos_Nova.pdf` (nombre oficial del entregable 28; 8 páginas). `Reporte_Cobertura_Eventos_Nova.pdf` es una copia idéntica byte a byte con nombre alternativo. Generado con Chrome headless desde HTML producido por `generar_reporte_cobertura_pdf.py`, que lee `medicion_actual/` y **falla si las cifras no coinciden** entre `coverage.json`, `coverage_reporte.txt` y `coverage_verificacion_80.txt`. Fuentes utilizadas (todas en `medicion_actual/`):
1. **Cifras globales**: `coverage_verificacion_80.txt` (líneas 98,19 % = 6572/6693; ramas 93,20 % = 1303/1398; «OK: cumple el mínimo de 80 %») y `coverage.json` → `totals`.
2. **Por módulo y líneas sin cubrir**: `coverage_reporte.txt` (76 módulos) y la tabla de este informe (por capa y por módulo).
3. **Pruebas y resultado**: `ejecucion_consola.txt` (8 grupos, 1654 pruebas, código 0, duración por grupo) y `cobertura_grupo1.log` … `cobertura_grupo8.log` (salida de `unittest`).
4. **Método**: herramienta coverage.py 7.16.2 + `unittest`; configuración `.coveragerc` (`source = src`, `branch = True`); comando y garantías en `medir_cobertura_aislada.py`; base exclusiva `eventosnova_regresion_test` (Alembic 0009, PostgreSQL 18.6); fecha 2026-11-03 21:37–22:04.
5. **Criterio PIA**: 80 % mínimo (`00_PIA_Y_CRITERIOS/criterios_PIA/PIA_CLN_Proyecto_Integrador_AD2026.pdf`, calidad + defensa, punto 1).
6. **Enlace al informe completo**: `html/Reporte_Cobertura_Eventos_Nova.html`.
7. **No usar** `medicion_anterior_31oct_1574_pruebas_NO_VIGENTE/` ni las cifras históricas de `tests/evidencias/cobertura*.txt`.
Contenido sugerido: portada del equipo, resumen (tabla de resultados), cobertura por capa, módulos con menor cobertura, método y aislamiento, conclusión de cumplimiento.
