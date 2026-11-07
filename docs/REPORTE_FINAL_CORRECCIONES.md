# Reporte final de correcciones

Alcance: solo presentación y la limitación de datos que la API devuelve al proveedor. Sin migraciones, sin cambios de esquema, sin cambios de reglas de negocio.

| Corrección | Problema | Solución | Archivos | Pruebas | Resultado |
|---|---|---|---|---|---|
| COR-05 | La API del proveedor devolvía `condiciones`: texto de condiciones comerciales del contrato del Cliente, con importes | Se quitó el campo de `ServicioAsignadoViewModel` y de las dos tablas del proveedor | `src/application/cqrs.py`, `src/web/js/paginas/otras.js` | `test_seguridad` (nueva comprobación de claves exactas), `test_h01_h02_proveedores` (aserciones ajustadas) | Aprobada. Verificado también con las respuestas reales de la API |
| COR-12 | Contraseña siempre oculta, sin forma de revisarla | Botón Mostrar/Ocultar (`conOjo`) en inicio de sesión y en todo campo de contraseña de los formularios; no altera el valor | `src/web/js/ui.js`, `src/web/js/paginas/ingreso.js`, `src/web/css/app.css` | Navegador real (Chrome): alterna `password`/`text` | Aprobada |
| COR-02 | Lista de proveedores larga y sin búsqueda; los resúmenes mostraban el identificador | Cuadro de búsqueda en toda lista con más de 6 opciones; resumen con el nombre | `src/web/js/ui.js`, `src/web/js/acciones.js`, `app.css` | Navegador real contra la base manual (102 proveedores) | Aprobada: verificada en Chrome con 102 proveedores reales (búsqueda por nombre, el valor enviado sigue siendo el identificador, se muestra el nombre) |
| COR-13 | La lista de cuentas no se podía filtrar | Búsqueda por nombre, correo o proveedor; filtros de rol y estado; mensaje sin coincidencias | `src/web/js/paginas/cuentas.js` | Navegador real contra la base manual (lectura) | Aprobada |
| COR-07 | Riesgo de capturar un importe mayor al saldo sin darse cuenta | Advertencia en la confirmación; no se bloquea (B-4/B-5/X-14) | `src/web/js/acciones.js` | `test_interfaz_bloque_a` (advertencia en un párrafo propio, sin bloqueo) y Chrome: aparece con importe > saldo y no con importe = saldo; se llegó al resumen sin confirmar ningún pago | Aprobada |
| COR-08 | Duda sobre quién define la tarifa del cargo tardío | Solo texto del formulario: usar la tarifa autorizada | `src/web/js/acciones.js` | Suite completa | Aprobada como presentación; la regla no cambió |
| COR-11 | Riesgo de repetir la comunicación de la política | Aviso preventivo en el formulario | `src/web/js/acciones.js` | — | Parcial; sin bloqueo en backend |
| COR-06 | Se mostraban nombres internos (`SaldoContratoOriginal`, `CargoCambioTardio`, `servicio adicional`, `SE-012`) | Etiquetas legibles solo para mostrar; valores internos, filtros y envíos intactos | `src/web/js/negocio.js`, `paginas/evento.js`, `paginas/otras.js`, `acciones.js` | `test_interfaz_bloque_a` (contra los valores reales de `ConceptoPago`, `TipoSolicitud`, `TipoDevolucion`) y Chrome | Aprobada |
| COR-16 | El formulario de cambio no mostraba los datos actuales del evento | Valores iniciales tomados del evento; solo se envían si el usuario marca que el cambio modifica los datos | `src/web/js/acciones.js` | `test_interfaz_bloque_a`; Chrome (coincide con la API y abrir/cancelar no modifica el evento) | Aprobada |
| COR-17 | Un pago registrado sin verificar no se distinguía bien | Explicación por estado, columna «Pendiente de verificación» y aviso con el número de pagos sin verificar; el estado oficial no se reemplaza | `src/web/js/negocio.js`, `paginas/evento.js` | `test_interfaz_bloque_a` (cada `EstadoPago` tiene explicación; solo Verificado «se suma»); Chrome | Aprobada |
| COR-03 | Formulario de cuentas (C-03) | Conservado íntegro | ver historial local | `test_interfaz_formulario_cuentas`, navegador | Aprobada |

## Intento revertido
COR-08 se implementó primero en backend (tarifa leída de `EVENTOSNOVA_TARIFA_CARGO_TARDIO` y rechazo de cambios tardíos sin tarifa). Tras tu aclaración se **revirtió por completo**: `rutas_solicitudes.py`, `esquemas_operaciones.py` y `servicios.py` quedaron sin diferencias respecto del último commit. No se cambió ninguna prueba por esto.

## Ajuste de interfaz del Bloque A
Para que la advertencia de COR-07 sea claramente visible, el resumen de confirmación acepta párrafos separados por salto de línea y destaca el que empieza con «Atención:» (`src/web/js/ui.js`).

## No realizado
Nada de COR-06, COR-16 y COR-17 queda pendiente. Siguen sin implementarse COR-01 (mensajes del backend), COR-04 (saldo dentro de la etiqueta del importe), COR-09, COR-10 y COR-11 en backend (por ser cambios de reglas; ver la lista maestra).
