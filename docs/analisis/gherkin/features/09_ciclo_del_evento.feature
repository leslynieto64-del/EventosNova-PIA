# language: es
# Eventos Nova - Equipo 16 - Especificación Gherkin derivada de los criterios de aceptación aprobados.
# Fuente: Historias de usuario de Eventos Nova, versión 2.0 consolidada (US-001 a US-033, CA-001 a CA-114).
# Estos escenarios son especificación ejecutable; la verificación automatizada vigente se realiza con unittest (ver etiquetas @prueba).

Característica: Inicio automático y finalización del evento

  # US-030 - Como Coordinador, quiero registrar que un evento se ha realizado y finalizado, para mantener actualizado su estado y distinguir los eventos concluidos de los que continúan en ejecución o fueron cancelados.
  @US-030 @CA-094 @positivo
  # @prueba: test_etapa9_casos_de_uso.py, test_evento_maquina_estados.py, test_h08_inicio_evento.py
  Escenario: CA-094
    Dado que el evento se llevó a cabo y concluyó
    Cuando el Coordinador registre su finalización
    Entonces el sistema deberá actualizar el estado del evento a Finalizado y registrar la fecha de finalización

  @US-030 @CA-095 @excepcional
  # @prueba: test_etapa9_casos_de_uso.py, test_evento_maquina_estados.py, test_h08_inicio_evento.py
  Escenario: CA-095
    Dado que un evento fue cancelado sin llevarse a cabo
    Cuando el Coordinador consulte o actualice su estado
    Entonces deberá conservarse como Cancelado y no deberá registrarse como Finalizado

  # US-033 - Como Coordinador, quiero que el Evento inicie automáticamente en la fecha y hora programadas y que lo que no llegó a confirmarse quede cerrado en ese momento, para que el estado del Evento, de su contratación y de sus solicitudes pendientes sea coherente desde el inicio.
  @US-033 @CA-109 @negativo
  # @prueba: test_d3_llegada_de_t.py
  Escenario: CA-109
    Dado que el Evento está En organización
    Cuando llegue la fecha y hora programadas (T)
    Entonces el Evento deberá iniciar automáticamente y pasar a En ejecución. El límite es inclusivo en T: en el instante T el Evento ya inició y, desde entonces, no se podrán solicitar cambios ni registrar nuevos servicios adicionales. Desde T no se tramita ningún servicio adicional: la solicitud presentada con el Evento iniciado se registra con el estado «No procedente» (motivo: el Evento ya inició) y se informa al Cliente, sin evaluar plazo ni saldo y sin generar cobro (GL-015, SE-004; interpretación del equipo, sin aprobación externa)

  @US-033 @CA-110 @negativo
  # @prueba: test_contrato_maquina_estados.py, test_d3_llegada_de_t.py
  Escenario: CA-110
    Dado que al llegar T el Evento sigue En gestión porque la contratación no llegó a confirmarse
    Cuando inicie el Evento
    Entonces el Evento deberá quedar Cerrado sin contratación, no Cancelado, y su contrato En preparación o Firmado deberá quedar Cerrado sin confirmar (D-3, decisión interna del equipo registrada en el ADR-008, sin aprobación externa). La contratación no podrá confirmarse después de T y el anticipo recibido, si existe, se devolverá conforme a CA-102 a CA-105. Un pago de anticipo registrado antes de T y verificado después de T se verifica sin confirmar ni reactivar la contratación y también se devuelve; su fecha de referencia es el día del cierre y la verificación tardía no reinicia el plazo (CA-104)

  @US-033 @CA-111 @excepcional
  # @prueba: test_d3_llegada_de_t.py
  Escenario: CA-111
    Dado que existen solicitudes de cambio, servicio adicional o sustitución de proveedor que no han sido confirmadas
    Cuando llegue T
    Entonces cada una deberá cerrarse con un único resultado conforme a CA-070, CA-071 y CA-096. Nada deberá confirmarse después de T y lo confirmado antes de T deberá aplicarse a la configuración del Evento
