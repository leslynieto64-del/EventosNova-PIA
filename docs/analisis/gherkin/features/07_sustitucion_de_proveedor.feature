# language: es
# Eventos Nova - Equipo 16 - Especificación Gherkin derivada de los criterios de aceptación aprobados.
# Fuente: Historias de usuario de Eventos Nova, versión 2.0 consolidada (US-001 a US-033, CA-001 a CA-114).
# Estos escenarios son especificación ejecutable; la verificación automatizada vigente se realiza con unittest (ver etiquetas @prueba).

Característica: Sustitución de proveedores

  # US-021 - Como Coordinador, quiero registrar cuando un proveedor no esté disponible o cancele y buscar una alternativa, para mantener los servicios necesarios para realizar el evento.
  @US-021 @CA-046 @excepcional
  # @prueba: test_h01_h02_proveedores.py, test_h06_h07_h21_correcciones.py
  Escenario: CA-046
    Dado que un proveedor no está disponible o cancela
    Cuando el Coordinador registre la situación
    Entonces debe quedar registrada la falta de disponibilidad o cancelación

  @US-021 @CA-047 @positivo
  Escenario: CA-047
    Dado que un proveedor no puede proporcionar el servicio
    Cuando el Coordinador busque una alternativa
    Entonces debe consultar la disponibilidad de otro proveedor para ese servicio

  @US-021 @CA-048 @positivo
  # @prueba: test_h13_criterios_aceptacion.py
  Escenario: CA-048
    Dado que no existe ningún proveedor alternativo disponible
    Cuando el Coordinador confirme que no hay otra opción para cubrir el servicio
    Entonces debe informar al Cliente, mantener pendiente la sustitución del proveedor para el servicio afectado y continuar buscando otra alternativa

  @US-021 @CA-049 @positivo
  Escenario: CA-049
    Dado que el proveedor alternativo modifica los servicios, los costos o las condiciones acordadas y el Cliente aprobó la alternativa
    Cuando el Coordinador continúe con la gestión de la sustitución
    Entonces deberá solicitar la autorización de Administración antes de confirmar el reemplazo

  @US-021 @CA-050 @positivo
  # @prueba: test_correcciones_etapas_3_a_7.py, test_decisiones_stakeholder.py, test_h13_criterios_aceptacion.py, test_sustitucion_maquina_estados.py
  Escenario: CA-050
    Dado que el proveedor alternativo modifica los servicios, los costos o las condiciones acordadas, el Cliente aprobó la alternativa y el Coordinador solicitó la autorización de Administración
    Cuando Administración rechace la sustitución
    Entonces el Coordinador deberá registrar que el reemplazo no fue autorizado, informar al Cliente, no confirmar el proveedor alternativo, mantener pendiente la sustitución del proveedor para el servicio afectado y continuar buscando otra alternativa

  @US-021 @CA-051 @positivo
  # @prueba: test_h01_h02_proveedores.py
  Escenario: CA-051
    Dado que el proveedor alternativo modifica los servicios, los costos o las condiciones acordadas, el Cliente aprobó la alternativa y Administración autorizó la sustitución
    Cuando el Coordinador gestione el reemplazo
    Entonces deberá documentar la sustitución mediante un anexo vinculado al contrato original antes de confirmar al proveedor alternativo. El anexo deberá identificar al proveedor sustituto y el servicio correspondiente, e incluir los costos y las condiciones modificadas, cuando corresponda. Una vez elaborado el anexo, el Coordinador deberá confirmar el reemplazo, actualizar la información del evento y comunicar la modificación a las personas involucradas

  @US-021 @CA-052 @excepcional
  # @prueba: apoyo_persistencia.py, test_correcciones_etapas_3_a_7.py, test_interfaz_textos.py, test_sustitucion_maquina_estados.py
  Escenario: CA-052
    Dado que se propone una sustitución de proveedor que genera un costo adicional
    Cuando el Coordinador registre la sustitución aprobada y autorizada cuando corresponda
    Entonces el costo adicional deberá incorporarse al saldo general del contrato original y liquidarse conforme al plazo ordinario de pago, como máximo tres días hábiles antes de la fecha del evento. Si la sustitución con costo adicional se aprueba después de ese límite ordinario, el importe deberá pagarse y verificarse antes de confirmar el reemplazo, sin considerarse vencido automáticamente por esa circunstancia. No existe un plazo fijo adicional separado de la condición de pagar y verificar antes de confirmar

  @US-021 @CA-053 @positivo
  # @prueba: test_h01_h02_proveedores.py
  Escenario: CA-053
    Dado que el proveedor alternativo no modifica los servicios, los costos ni las condiciones acordadas
    Cuando el Coordinador gestione la sustitución
    Entonces no será necesario obtener la aprobación del Cliente ni la autorización de Administración, pero deberá documentar la sustitución mediante un anexo vinculado al contrato original antes de confirmar el reemplazo. El Coordinador deberá identificar al proveedor sustituto y el servicio correspondiente en el anexo, e incluir los costos y las condiciones modificadas, cuando corresponda. Una vez elaborado el anexo, el Coordinador deberá confirmar el reemplazo, actualizar la información del evento y comunicar la modificación a las personas involucradas de acuerdo con sus responsabilidades

  @US-021 @CA-054 @negativo
  # @prueba: test_etapa9_casos_de_uso.py, test_sustitucion_maquina_estados.py
  Escenario: CA-054
    Dado que el Cliente rechaza la alternativa de proveedor que modifica los servicios, los costos o las condiciones acordadas
    Cuando el Coordinador registre la decisión del Cliente
    Entonces deberá registrar el rechazo de la alternativa, no confirmar el reemplazo, mantener pendiente la sustitución del proveedor para el servicio afectado y continuar buscando otra alternativa

  @US-021 @CA-096 @negativo
  # @prueba: test_etapa9_casos_de_uso.py, test_h06_h07_h21_correcciones.py, test_h08_inicio_evento.py, test_sustitucion_maquina_estados.py
  Escenario: CA-096
    Dado que una sustitución de proveedor continúa pendiente y el evento está por iniciar
    Cuando inicie el evento sin que el reemplazo haya sido confirmado
    Entonces la sustitución deberá cerrarse como no procedente por inicio del evento, no deberá confirmarse el proveedor alternativo y deberá registrarse que el reemplazo no se concretó. Si el Evento no está cancelado, se aplicará la regla de devolución de CA-097. No deberán modificarse ni devolverse por este motivo los pagos del contrato original ni otros conceptos independientes
