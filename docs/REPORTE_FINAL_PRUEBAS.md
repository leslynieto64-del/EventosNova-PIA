# Reporte final de pruebas

Estados: **Aprobada**, **Fallida**, **Parcial**, **No ejecutada**. Una respuesta 200 no se tomó como prueba de que una función es correcta: cada fila indica qué se comprobó.

| Prueba | Resultado | Evidencia | Observaciones |
|---|---|---|---|
| Suite automatizada completa (1,677 pruebas) en base aislada `eventosnova_regresion_test` | Aprobada | 1,677 ejecutadas, 0 fallos, 0 errores, 1 omitida (prueba de navegador opt-in). Son 1,665 de referencia + 12 nuevas (`test_interfaz_bloque_a`) | Una corrida intermedia falló en `test_auditoria_requisitos` porque una prueba nueva mencionaba el código de una regla y el generador de trazabilidad la contó; se quitó la mención (no se tocó el documento generado) y la corrida final quedó limpia |
| Seguridad y permisos (75) | Aprobada | `test_seguridad.py`, incluye nueva comprobación de claves exactas de la vista del proveedor | — |
| Interfaz web (32) y operaciones de API (44) | Aprobada | Corridas dirigidas | 1 omitida por diseño |
| Migraciones (Alembic 0001–0009) | Aprobada | `test_migraciones_ciclo` y revisión 0009 en la base manual | Base normal `eventosnova` sigue en 0004, sin tocar |
| Navegador real (Chrome), recorrido de los 3 roles (30 comprobaciones, `scripts/probar_bloque_a_navegador.mjs`) | Aprobada | 30 de 30, repetido 3 veces. Administración (cuentas, filtros, búsqueda en lista de 102 proveedores, ojo de contraseña, advertencia de excedente, etiquetas, pagos de la boda), Coordinación (acciones de solicitudes, sin registrar pagos ni cuentas, precarga del cambio) y Proveedor (solo sus servicios, sin condiciones ni importes, 403 en lo administrativo, menú reducido, móvil 390 px sin desborde, sin errores de consola) | Solo lectura: los formularios se abren y se cancelan; la boda conserva sus 7 pagos. Una falla puntual de una corrida fue un tiempo de carga del propio script y se corrigió con una espera real |
| `/health`, `/ready`, `/app/`, `/docs` en el entorno manual con la imagen nueva | Aprobada | Todos HTTP 200 | Imagen `eventosnova-app:cierre-integral`, solo servicios manuales |
| Privacidad del proveedor sobre la boda real | Aprobada | Proveedor alterno ve el evento; el original ya no (404); cruce entre proveedores y endpoints privilegiados dan 403 | Antes de COR-05 la respuesta incluía las condiciones del contrato; ya no |
| Ronda 2 sobre la boda: cambio de horario y menú | Aprobada | Solicitudes confirmadas, verificadas por SQL | Sin duplicados |
| Ronda 2: servicio adicional Fotografía $1,200 | Aprobada | Solicitud confirmada, obligación y pago verificados | — |
| Ronda 2: sustitución de proveedor sin costo | Aprobada | Banquete reasignado al proveedor alterno y confirmado | — |
| Ronda 2: saldo pendiente | Aprobada | 7 pagos verificados que suman 12,700.00 frente a obligaciones 3,000 + 7,000 + 1,500 + 1,200 | Coincide con lo acordado |
| Reglas de fechas especiales con fecha controlada | Aprobada | Pruebas automatizadas de cambio tardío, servicio adicional fuera de plazo y plazos hábiles dentro de la suite | No se añadieron pruebas nuevas |
| Cambio tardío (Ronda 2 pendiente) | Aprobada | Evento nuevo a 5 días naturales: cargo por cambio tardío de 500.00 (valor de prueba) con plazo de 24 horas, un anexo, pago verificado, cambio Confirmada y horario 19:00 → 20:00; sin duplicados (SQL) | Con la hora real del servidor y un evento independiente, no con la boda: el reloj controlado solo existe en las pruebas automatizadas |
| Servicio adicional fuera de plazo (Ronda 2 pendiente) | Aprobada | Evento nuevo a 4 días naturales: «No procedente» (menos de cinco días naturales), sin obligaciones ni anexos nuevos (SQL) | El saldo de ese evento figura «Pendiente» pese a estar pagado: lo pagué después de su plazo (regla aprobada D-2). Es un efecto de las fechas elegidas |
| Advertencia de excedente en pagos (COR-07) | Aprobada | Chrome: aparece como bloque destacado con importe > saldo y desaparece con importe = saldo; `test_interfaz_bloque_a` comprueba que no hay bloqueo | No se confirmó ningún pago |
| Permisos por rol en navegador | Aprobada | Incluido en el recorrido de 30 comprobaciones | — |
| Flujo de cuentas de proveedor con datos reales en navegador | Parcial | Formulario verificado sin enviar | No se creó ninguna cuenta |
| COR-06, COR-16 y COR-17 (presentación) | Aprobada | `test_interfaz_bloque_a` (12 pruebas contra los valores reales del dominio) y Chrome | Ningún valor interno, filtro ni envío a la API cambió |
| Calidad del CI: Alembic cabeza única (0009), SQL offline y cobertura mínima | Aprobada | `alembic heads` = 0009; `upgrade head --sql` sin errores; cobertura de sentencias 98.19 % (6,572 de 6,693), ramas 93.20 %; mínimo exigido 80 % | `docker compose config` del CI no se ejecutó en este bloque |
| `/health`, `/ready`, `/app/`, `/docs` en el entorno manual (imagen `eventosnova-app:bloque-a`) | Aprobada | Todos HTTP 200 | Solo servicios manuales recreados |
| Bases: manual en 0009 y normal en 0004 | Aprobada | Manual 0009; normal `eventosnova` 0004; contenedores del puerto 8000 sin cambios (12 h en marcha) | — |
| Restricciones | Cumplidas | Sin migraciones, sin commit/push/merge/despliegue, base normal y puerto 8000 intactos | — |
