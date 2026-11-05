# language: es
# Eventos Nova - Equipo 16 - Especificación Gherkin derivada de los criterios de aceptación aprobados.
# Fuente: Historias de usuario de Eventos Nova, versión 2.0 consolidada (US-001 a US-033, CA-001 a CA-114).
# Estos escenarios son especificación ejecutable; la verificación automatizada vigente se realiza con unittest (ver etiquetas @prueba).

Característica: Solicitudes de cambio

  # US-017 - Como Coordinador, quiero registrar los cambios solicitados después de la contratación, para mantener actualizada la información del evento.
  @US-017 @CA-037 @positivo
  # @prueba: test_h13_criterios_aceptacion.py
  Escenario: CA-037
    Dado que el Cliente solicita un cambio después de la contratación
    Cuando el Coordinador lo registre
    Entonces el cambio debe quedar registrado en la información del evento junto con la fecha en que fue solicitado

  @US-017 @CA-038 @excepcional
  # @prueba: test_correcciones_etapas_3_a_7.py, test_e3f1_correcciones_negocio.py, test_h13_criterios_aceptacion.py, test_solicitud_cambio_maquina_estados.py
  Escenario: CA-038 - Escenario A: el cambio no afecta costos ni condiciones
    Dado que el Cliente solicitó un cambio viable que no afecta los costos ni las condiciones acordadas
    Cuando el Coordinador tramite la solicitud
    Entonces la solicitud expresa del Cliente es suficiente para tramitarlo
    Y no se requiere aprobación adicional del Cliente ni autorización de Administración

  @US-017 @CA-038 @excepcional
  # @prueba: test_correcciones_etapas_3_a_7.py, test_e3f1_correcciones_negocio.py, test_h13_criterios_aceptacion.py, test_solicitud_cambio_maquina_estados.py
  Escenario: CA-038 - Escenario B: el cambio afecta costos o condiciones
    Dado que el Cliente solicitó un cambio viable que afecta los costos o las condiciones acordadas
    Cuando el Coordinador tramite la solicitud
    Entonces deben registrarse la aprobación del Cliente y la autorización de Administración antes de confirmar la modificación
    Y el cargo por cambio tardío, por sí solo, no requiere autorización adicional de Administración

  @US-017 @CA-038 @excepcional
  # @prueba: test_correcciones_etapas_3_a_7.py, test_e3f1_correcciones_negocio.py, test_h13_criterios_aceptacion.py, test_solicitud_cambio_maquina_estados.py
  Escenario: CA-038 - Escenario C: confirmación del cambio
    Dado que el cambio está documentado mediante el anexo vinculado al contrato original
    Y se cumplieron los pagos obligatorios aplicables
    Cuando el Coordinador confirme la modificación
    Entonces se actualiza la información del evento y se comunica a los participantes según sus responsabilidades
    Y mientras falte el anexo, una aprobación, una autorización o un pago requerido se mantiene la última configuración confirmada

  @US-017 @CA-039 @positivo
  # @prueba: apoyo_especificaciones.py, apoyo_regularizacion_solicitudes.py, test_e3f1_correcciones_negocio.py, test_etapa9_casos_de_uso.py, test_h08_inicio_evento.py, test_h08_intervalo_pendiente.py, test_h13_criterios_aceptacion.py, test_regularizacion_solicitudes.py
  Escenario: CA-039
    Dado que el Cliente solicita un cambio después de la contratación
    Cuando el evento ya haya iniciado
    Entonces la solicitud de cambio no debe proceder

  # US-018 - Como Coordinador, quiero registrar y consultar el resultado de la aprobación del Cliente y de la autorización de Administración para los cambios que afecten los costos o las condiciones acordadas, para evitar confirmar una modificación sin las validaciones requeridas.
  @US-018 @CA-040 @positivo
  # @prueba: test_etapa9_casos_de_uso.py
  Escenario: CA-040
    Dado que un cambio afecta los costos o las condiciones acordadas
    Cuando el Coordinador gestione el cambio
    Entonces debe solicitar la aprobación del Cliente y la autorización de Administración antes de confirmar la modificación

  @US-018 @CA-041 @positivo
  # @prueba: test_correcciones_etapas_3_a_7.py, test_decisiones_stakeholder.py, test_e3f1_correcciones_negocio.py, test_e3g_cargo_tardio_y_conceptos.py, test_etapa9_transacciones_y_reacciones.py, test_h03_consultas_administracion.py, test_reglas_corregidas.py, test_solicitud_cambio_maquina_estados.py
  Escenario: CA-041
    Dado que el Cliente aprobó el cambio y Administración lo autorizó
    Cuando corresponda, cuando el Coordinador vaya a confirmar la modificación
    Entonces deberá verificar que el anexo vinculado al contrato original esté elaborado y que, si existen nuevos importes por pagar, Administración haya registrado y verificado el pago que el Cliente efectuó dentro del plazo de 24 horas naturales contado desde la comunicación de la solicitud de pago; el registro y la verificación pueden ser posteriores a ese plazo. Solo después de cumplir estas condiciones y los demás requisitos aplicables podrá confirmar el cambio, actualizar la información del evento y comunicar la modificación a los proveedores involucrados

  # US-019 - Como Cliente, quiero aprobar o rechazar los cambios que afecten los costos o condiciones de mi evento, para decidir si acepto la modificación.
  @US-019 @CA-042 @positivo
  # @prueba: test_e3g_cargo_tardio_y_conceptos.py
  Escenario: CA-042
    Dado que un cambio requiere la aprobación del Cliente
    Cuando el Cliente rechace la modificación
    Entonces el cambio no debe aprobarse y debe mantenerse la última configuración confirmada del evento

  @US-019 @CA-043 @positivo
  # @prueba: test_solicitud_cambio_maquina_estados.py
  Escenario: CA-043
    Dado que un cambio requiere la aprobación del Cliente
    Cuando el Cliente apruebe la modificación
    Entonces la aprobación debe quedar registrada y se debe solicitar la autorización de Administración antes de confirmar el cambio

  # US-020 - Como Administración, quiero autorizar o rechazar los cambios que afecten los costos o condiciones, para controlar las modificaciones realizadas.
  @US-020 @CA-044 @negativo
  # @prueba: test_e3g_cargo_tardio_y_conceptos.py, test_h13_criterios_aceptacion.py
  Escenario: CA-044
    Dado que un cambio requiere la autorización de Administración
    Cuando Administración rechace la modificación
    Entonces el cambio no debe autorizarse, se debe informar al Cliente sobre el rechazo y debe mantenerse la última configuración confirmada del evento

  @US-020 @CA-045 @positivo
  Escenario: CA-045
    Dado que un cambio requiere la autorización de Administración
    Cuando Administración autorice la modificación
    Entonces la autorización debe quedar registrada y el proceso de confirmación del cambio debe continuar

  # US-023 - Como Cliente, quiero solicitar cambios en los servicios de mi evento, para ajustar la organización de acuerdo con mis necesidades.
  @US-023 @CA-059 @positivo
  # @prueba: test_h13_criterios_aceptacion.py
  Escenario: CA-059
    Dado que el Cliente tiene un evento contratado
    Cuando solicite un cambio en los servicios que ya forman parte del evento
    Entonces el Coordinador debe poder recibir y registrar la solicitud de cambio

  # US-024 - Como Coordinador, quiero gestionar las solicitudes de cambios realizadas por el Cliente, verificando primero que no exista un saldo vencido del contrato original, para evaluar su viabilidad, aplicar las condiciones correspondientes, obtener las aprobaciones necesarias, documentar el cambio aprobado mediante un anexo vinculado al contrato original, solicitar y dar seguimiento al pago de los nuevos importes dentro del plazo establecido y actualizar la información del evento únicamente cuando se hayan cumplido los requisitos aplicables, incluyendo las aprobaciones, la documentación y la verificación del pago cuando corresponda.
  @US-024 @CA-060 @positivo
  # @prueba: test_correcciones_etapas_3_a_7.py, test_etapa9_casos_de_uso.py, test_h13_criterios_aceptacion.py
  Escenario: CA-060
    Dado que el Cliente solicita un cambio
    Cuando el Coordinador revise su viabilidad
    Entonces debe consultar a los proveedores involucrados para determinar si el cambio puede realizarse y evaluar su impacto en los servicios, costos y condiciones acordadas

  @US-024 @CA-061 @positivo
  # @prueba: test_e3f1_correcciones_negocio.py, test_e3g_cargo_tardio_y_conceptos.py, test_especificaciones_negocio.py, test_etapa9_casos_de_uso.py
  Escenario: CA-061
    Dado que el Cliente solicita un cambio con siete días naturales o más de anticipación al evento
    Cuando el Coordinador revise la solicitud
    Entonces debe consultar a los proveedores involucrados para verificar si el cambio puede realizarse y no debe aplicarse un cargo adicional por cambio por parte de Eventos Nova

  @US-024 @CA-062 @negativo
  # @prueba: apoyo_maquina_estados_solicitud_cambio.py, test_e3f1_correcciones_negocio.py, test_e3g_cargo_tardio_y_conceptos.py, test_especificaciones_negocio.py, test_etapa9_casos_de_uso.py
  Escenario: CA-062
    Dado que el Cliente solicita un cambio con menos de siete días naturales de anticipación al evento
    Cuando el Coordinador revise la solicitud y determine su viabilidad
    Entonces deberá consultar a los proveedores involucrados para verificar si el cambio puede realizarse. Si el cambio es viable, el Cliente acepta la modificación y finalmente se realiza, deberá aplicarse el cargo por cambio tardío correspondiente a la tarifa vigente establecida por Eventos Nova. Si el cambio no puede realizarse o el Cliente no acepta la modificación propuesta, la solicitud no procederá y no deberá cobrarse dicho cargo

  @US-024 @CA-063 @excepcional
  # @prueba: test_e3g_cargo_tardio_y_conceptos.py
  Escenario: CA-063
    Dado que el cambio solicitado puede generar costos adicionales o modificar las condiciones de un proveedor
    Cuando el Coordinador consulte al proveedor
    Entonces debe determinar los costos o condiciones adicionales de manera independiente al cargo por cambio tardío establecido por Eventos Nova

  @US-024 @CA-064 @positivo
  # @prueba: test_correcciones_etapas_3_a_7.py
  Escenario: CA-064
    Dado que el Cliente solicita un aumento en el número de invitados
    Cuando el Coordinador revise el cambio
    Entonces debe consultar con los proveedores para determinar su impacto en los servicios contratados y verificar si pueden atender la nueva cantidad

  @US-024 @CA-065 @positivo
  # @prueba: test_h13_criterios_aceptacion.py
  Escenario: CA-065
    Dado que el aumento de invitados supera la capacidad disponible y no puede realizarse
    Cuando el Coordinador determine que el cambio no es posible
    Entonces debe informar al Cliente y mantener la última configuración confirmada del evento

  @US-024 @CA-066 @excepcional
  # @prueba: apoyo_especificaciones.py, apoyo_regularizacion_solicitudes.py, test_n6_validacion_servicio_adicional.py, test_reglas_corregidas.py, test_regularizacion_solicitudes.py
  Escenario: CA-066
    Dado que el Cliente solicita un cambio y el Coordinador identifica que existe un saldo vencido del contrato original
    Cuando detenga la gestión e informe al Cliente que debe regularizar el saldo
    Entonces la solicitud solo podrá retomarse si el Cliente liquida el saldo vencido y los cargos moratorios correspondientes dentro de las 24 horas naturales posteriores a la comunicación de dichos cargos. Al finalizar el plazo, Administración deberá revisar los pagos recibidos y verificar si la liquidación se realizó dentro del periodo establecido. Si el pago se realizó dentro del plazo, Administración deberá registrar y verificar la liquidación e informar al Coordinador para que retome la solicitud, siempre que se cumplan los demás requisitos aplicables. Si el Cliente no realizó el pago dentro del plazo, Administración deberá informar al Coordinador para que registre la cancelación del evento e informe a las personas involucradas

  @US-024 @CA-067 @excepcional
  # @prueba: test_e3f1_correcciones_negocio.py, test_e3g_cargo_tardio_y_conceptos.py, test_etapa9_casos_de_uso.py, test_h03_consultas_administracion.py, test_h10_anticipo_liquidado.py, test_reglas_corregidas.py, test_solicitud_cambio_maquina_estados.py
  Escenario: CA-067
    Dado que un cambio aprobado genera nuevos importes por pagar y se han obtenido las aprobaciones requeridas
    Cuando el Coordinador comunique al Cliente la solicitud de pago
    Entonces deberá informarle que cuenta con un plazo máximo de 24 horas naturales a partir de dicha comunicación para realizarlo. Administración deberá registrar y verificar el pago recibido; el plazo es para que el Cliente pague, por lo que el registro y la verificación pueden ser posteriores. Si el Cliente efectuó el pago dentro del plazo y Administración lo verifica, el Coordinador podrá continuar con la confirmación del cambio, siempre que se cumplan los demás requisitos aplicables; mientras la verificación esté pendiente, la solicitud no se cierra por falta de pago. Si se comprueba que el Cliente no efectuó el pago dentro del plazo, la solicitud de cambio deberá cerrarse por falta de pago, registrar el motivo e informar al Cliente, conservando la última configuración confirmada del evento y sin confirmar el cambio

  @US-024 @CA-068 @negativo
  # @prueba: test_e3f1_correcciones_negocio.py, test_e3g_cargo_tardio_y_conceptos.py, test_solicitud_cambio_maquina_estados.py
  Escenario: CA-068
    Dado que un cambio solicitado por el Cliente fue aprobado y cuenta con la autorización de Administración
    Cuando esta sea necesaria, cuando el Coordinador vaya a confirmar la modificación
    Entonces deberá elaborar previamente un anexo vinculado al contrato original que especifique el cambio aprobado e incluya los nuevos costos o condiciones cuando corresponda. La modificación no podrá confirmarse antes de que el anexo esté elaborado y se hayan cumplido las aprobaciones obligatorias y, cuando existan nuevos importes por pagar, el pago se encuentre registrado y verificado

  @US-024 @CA-069 @negativo
  # @prueba: test_e3g_cargo_tardio_y_conceptos.py, test_etapa9_casos_de_uso.py, test_h13_criterios_aceptacion.py
  Escenario: CA-069
    Dado que el Coordinador consulta a los proveedores para evaluar un cambio y estos informan que no es viable por falta de tiempo o disponibilidad
    Cuando registre el resultado
    Entonces deberá informar al Cliente, registrar la solicitud como no procedente y mantener la última configuración confirmada del evento. No deberá cobrar el cargo por cambio tardío si la modificación no se realiza

  @US-024 @CA-070 @negativo
  # @prueba: test_e3f1_correcciones_negocio.py, test_e3g_cargo_tardio_y_conceptos.py, test_etapa9_casos_de_uso.py, test_regularizacion_solicitudes.py, test_servicio_adicional_maquina_estados.py, test_solicitud_cambio_maquina_estados.py
  Escenario: CA-070
    Dado que existe una solicitud de cambio que todavía no ha sido confirmada ni realizada
    Cuando inicie el evento
    Entonces la solicitud deberá cerrarse como no procedente por inicio del evento y deberá conservarse la última configuración confirmada. Se dejarán sin efecto los importes pendientes de cobro correspondientes exclusivamente a ese cambio; si el Evento no está cancelado y se recibió un importe por el cambio no realizado, Administración deberá devolverlo dentro de los cinco días hábiles siguientes al cierre, una vez verificado el importe (si el pago se registra después del cierre, el plazo corre desde su registro), conforme a SE-012. Esta devolución no afectará los pagos u obligaciones del contrato original ni otros conceptos independientes. Si el Evento fue cancelado, se aplicará la política de no reembolso correspondiente a la cancelación del Evento
