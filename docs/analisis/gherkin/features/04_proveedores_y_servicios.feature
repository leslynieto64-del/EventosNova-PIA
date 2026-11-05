# language: es
# Eventos Nova - Equipo 16 - Especificación Gherkin derivada de los criterios de aceptación aprobados.
# Fuente: Historias de usuario de Eventos Nova, versión 2.0 consolidada (US-001 a US-033, CA-001 a CA-114).
# Estos escenarios son especificación ejecutable; la verificación automatizada vigente se realiza con unittest (ver etiquetas @prueba).

Característica: Proveedores y servicios contratados

  # US-012 - Como Coordinador, quiero dar seguimiento a los servicios pendientes de confirmación, para mantener el control de los servicios que aún no están completamente confirmados.
  @US-012 @CA-028 @positivo
  # @prueba: test_h03_consultas_administracion.py
  Escenario: CA-028
    Dado que existen servicios que aún no están completamente confirmados
    Cuando el Coordinador dé seguimiento al evento
    Entonces debe poder identificar y dar seguimiento a los servicios pendientes

  # US-013 - Como Coordinador, quiero consultar la disponibilidad de los proveedores, para seleccionar los que puedan proporcionar los servicios contratados.
  @US-013 @CA-029 @positivo
  # @prueba: test_h01_h02_proveedores.py, test_interfaz_textos.py
  Escenario: CA-029
    Dado que el Coordinador necesita contratar un servicio
    Cuando consulte a los proveedores
    Entonces debe poder conocer su disponibilidad para la fecha del evento

  @US-013 @CA-030 @positivo
  # @prueba: test_h01_h02_proveedores.py
  Escenario: CA-030
    Dado que un proveedor no está disponible
    Cuando el Coordinador revise las opciones
    Entonces debe poder considerar otro proveedor disponible

  # US-014 - Como Coordinador, quiero asignar proveedores a los servicios del evento, para organizar la prestación de cada servicio.
  @US-014 @CA-031 @positivo
  # @prueba: test_h01_h02_proveedores.py, test_interfaz_textos.py
  Escenario: CA-031
    Dado que el Coordinador ha seleccionado un proveedor disponible
    Cuando lo asigne a un servicio
    Entonces el proveedor debe quedar relacionado con el servicio correspondiente del evento

  @US-014 @CA-032 @positivo
  # @prueba: test_h01_h02_proveedores.py
  Escenario: CA-032
    Dado que un proveedor fue asignado a un servicio
    Cuando se consulte la información del evento
    Entonces debe poder identificarse el proveedor asignado

  # US-015 - Como Proveedor, quiero consultar la información necesaria del evento y del servicio asignado, para conocer las condiciones del servicio que debe proporcionar.
  @US-015 @CA-033 @positivo
  # @prueba: test_h01_h02_proveedores.py
  Escenario: CA-033
    Dado que el Proveedor tiene un servicio asignado
    Cuando consulte la información del evento
    Entonces debe poder conocer la fecha, hora, lugar, tipo de evento y número aproximado de invitados

  @US-015 @CA-034 @positivo
  # @prueba: test_h01_h02_proveedores.py
  Escenario: CA-034
    Dado que el Proveedor tiene un servicio asignado
    Cuando consulte la información del servicio
    Entonces debe poder conocer las características, cantidades y condiciones acordadas

  # US-016 - Como Proveedor, quiero confirmar mi disponibilidad y las condiciones del servicio, para informar si puede proporcionar el servicio contratado.
  @US-016 @CA-035 @positivo
  # @prueba: test_h01_h02_proveedores.py, test_h03_consultas_administracion.py
  Escenario: CA-035
    Dado que un servicio fue asignado al Proveedor
    Cuando revise la fecha y las condiciones del servicio
    Entonces debe poder confirmar si está disponible para realizarlo

  @US-016 @CA-036 @positivo
  # @prueba: test_h01_h02_proveedores.py, test_h03_consultas_administracion.py
  Escenario: CA-036
    Dado que el Proveedor no puede realizar el servicio
    Cuando informe su situación al Coordinador
    Entonces el Coordinador debe poder conocer que el servicio no está disponible
