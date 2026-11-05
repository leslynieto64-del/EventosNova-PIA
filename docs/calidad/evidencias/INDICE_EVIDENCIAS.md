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
| `06_CI_CD/` | URL y número de la ejecución de CI, captura de los jobs «pruebas» y «docker» en verde y artefacto coverage.json. | 0 | Pendiente |
| `08_BLOQUE_A_CHROME/` | Capturas del recorrido en Chrome del Bloque A: búsqueda y filtros de cuentas, advertencia de excedente, precarga del cambio y vista del proveedor sin condiciones (1440 y 390 px) | 5 | Vigente (05/11/2026) |
| `07_DESPLIEGUE/` | URL pública, capturas de /health, /ready y /docs en producción, registro del preDeploy y del worker, commit o etiqueta desplegada. | 0 | Pendiente |



## Actualización del 05/11/2026

- CI: existen ejecuciones correctas sobre `main` (`4be166b`: 1,654 pruebas; run 41901496391), sobre el commit `9c72bc7` de la PR #2 (1,677 pruebas; run 42104865505) y sobre `main` tras la fusión (`0b16cf3`; 1,677 pruebas; run 42109720404; cobertura 98.21 %), pero sus capturas y artefactos **no se entregaron** en las fuentes: `06_CI_CD/` sigue pendiente.
- Despliegue: Render no está desplegado; `07_DESPLIEGUE/` sigue pendiente.
- Las 5 capturas del Bloque A son del entorno manual (127.0.0.1:8001) con datos de prueba.
