# language: es
# Eventos Nova - Equipo 16 - Especificación Gherkin derivada de los criterios de aceptación aprobados.
# Fuente: Historias de usuario de Eventos Nova, versión 2.0 consolidada (US-001 a US-033, CA-001 a CA-114).
# Estos escenarios son especificación ejecutable; la verificación automatizada vigente se realiza con unittest (ver etiquetas @prueba).

Característica: Cancelación del evento y devoluciones

  # US-026 - Como Cliente, quiero solicitar la cancelación de mi evento después de confirmada la contratación y antes de que inicie el evento, para informar que ya no deseo continuar con la organización.
  @US-026 @CA-084 @excepcional
  # @prueba: test_etapa9_casos_de_uso.py, test_evento_maquina_estados.py
  Escenario: CA-084
    Dado que la contratación del evento está confirmada y el evento aún no ha iniciado
    Cuando el Cliente solicite la cancelación
    Entonces la solicitud debe quedar registrada para su revisión

  # US-027 - Como Coordinador, quiero revisar y gestionar las solicitudes de cancelación de los eventos verificando que la contratación esté confirmada y que el evento aún no haya iniciado, para registrar la cancelación o el rechazo, revisar los pagos relacionados y comunicar el resultado a las personas involucradas.
  @US-027 @CA-085 @excepcional
  Escenario: CA-085
    Dado que existe una solicitud de cancelación
    Cuando el Coordinador la reciba
    Entonces debe poder consultar la información del evento y las condiciones del contrato

  @US-027 @CA-086 @excepcional
  Escenario: CA-086
    Dado que existe una solicitud de cancelación
    Cuando el Coordinador la revise
    Entonces debe poder identificar el estado del evento y las condiciones del contrato

  @US-027 @CA-087 @excepcional
  # @prueba: test_decisiones_stakeholder.py, test_etapa9_casos_de_uso.py, test_h08_inicio_evento.py, test_h13_criterios_aceptacion.py
  Escenario: CA-087
    Dado que la contratación está confirmada y el evento aún no ha iniciado
    Cuando el Coordinador determine que la cancelación solicitada por el Cliente procede y la registre
    Entonces la información del evento deberá quedar actualizada, la cancelación deberá comunicarse al Cliente, a Administración y a los proveedores involucrados, y deberá dejarse constancia de las comunicaciones realizadas. Deberá informarse al Cliente que no se reembolsarán los pagos relacionados con el evento conforme a la política de no reembolso incluida en el contrato. Esta regla se refiere a la cancelación del evento y se distingue del cierre de una solicitud independiente no realizada mientras el Evento continúa vigente. Las solicitudes de cambio, servicio adicional o sustitución que sigan en trámite se cierran con el motivo «Evento cancelado»; las ya confirmadas no se cierran por esta regla. Si una solicitud confirmada todavía no se había aplicado al evento, la operación no se aplica al evento cancelado: la solicitud conserva su confirmación y se registra, para su revisión, que la operación no pudo aplicarse por la cancelación

  @US-027 @CA-088 @negativo
  # @prueba: test_etapa9_casos_de_uso.py, test_evento_maquina_estados.py, test_h08_inicio_evento.py, test_h08_intervalo_pendiente.py
  Escenario: CA-088
    Dado que existe una solicitud de cancelación y el evento ya inició
    Cuando el Coordinador la revise
    Entonces debe rechazar la solicitud, informar al Cliente que la cancelación no procede y mantener la ejecución del evento

  # US-028 - Como Administración, quiero revisar el contrato y los pagos relacionados con la cancelación de un evento, ya sea solicitada por el Cliente o derivada de la falta de liquidación del saldo pendiente del contrato original dentro del plazo establecido, para identificar los pagos realizados y el saldo pendiente, cuando exista, y dejar registrada la aplicación de la política de no reembolso.
  @US-028 @CA-089 @excepcional
  # @prueba: test_correcciones_etapas_3_a_7.py, test_h13_criterios_aceptacion.py
  Escenario: CA-089
    Dado que existe una cancelación registrada, ya sea solicitada por el Cliente o registrada por el Coordinador debido a la falta de liquidación del saldo pendiente del contrato original dentro del plazo establecido
    Cuando Administración revise la información del evento
    Entonces debe poder consultar el contrato relacionado

  @US-028 @CA-090 @excepcional
  # @prueba: test_correcciones_etapas_3_a_7.py
  Escenario: CA-090
    Dado que existe una cancelación registrada, ya sea solicitada por el Cliente o registrada por el Coordinador debido a la falta de liquidación del saldo pendiente del contrato original dentro del plazo establecido
    Cuando Administración revise la información de pagos
    Entonces debe poder consultar los pagos realizados del evento

  @US-028 @CA-091 @excepcional
  # @prueba: test_correcciones_etapas_3_a_7.py
  Escenario: CA-091 - Escenario único: revisión administrativa de la cancelación
    Dado que un Evento fue cancelado a solicitud del Cliente o por falta de regularización del saldo del contrato original
    Cuando Administración registre la revisión del contrato y de los pagos relacionados
    Entonces se registran el resultado, los pagos realizados y el saldo pendiente, si existe, y se comunican al Coordinador
    Y se deja constancia, una sola vez por cancelación y con la relación de los pagos, de que no corresponde reembolso del anticipo, de los pagos del contrato original, de cambios, cargos por cambio tardío, servicios adicionales, excedentes del anticipo ni pagos tardíos
    Y no se genera ninguna devolución automática y la regla no sustituye la devolución SE-012 de solicitudes cerradas con el Evento vigente

  @US-028 @CA-114 @excepcional
  Escenario: CA-114
    Dado que el Evento está Cancelado y existen un excedente del anticipo (por ejemplo, 1 000 sobre un anticipo aceptado de 4 000) o un pago tardío relacionado con el Evento
    Cuando Administración registre y verifique esos pagos
    Entonces no se generará ninguna devolución y la constancia de no reembolso, registrada una sola vez por cancelación, deberá incluir la relación de los pagos. Un Evento Cerrado sin contratación nunca es un Evento Cancelado, por lo que esta regla no se le aplica

  # US-031 - Como Administración, quiero registrar y ejecutar las devoluciones que correspondan por cambios, servicios adicionales o sustituciones que no se realizaron con el Evento vigente, para mantener el control financiero de los importes devueltos y dejar constancia de su motivo, importe, fecha y comprobante.
  @US-031 @CA-097 @excepcional
  # @prueba: test_e3g_cargo_tardio_y_conceptos.py, test_estado_cuenta_maquina_estados.py, test_etapa9_casos_de_uso.py, test_h09_pago_pendiente_al_cierre.py, test_h09_plazo_devolucion.py, test_h13_criterios_aceptacion.py
  Escenario: CA-097
    Dado que una solicitud de cambio, servicio adicional o sustitución se cerró sin confirmarse y la operación no se realizó
    Cuando se registre el cierre de esa solicitud
    Entonces se dejarán sin efecto los importes pendientes de cobro que correspondan exclusivamente a ella, independientemente de que el Evento esté cancelado. Si el Evento no está cancelado, Administración deberá devolver los importes efectivamente recibidos por esa operación dentro de los cinco días hábiles siguientes al cierre, una vez verificado el importe (si el pago se registra después del cierre, el plazo corre desde su registro), conforme a SE-012. En una sustitución, se devolverá únicamente el importe adicional atribuible al reemplazo no realizado. No se devolverán por este motivo los pagos del contrato original ni otros conceptos independientes. Si el Evento se cancela, no se realizará devolución y se aplicará la política de no reembolso correspondiente a la cancelación del Evento

  @US-031 @CA-098 @negativo
  # @prueba: test_estado_cuenta_maquina_estados.py, test_etapa9_casos_de_uso.py, test_h09_pago_pendiente_al_cierre.py, test_h09_plazo_devolucion.py, test_h13_criterios_aceptacion.py, test_integraciones_simuladas.py
  Escenario: CA-098
    Dado que corresponde una devolución por una operación no realizada mientras el Evento no está cancelado
    Cuando Administración la efectúe
    Entonces deberá registrar el concepto y la solicitud asociados, el importe, el motivo, la fecha de devolución y el comprobante correspondiente, e informar al Coordinador para que comunique el resultado al Cliente. La devolución deberá efectuarse dentro de los cinco días hábiles siguientes al cierre de la solicitud, una vez verificado el importe; si el pago se registra después del cierre, el plazo corre desde su registro. La devolución no podrá superar el importe efectivamente recibido por el pago al que corresponde y cada pago generará, como máximo, una devolución. Esta devolución es distinta de la devolución del anticipo (CA-102 a CA-105)
