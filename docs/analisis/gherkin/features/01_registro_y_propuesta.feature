# language: es
# Eventos Nova - Equipo 16 - Especificación Gherkin derivada de los criterios de aceptación aprobados.
# Fuente: Historias de usuario de Eventos Nova, versión 2.0 consolidada (US-001 a US-033, CA-001 a CA-114).
# Estos escenarios son especificación ejecutable; la verificación automatizada vigente se realiza con unittest (ver etiquetas @prueba).

Característica: Registro del evento y gestión de la propuesta

  # US-001 - Como Coordinador, quiero registrar la información del cliente y del evento, para comenzar con la organización del evento.
  @US-001 @CA-001 @positivo
  Escenario: CA-001
    Dado que el Coordinador recibe una solicitud
    Cuando registre la información del Cliente y del evento
    Entonces los datos deben quedar registrados

  @US-001 @CA-002 @positivo
  Escenario: CA-002
    Dado que la información del Cliente y del evento fue registrada
    Cuando el Coordinador consulte el evento
    Entonces debe poder visualizar la información registrada

  # US-002 - Como Coordinador, quiero registrar el tipo de evento, la fecha, la hora, el número aproximado de invitados, el lugar y los servicios solicitados, para contar con la información necesaria para preparar la propuesta.
  @US-002 @CA-003 @positivo
  # @prueba: test_api_esquemas.py, test_api_propuestas.py, test_validacion_datos_api.py, test_validacion_datos_dominio.py
  Escenario: CA-003
    Dado que el Coordinador está registrando un evento
    Cuando ingrese el tipo de evento, fecha, hora, número aproximado de invitados, lugar y servicios solicitados
    Entonces estos datos deben quedar registrados en el evento

  @US-002 @CA-004 @positivo
  Escenario: CA-004
    Dado que los datos del evento fueron registrados
    Cuando el Coordinador prepare la propuesta
    Entonces debe poder consultar esta información

  # US-003 - Como Coordinador, quiero elaborar una propuesta que incluya los servicios, proveedores considerados, costos y condiciones, para presentar al cliente una opción de acuerdo con sus necesidades.
  @US-003 @CA-005 @positivo
  # @prueba: test_api_esquemas.py, test_api_propuestas.py, test_validacion_datos_api.py, test_validacion_datos_dominio.py
  Escenario: CA-005
    Dado que se cuenta con la información del evento
    Cuando el Coordinador elabore la propuesta
    Entonces debe incluir los servicios, proveedores considerados, costos y condiciones

  @US-003 @CA-006 @positivo
  Escenario: CA-006
    Dado que la propuesta fue elaborada
    Cuando el Coordinador la consulte
    Entonces debe poder revisar la información incluida en ella

  # US-004 - Como Coordinador, quiero crear una nueva versión de la propuesta cuando el cliente solicite cambios antes de aceptarla, para mantener actualizada la información de la propuesta.
  @US-004 @CA-007 @positivo
  # @prueba: test_etapa9_casos_de_uso.py, test_h03_consultas_administracion.py
  Escenario: CA-007
    Dado que el Cliente solicita un cambio antes de aceptar la propuesta
    Cuando el Coordinador realice el cambio
    Entonces debe crear una nueva versión de la propuesta

  @US-004 @CA-008 @positivo
  # @prueba: test_h03_consultas_administracion.py
  Escenario: CA-008
    Dado que existe una nueva versión de la propuesta
    Cuando el Coordinador la consulte
    Entonces debe contener los cambios solicitados

  # US-005 - Como Coordinador, quiero identificar cada versión de la propuesta con un número consecutivo y una fecha de actualización, para reconocer cuál es la versión vigente.
  @US-005 @CA-009 @positivo
  # @prueba: test_h03_consultas_administracion.py
  Escenario: CA-009
    Dado que se crea una nueva versión de la propuesta
    Cuando se registre
    Entonces debe tener un número consecutivo y una fecha de actualización

  @US-005 @CA-010 @positivo
  # @prueba: test_etapa9_casos_de_uso.py
  Escenario: CA-010
    Dado que existen varias versiones de una propuesta
    Cuando el Coordinador consulte sus versiones
    Entonces debe poder reconocer cuál es la versión vigente

  # US-006 - Como Cliente, quiero revisar la propuesta y sus condiciones, para decidir si acepto los servicios y costos ofrecidos.
  @US-006 @CA-011 @positivo
  Escenario: CA-011
    Dado que el Coordinador ha preparado una propuesta
    Cuando el Cliente la revise
    Entonces debe poder consultar los servicios, costos y condiciones incluidos

  @US-006 @CA-012 @positivo
  # @prueba: test_h13_criterios_aceptacion.py
  Escenario: CA-012
    Dado que el Cliente ha revisado la propuesta
    Cuando decida si está de acuerdo con ella
    Entonces podrá aceptarla o solicitar cambios antes de aceptarla

  # US-007 - Como Cliente, quiero aceptar la propuesta, para continuar con la formalización del contrato.
  @US-007 @CA-013 @positivo
  # @prueba: test_api_operaciones.py, test_etapa9_casos_de_uso.py
  Escenario: CA-013
    Dado que el Cliente está de acuerdo con los servicios, costos y condiciones
    Cuando acepte la propuesta
    Entonces la propuesta debe quedar aceptada

  @US-007 @CA-014 @positivo
  # @prueba: test_h13_criterios_aceptacion.py
  Escenario: CA-014
    Dado que la propuesta fue aceptada
    Cuando el Coordinador continúe con el proceso
    Entonces debe iniciar la formalización del contrato

  # US-029 - Como Coordinador, quiero registrar cuando una propuesta no sea aceptada y se cierre, para mantener actualizado el estado de las propuestas.
  @US-029 @CA-092 @excepcional
  # @prueba: test_etapa9_casos_de_uso.py, test_evento_maquina_estados.py
  Escenario: CA-092
    Dado que el Cliente no acepta la propuesta y tampoco desea solicitar cambios
    Cuando decida no continuar con ella
    Entonces la propuesta debe quedar registrada como no aceptada y cerrada

  @US-029 @CA-093 @excepcional
  # @prueba: test_etapa9_casos_de_uso.py
  Escenario: CA-093
    Dado que una propuesta fue cerrada como no aceptada
    Cuando el Cliente posteriormente desee continuar con la organización del evento
    Entonces podrá solicitar una nueva propuesta. El cierre de la propuesta no cancela ni cierra definitivamente el Evento; mientras pueda solicitarse otra propuesta, el Evento deberá permanecer En gestión. El estado Cerrado sin contratación se utilizará cuando el proceso de contratación se cierre definitivamente sin confirmarse
