# ADR-004: Reacciones a Domain Events después del commit, en transacciones propias, con Outbox propuesto

| Campo | Contenido |
|---|---|
| Identificador | ADR-004 |
| Título | Reacciones a Domain Events después del commit, en transacciones propias, con Outbox propuesto |
| Fecha | 13/10/2026 |
| Estado | Aceptada (13/10/2026). Modificada por ADR-005: el Outbox es persistente.<br>El riesgo señalado (Outbox en memoria que no sobrevive a un reinicio) quedó resuelto con ADR-005: el Outbox es persistente (outbox_evento, outbox_reaccion) y lo despacha el trabajador trabajador_outbox. |
| Contexto | Confirmar una operación afecta otros agregados (por ejemplo, ContratacionConfirmada cambia Evento y EstadoCuenta). Modificar varias raíces en el método de origen rompería los límites de agregado; publicar antes del commit comunicaría hechos que podrían revertirse. |
| Problema | No documentado como apartado independiente; el problema se expone en el contexto. |
| Decisión | Cada operación de origen confirma su raíz (excepción justificada: comunicarSolicitudPago()). Los Domain Events se guardan con el commit en un Outbox y un despachador ejecuta reacciones idempotentes, cada una en su transacción. |
| Alternativas consideradas | Una sola transacción con todos los agregados: acoplamiento y bloqueos. Publicación en memoria después del commit sin registro: se pierden eventos si el proceso falla. Bus de mensajes: desproporcionado para el alcance. |
| Consecuencias positivas | Beneficio: cada reacción se reintenta sin repetir las ya procesadas y sin duplicar efectos (comprobado con pruebas sobre el Outbox en memoria). |
| Consecuencias negativas | Costo: consistencia eventual entre agregados y necesidad de idempotencia.<br>Riesgo: en el código base el Outbox vive en memoria, por lo que no sobrevive a un reinicio.<br>Trabajo posterior: Outbox persistente en la misma base de datos que los agregados. Una operación confirmada antes del inicio del Evento se aplica aunque su reacción llegue después del inicio (O-02 resuelta). Si el Evento se canceló antes de aplicarla, la operación no se aplica, la configuración no cambia y la solicitud conserva su confirmación; el registro del Outbox queda en «Revisión» con el motivo (BN-008). |
| Implementación | No documentado. |
| Referencias | Fuente: documento ADR de la Unidad 3 (ADR_Eventos_Nova_U3_ADR-001_a_004.docx, 13/10/2026) (texto conservado sin cambios)<br>BN-006, BN-009, SE-012; US-008, US-010, US-021; CA-019, CA-021, CA-051, CA-070, CA-071, CA-096; hallazgos H-01, H-02, H-03.<br>Documento original de la Unidad 3: ADR_Eventos_Nova (13/10/2026). |
| Aprobación | Aceptada por el equipo en el entregable de la Unidad 3 (13/10/2026). Las fuentes no registran una aprobación externa específica (cliente o profesor). |

_Formato uniforme de 13 campos. El contenido se tomó del ADR registrado; cuando un campo no figura en él, se indica «No documentado». Las decisiones del equipo no se presentan como aprobaciones del cliente ni del profesor._
