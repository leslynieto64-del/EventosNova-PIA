# ADR-002: SustitucionProveedor y EstadoCuenta como raíces de agregado independientes

| Campo | Contenido |
|---|---|
| Identificador | ADR-002 |
| Título | SustitucionProveedor y EstadoCuenta como raíces de agregado independientes |
| Fecha | 13/10/2026 |
| Estado | Aceptada (13/10/2026). Vigente. |
| Contexto | Una sustitución de proveedor es un proceso largo con alternativas sucesivas, y el servicio original debe seguir vigente hasta confirmar el reemplazo. Las reglas de saldo general, regularización y devoluciones abarcan varias obligaciones del mismo contrato. |
| Problema | No documentado como apartado independiente; el problema se expone en el contexto. |
| Decisión | Mantener SustitucionProveedor y EstadoCuenta como raíces propias (siete raíces en total), con referencias por identificador. |
| Alternativas consideradas | Sustitución como entidad de Contrato o de Evento: mezclaría el documento o la configuración con un proceso pendiente y bloquearía el Evento. Reutilizar SolicitudCambio: la inicia el proveedor y sus aprobaciones dependen del impacto. Una raíz por obligación de pago: las reglas que cruzan obligaciones solo podrían verificarse fuera del límite. |
| Consecuencias positivas | Beneficio: Evento no cambia hasta SustitucionProveedorConfirmada; las reglas financieras se protegen juntas. |
| Consecuencias negativas | Costo: más repositorios y reacciones a Domain Events. |
| Implementación | Decisión arquitectónica asociada: un EstadoCuenta por contrato, por lo que las consultas por evento usan listarPorEventoId(). |
| Referencias | Fuente: documento ADR de la Unidad 3 (ADR_Eventos_Nova_U3_ADR-001_a_004.docx, 13/10/2026) (texto conservado sin cambios)<br>SE-001, SE-012, BN-004, BN-005, BN-006; US-011, US-021, US-031; GL-056, GL-058, GL-059; CA-026, CA-046 a CA-054, CA-096 a CA-098.<br>Documento original de la Unidad 3: ADR_Eventos_Nova (13/10/2026). |
| Aprobación | Aceptada por el equipo en el entregable de la Unidad 3 (13/10/2026). Las fuentes no registran una aprobación externa específica (cliente o profesor). |

_Formato uniforme de 13 campos. El contenido se tomó del ADR registrado; cuando un campo no figura en él, se indica «No documentado». Las decisiones del equipo no se presentan como aprobaciones del cliente ni del profesor._
