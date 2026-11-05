# ADR-001: Domain Model como patrón principal de lógica de negocio

| Campo | Contenido |
|---|---|
| Identificador | ADR-001 |
| Título | Domain Model como patrón principal de lógica de negocio |
| Fecha | 13/10/2026 |
| Estado | Aceptada (13/10/2026). Vigente. |
| Contexto | Las reglas relacionan propuestas, contratos, eventos, solicitudes, proveedores y pagos, con estados, plazos y aprobaciones que deben cumplirse antes de confirmar una operación (BN-002 a BN-005, BN-009). |
| Problema | No documentado como apartado independiente; el problema se expone en el contexto. |
| Decisión | Domain Model con agregados que protegen sus invariantes, porque permite ubicar cada regla en el concepto responsable y evitar confirmaciones inválidas. |
| Alternativas consideradas | Transaction Script: sencillo, pero acumularía validaciones de pagos, plazos y autorizaciones en procedimientos extensos. Table Module: organiza operaciones por tabla, pero las reglas que cruzan varios conceptos requerirían coordinación entre módulos. |
| Consecuencias positivas | Beneficio: reglas localizadas y verificables con pruebas por agregado. |
| Consecuencias negativas | Costo: mayor esfuerzo inicial de diseño.<br>Riesgo: límites de agregado mal definidos; se mitigó en la Etapa 3. |
| Implementación | Validación con el BPMN: el modelo se contrastó con el BPMN maestro completamente desplegado y con los subprocesos SP-01 a SP-08 (diagramas/bpmn). Cada raíz corresponde a un tramo del proceso: Propuesta (SP-01); Contrato y EstadoCuenta (SP-02, SP-06 y SE-012, SP-08); Evento (inicio, ejecución, finalización y cancelación, SP-07); SolicitudCambio (SP-03); SolicitudServicioAdicional (SP-04) y SustitucionProveedor (SP-05). El BPMN comprueba el estado del Evento al recibir el aviso del proveedor: el aviso recibido después del inicio quedó definido como fuera del alcance del sistema y, con el Evento cancelado, no se confirma ninguna sustitución (BN-008), lo que el prototipo respeta. |
| Referencias | Fuente: documento ADR de la Unidad 3 (ADR_Eventos_Nova_U3_ADR-001_a_004.docx, 13/10/2026) (texto conservado sin cambios)<br>BN-002, BN-003, BN-004, BN-005, BN-006, BN-009; US-004, US-005, US-008, US-024, US-025; CA-007 a CA-010, CA-015 a CA-019, CA-038, CA-041, CA-067, CA-082; CU-01 a CU-05.<br>Documento original de la Unidad 3: ADR_Eventos_Nova (13/10/2026). |
| Aprobación | Aceptada por el equipo en el entregable de la Unidad 3 (13/10/2026). Las fuentes no registran una aprobación externa específica (cliente o profesor). |

_Formato uniforme de 13 campos. El contenido se tomó del ADR registrado; cuando un campo no figura en él, se indica «No documentado». Las decisiones del equipo no se presentan como aprobaciones del cliente ni del profesor._
