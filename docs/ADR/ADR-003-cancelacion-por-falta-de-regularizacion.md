# ADR-003: La cancelación por falta de regularización la registra el Coordinador

| Campo | Contenido |
|---|---|
| Identificador | ADR-003 |
| Título | La cancelación por falta de regularización la registra el Coordinador |
| Fecha | 13/10/2026 |
| Estado | Aceptada (13/10/2026). Vigente; reforzada por S-3 (ADR-011). |
| Contexto | En una revisión anterior la reacción a PlazoRegularizacionVencido cancelaba el Evento automáticamente. Las fuentes indican que Administración revisa los pagos e informa al Coordinador, y que este registra la cancelación, indica el motivo e informa a los involucrados. |
| Problema | No documentado como apartado independiente; el problema se expone en el contexto. |
| Decisión | Conservar PlazoRegularizacionVencido como hecho verificado por Administración; su reacción solo avisa. El Coordinador ejecuta registrarCancelacionPorFaltaDeRegularizacion() mediante su Command; Evento exige la verificación previa y el motivo. |
| Alternativas consideradas | Cancelación automática por reacción: contradice la regla y omite el motivo del Coordinador. Tarea manual sin Domain Event: perdería el aviso trazable del vencimiento. |
| Consecuencias positivas | Beneficio: responsabilidades del negocio respetadas y probadas. El Coordinador registra la cancelación en cuanto recibe el aviso de Administración y antes del inicio del Evento; después del inicio ya no procede y el adeudo se conserva (P-08 resuelto). Este escenario se distingue del cierre por anticipo no recibido, que deja el Evento Cerrado sin contratación. |
| Consecuencias negativas | No documentado. |
| Implementación | No documentado. |
| Referencias | Fuente: documento ADR de la Unidad 3 (ADR_Eventos_Nova_U3_ADR-001_a_004.docx, 13/10/2026) (texto conservado sin cambios)<br>BN-005, BN-008, SE-007, SE-010 (distinción del cierre sin contratación); CU-02, CU-03; US-010, US-011; CA-020, CA-021, CA-025, CA-027; hallazgo H-10; P-08 resuelto.<br>Documento original de la Unidad 3: ADR_Eventos_Nova (13/10/2026). |
| Aprobación | Aceptada por el equipo en el entregable de la Unidad 3 (13/10/2026). Las fuentes no registran una aprobación externa específica (cliente o profesor). |

_Formato uniforme de 13 campos. El contenido se tomó del ADR registrado; cuando un campo no figura en él, se indica «No documentado». Las decisiones del equipo no se presentan como aprobaciones del cliente ni del profesor._
