# language: es
# Eventos Nova - Equipo 16 - Especificación Gherkin derivada de los criterios de aceptación aprobados.
# Fuente: Historias de usuario de Eventos Nova, versión 2.0 consolidada (US-001 a US-033, CA-001 a CA-114).
# Estos escenarios son especificación ejecutable; la verificación automatizada vigente se realiza con unittest (ver etiquetas @prueba).

Característica: Pagos, saldo del contrato original y consultas administrativas

  # US-011 - Como Coordinador, quiero consultar el estado de los pagos del evento, incluyendo el anticipo, los pagos registrados, el saldo pendiente del contrato original y su fecha límite, así como los importes correspondientes a cambios, cargos por cambio tardío y servicios adicionales, para dar seguimiento a los pagos, identificar los saldos vencidos y verificar qué conceptos están pendientes de pago.
  @US-011 @CA-022 @excepcional
  # @prueba: test_h03_consultas_administracion.py
  Escenario: CA-022
    Dado que existe un evento con pagos registrados
    Cuando el Coordinador consulte el estado de los pagos
    Entonces debe poder conocer los pagos realizados y el saldo pendiente

  @US-011 @CA-023 @excepcional
  # @prueba: test_d2_pago_tardio_del_saldo.py, test_estado_cuenta_maquina_estados.py, test_h03_consultas_administracion.py, test_openapi_exportada.py
  Escenario: CA-023
    Dado que el saldo pendiente del contrato original debe liquidarse como máximo tres días hábiles antes del evento
    Cuando el Coordinador consulte el estado de los pagos
    Entonces debe poder identificar el saldo pendiente, la fecha límite de pago y si el plazo ya venció

  @US-011 @CA-024 @excepcional
  # @prueba: test_h13_criterios_aceptacion.py
  Escenario: CA-024
    Dado que existe un saldo pendiente
    Cuando Administración lo identifique
    Entonces debe informar al Coordinador para que dé seguimiento al pago con el Cliente

  @US-011 @CA-025 @excepcional
  # @prueba: test_estado_cuenta_maquina_estados.py, test_h13_criterios_aceptacion.py
  Escenario: CA-025
    Dado que el saldo pendiente del contrato original venció
    Cuando el Coordinador active el procedimiento de cobro
    Entonces deberá enviar al Cliente un recordatorio amistoso, comunicar el monto pendiente y los cargos moratorios estipulados en el contrato, y registrar las acciones de seguimiento y las comunicaciones realizadas

  @US-011 @CA-026 @excepcional
  # @prueba: test_e3g_cargo_tardio_y_conceptos.py, test_estado_cuenta_maquina_estados.py, test_h03_consultas_administracion.py, test_h10_anticipo_liquidado.py, test_h13_criterios_aceptacion.py
  Escenario: CA-026
    Dado que un evento tiene un saldo pendiente del contrato original y también existen importes correspondientes a cambios, cargos por cambio tardío o servicios adicionales
    Cuando el Coordinador consulte el estado de los pagos
    Entonces cada concepto deberá aparecer registrado por separado con su importe y estado de pago, sin que el pago de uno se considere como liquidación de los demás

  @US-011 @CA-027 @negativo
  # @prueba: apoyo_esperados_oraculo.py, test_correcciones_etapas_3_a_7.py, test_decisiones_stakeholder.py, test_estado_cuenta_maquina_estados.py, test_h03_consultas_administracion.py, test_h08_inicio_evento.py, test_interfaz_textos.py, test_reglas_corregidas.py, test_regularizacion_solicitudes.py
  Escenario: CA-027
    Dado que el saldo pendiente del contrato original venció y se comunicaron al Cliente los cargos moratorios correspondientes
    Cuando transcurran las 24 horas naturales posteriores a dicha comunicación
    Entonces Administración deberá revisar los pagos recibidos y verificar si el Cliente liquidó dentro de ese plazo. Si el pago se realizó dentro del plazo, Administración deberá registrar y verificar la liquidación e informar al Coordinador para que se retome la organización del evento, siempre que se cumplan los demás requisitos aplicables. Si el Cliente no realizó el pago dentro del plazo, Administración deberá informar al Coordinador para que registre la cancelación del evento, indique el motivo e informe a las personas involucradas. El pago efectuado después de las 24 horas naturales no evitará la cancelación, aunque su registro formal todavía no se haya realizado. Si el pago se efectuó dentro del plazo, el cumplimiento se reconoce una vez comprobado, aunque Administración lo registre o verifique después de las 24 horas. El Coordinador registrará la cancelación en cuanto reciba el aviso, sin intervención automática del sistema y antes del inicio del evento; después del inicio la cancelación ya no procede y el adeudo permanece registrado. Al registrarse la cancelación, las solicitudes en trámite se cierran con el motivo «Evento cancelado»; una operación ya confirmada que todavía no se aplicó no se aplica al evento cancelado y se registra para su revisión

  @US-011 @CA-112 @excepcional
  Escenario: CA-112
    Dado que existen obligaciones de pago que quedaron Sin efecto
    Cuando se consulten los pagos realizados y pendientes, las fechas límite, los vencimientos y las devoluciones pendientes
    Entonces las obligaciones Sin efecto no deberán aparecer como pagos pendientes ni como vencidas. Una obligación Sin efecto nunca vuelve a otro estado

  @US-011 @CA-113 @excepcional
  # @prueba: apoyo_esperados_oraculo.py, test_d2_pago_tardio_del_saldo.py
  Escenario: CA-113
    Dado que venció el plazo de pago del saldo pendiente del contrato original
    Cuando el Cliente efectúe el pago del saldo después de esa fecha límite
    Entonces el pago no liquidará directamente el saldo: este seguirá vencido y el pago contará para la regularización, que requiere liquidar también los cargos moratorios conforme a CA-027

  # US-022 - Como Administración, quiero consultar la información de pagos, costos, proveedores, cambios y servicios adicionales de los eventos, para llevar un mejor control administrativo, revisar las solicitudes pendientes y autorizar los servicios adicionales que hayan sido aprobados previamente por el Cliente.
  @US-022 @CA-055 @positivo
  # @prueba: test_h03_consultas_administracion.py
  Escenario: CA-055
    Dado que Administración consulta un evento
    Cuando revise su información
    Entonces debe poder consultar los pagos, costos, proveedores, cambios y servicios correspondientes

  @US-022 @CA-056 @positivo
  # @prueba: test_h03_consultas_administracion.py
  Escenario: CA-056
    Dado que Administración necesita dar seguimiento a los eventos
    Cuando consulte la información de un evento
    Entonces debe poder identificar su estado actual

  @US-022 @CA-057 @positivo
  # @prueba: test_h03_consultas_administracion.py
  Escenario: CA-057
    Dado que existen pagos, costos, proveedores, cambios o servicios adicionales relacionados con un evento
    Cuando Administración consulte la información del evento
    Entonces debe poder identificar los pagos realizados y pendientes, los costos, los proveedores asignados, los cambios que requieran autorización y los servicios adicionales que requieran seguimiento o autorización

  @US-022 @CA-058 @negativo
  # @prueba: test_h03_consultas_administracion.py
  Escenario: CA-058
    Dado que existen elementos pendientes de seguimiento
    Cuando Administración consulte la información de los eventos
    Entonces deberá poder identificar los eventos próximos, los pagos pendientes, los cambios pendientes de autorización, los servicios aún no confirmados y las solicitudes de servicios adicionales, distinguiendo las que estén pendientes, pendientes de autorización, autorizadas, rechazadas o confirmadas
