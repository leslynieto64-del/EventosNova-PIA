# language: es
# Eventos Nova - Equipo 16 - Especificación Gherkin derivada de los criterios de aceptación aprobados.
# Fuente: Historias de usuario de Eventos Nova, versión 2.0 consolidada (US-001 a US-033, CA-001 a CA-114).
# Estos escenarios son especificación ejecutable; la verificación automatizada vigente se realiza con unittest (ver etiquetas @prueba).

Característica: Solicitudes de servicios adicionales

  # US-025 - Como Coordinador, quiero gestionar las solicitudes de servicios adicionales realizadas por el Cliente, registrando la solicitud y comprobando, en este orden, que el Evento no esté cancelado ni iniciado, que la solicitud cumpla el plazo establecido y que no exista un saldo vencido del contrato original, para consultar la disponibilidad de los proveedores, determinar el costo y las condiciones del servicio, obtener la aprobación del Cliente y la autorización obligatoria de Administración, solicitar y dar seguimiento al pago y confirmar el servicio únicamente cuando el pago esté registrado y verificado y se cumplan los demás requisitos.
  @US-025 @CA-071 @negativo
  # @prueba: test_ca073_074_consulta_en_dos_etapas.py, test_ca073_074_disponibilidad.py, test_h08_inicio_evento.py, test_h09_pago_pendiente_al_cierre.py, test_n6_validacion_servicio_adicional.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-071
    Dado que existe una solicitud de servicio adicional que todavía no ha sido confirmada ni realizada
    Cuando inicie el evento
    Entonces la solicitud deberá cerrarse como no procedente por inicio del evento y el servicio no deberá confirmarse ni realizarse. Se dejarán sin efecto los importes pendientes de cobro correspondientes exclusivamente a ese servicio; si el Evento no está cancelado y se recibió un importe por el servicio adicional no realizado, Administración deberá devolverlo dentro de los cinco días hábiles siguientes al cierre, una vez verificado el importe (si el pago se registra después del cierre, el plazo corre desde su registro), conforme a SE-012. Esta devolución no afectará los pagos u obligaciones del contrato original ni otros conceptos independientes. Si el Evento fue cancelado, se aplicará la política de no reembolso correspondiente a la cancelación del Evento

  @US-025 @CA-072 @excepcional
  # @prueba: apoyo_especificaciones.py, apoyo_regularizacion_solicitudes.py, test_correcciones_etapas_3_a_7.py, test_etapa9_casos_de_uso.py, test_n6_validacion_servicio_adicional.py, test_reglas_corregidas.py, test_regularizacion_solicitudes.py
  Escenario: CA-072
    Dado que el Cliente solicita un servicio adicional, la solicitud ya se registró y superó las verificaciones anteriores (el Evento no está cancelado ni ha iniciado y faltan al menos cinco días naturales para el evento) y, solo entonces, el Coordinador identifica que existe un saldo vencido del contrato original
    Cuando detenga la gestión e informe al Cliente que debe regularizar el saldo
    Entonces la solicitud solo podrá retomarse si el Cliente liquida el saldo vencido y los cargos moratorios correspondientes dentro de las 24 horas naturales posteriores a la comunicación de dichos cargos. Al finalizar el plazo, Administración deberá revisar los pagos recibidos y verificar si la liquidación se realizó dentro del periodo establecido. Si el pago se realizó dentro del plazo, Administración deberá registrar y verificar la liquidación e informar al Coordinador para que retome la solicitud, siempre que se cumplan los demás requisitos aplicables, incluido el plazo mínimo de cinco días naturales de anticipación al evento, la disponibilidad del proveedor y las aprobaciones obligatorias del Cliente y de Administración. Si el Cliente no realizó el pago dentro del plazo, Administración deberá informar al Coordinador para que registre la cancelación del evento e informe a las personas involucradas

  @US-025 @CA-073 @positivo
  # @prueba: test_ca073_074_consulta_en_dos_etapas.py, test_ca073_074_disponibilidad.py, test_h06_h07_h21_correcciones.py, test_n6_validacion_servicio_adicional.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-073
    Dado que el Cliente solicita un servicio adicional con cinco días naturales o más de anticipación al evento
    Cuando el Coordinador revise la solicitud
    Entonces deberá consultar primero la disponibilidad de los proveedores que ya participan en el evento y determinar el costo establecido por el proveedor y las condiciones del servicio. Eventos Nova no deberá aplicar un cargo propio adicional por el servicio adicional

  @US-025 @CA-074 @positivo
  # @prueba: test_ca073_074_consulta_en_dos_etapas.py, test_ca073_074_disponibilidad.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-074
    Dado que ninguno de los proveedores que ya participan en el evento puede proporcionar el servicio adicional
    Cuando el Coordinador revise la disponibilidad
    Entonces debe buscar una alternativa con otro proveedor

  @US-025 @CA-075 @positivo
  # @prueba: test_ca073_074_consulta_en_dos_etapas.py, test_ca073_074_disponibilidad.py, test_correcciones_etapas_3_a_7.py, test_h06_h07_h21_correcciones.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-075
    Dado que el Coordinador busca una alternativa para proporcionar el servicio adicional
    Cuando encuentre un proveedor disponible
    Entonces debe confirmar su disponibilidad y determinar el costo y las condiciones del servicio antes de continuar con la solicitud

  @US-025 @CA-076 @positivo
  # @prueba: test_ca073_074_consulta_en_dos_etapas.py, test_ca073_074_disponibilidad.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-076
    Dado que ninguno de los proveedores actuales ni las alternativas consultadas puede proporcionar el servicio adicional y el Coordinador determina que necesita más tiempo para buscar otra alternativa
    Cuando informe al Cliente de esta situación
    Entonces deberá comunicarle que la búsqueda requiere más tiempo y verificar que todavía se cumpla el plazo mínimo de cinco días naturales de anticipación al evento antes de continuar con la gestión

  @US-025 @CA-077 @negativo
  # @prueba: apoyo_especificaciones.py, apoyo_regularizacion_solicitudes.py, test_ca073_074_consulta_en_dos_etapas.py, test_ca073_074_disponibilidad.py, test_d1_servicio_adicional_contratacion_confirmada.py, test_e3f1_correcciones_negocio.py, test_especificaciones_negocio.py, test_n6_validacion_servicio_adicional.py, test_reglas_corregidas.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-077
    Dado que no se encuentra una alternativa disponible para el servicio adicional y el Cliente acepta esperar más tiempo
    Cuando el Coordinador evalúe si puede continuar con la búsqueda
    Entonces deberá verificar que todavía queden al menos cinco días naturales antes del evento. Si se cumple este plazo, podrá continuar con la búsqueda. Si quedan menos de cinco días naturales y no se ha encontrado una alternativa que permita continuar con la solicitud, deberá detener la gestión, registrar la solicitud como no procedente e informar al Cliente. La aceptación del Cliente de esperar no constituye una excepción al plazo mínimo establecido

  @US-025 @CA-078 @positivo
  # @prueba: test_ca073_074_disponibilidad.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-078
    Dado que no se encuentra una alternativa disponible para el servicio adicional
    Cuando el Cliente no acepte esperar más tiempo
    Entonces el Coordinador deberá registrar que el servicio adicional no se realizará e informar al Cliente

  @US-025 @CA-079 @negativo
  # @prueba: test_servicio_adicional_maquina_estados.py
  Escenario: CA-079
    Dado que existe un proveedor disponible para proporcionar el servicio adicional y se han determinado su costo y condiciones
    Cuando el Coordinador presente la información al Cliente
    Entonces el Cliente deberá poder aprobar o rechazar el servicio adicional. Si el Cliente no lo aprueba, deberá registrarse como no aprobado y no confirmarse el servicio. Si el Cliente lo aprueba, el Coordinador deberá solicitar obligatoriamente la autorización de Administración antes de continuar con la gestión

  @US-025 @CA-080 @excepcional
  # @prueba: test_especificaciones_negocio.py, test_h06_h07_h21_correcciones.py, test_h08_inicio_evento.py, test_reglas_corregidas.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-080
    Dado que el Cliente solicitó un servicio adicional con al menos cinco días naturales de anticipación y se encontró una alternativa disponible mientras todavía se cumplía ese plazo
    Cuando la solicitud avance a la aprobación del Cliente y a la autorización de Administración
    Entonces conservará su elegibilidad durante ambas fases siempre que el evento no haya iniciado, aunque durante la espera queden menos de cinco días naturales. Después de obtener la aprobación y autorización, el Coordinador deberá formalizar el servicio mediante el anexo vinculado al contrato original antes de comunicar la solicitud de pago. Desde esa comunicación, el Cliente contará con 24 horas naturales para pagar. Si el evento inicia antes de que el servicio esté confirmado, la solicitud se cerrará por inicio del evento y el servicio no se realizará; de lo contrario, si se comprueba que el Cliente no efectuó el pago dentro del plazo, la solicitud se cerrará por falta de pago e informará al Cliente. Si el Cliente pagó dentro del plazo, el servicio permanece pendiente de verificación aunque Administración registre o verifique el pago después, y no se cierra por esa demora

  @US-025 @CA-081 @positivo
  # @prueba: test_correcciones_etapas_3_a_7.py, test_decisiones_stakeholder.py, test_etapa9_casos_de_uso.py, test_h13_criterios_aceptacion.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-081
    Dado que el Cliente aprobó el costo y las condiciones de un servicio adicional
    Cuando Administración rechace la solicitud
    Entonces el Coordinador deberá registrar el servicio como no autorizado, informar al Cliente y no confirmar el servicio adicional

  @US-025 @CA-082 @positivo
  # @prueba: test_correcciones_etapas_3_a_7.py, test_decisiones_stakeholder.py, test_etapa9_casos_de_uso.py, test_h06_h07_h21_correcciones.py, test_reglas_corregidas.py, test_servicio_adicional_cierre_falta_pago.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-082
    Dado que el Cliente aprobó el costo y las condiciones del servicio adicional y Administración autorizó la solicitud
    Cuando el Coordinador prepare la formalización del servicio
    Entonces deberá documentarlo mediante un anexo vinculado al contrato original que identifique el servicio, su costo y las condiciones aprobadas, antes de comunicar la solicitud de pago. El plazo de pago de 24 horas naturales comenzará con esa comunicación. El servicio solo podrá confirmarse cuando el pago esté registrado y verificado y se cumplan los demás requisitos. Si la solicitud se presentó con al menos cinco días naturales de anticipación y se encontró una alternativa disponible dentro de ese plazo, conservará su elegibilidad durante la aprobación y autorización mientras el evento no haya iniciado

  @US-025 @CA-083 @negativo
  # @prueba: apoyo_especificaciones.py, apoyo_regularizacion_solicitudes.py, test_ca073_074_disponibilidad.py, test_d1_servicio_adicional_contratacion_confirmada.py, test_e3f1_correcciones_negocio.py, test_especificaciones_negocio.py, test_n6_validacion_servicio_adicional.py, test_reglas_corregidas.py, test_regularizacion_solicitudes.py, test_servicio_adicional_maquina_estados.py
  Escenario: CA-083
    Dado que el Cliente solicita un servicio adicional con menos de cinco días naturales de anticipación al evento
    Cuando el Coordinador revise la solicitud
    Entonces deberá registrarla como no procedente, informar al Cliente y detener la gestión. No deberá continuar con la búsqueda de proveedores, solicitar las aprobaciones ni confirmar el servicio

  @US-025 @CA-099 @negativo
  # @prueba: test_e3f1_correcciones_negocio.py, test_h08_inicio_evento.py, test_n6_validacion_servicio_adicional.py
  Escenario: CA-099
    Dado que el Cliente solicita un servicio adicional para un Evento que ya inició
    Cuando el Coordinador registre la solicitud y verifique el estado del Evento
    Entonces deberá registrarla como no procedente con el motivo de que el Evento ya inició, informar al Cliente y detener la gestión. Como es la primera verificación, no se evaluarán el plazo mínimo ni el saldo vencido y se registrará solo este motivo. Este criterio se aplica a una solicitud nueva; el cierre de una solicitud que ya estaba en trámite cuando inicia el Evento se rige por CA-071

  @US-025 @CA-100 @negativo
  # @prueba: test_e3f1_correcciones_negocio.py, test_n6_validacion_servicio_adicional.py
  Escenario: CA-100
    Dado que el Cliente solicita un servicio adicional para un Evento cancelado
    Cuando el Coordinador registre la solicitud y verifique el estado del Evento
    Entonces deberá registrarla como no procedente con el motivo de que el Evento está cancelado, informar al Cliente y detener la gestión. Como es la primera verificación, no se evaluarán el plazo mínimo ni el saldo vencido y se registrará solo este motivo. Este criterio se aplica a una solicitud nueva; las solicitudes que ya estaban en trámite cuando se cancela el Evento se cierran con el motivo «Evento cancelado» conforme a BN-008

  @US-025 @CA-101 @excepcional
  # @prueba: test_d1_servicio_adicional_contratacion_confirmada.py
  Escenario: CA-101
    Dado que la contratación del Evento no está confirmada (el Evento está En gestión o Cerrado sin contratación)
    Cuando el Cliente solicite un servicio adicional
    Entonces el Coordinador no deberá registrar la solicitud, informará al Cliente que un servicio adicional solo puede registrarse con la contratación confirmada y no evaluará el plazo mínimo ni el saldo vencido
