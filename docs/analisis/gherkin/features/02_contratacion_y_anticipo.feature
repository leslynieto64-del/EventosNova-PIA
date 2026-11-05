# language: es
# Eventos Nova - Equipo 16 - Especificación Gherkin derivada de los criterios de aceptación aprobados.
# Fuente: Historias de usuario de Eventos Nova, versión 2.0 consolidada (US-001 a US-033, CA-001 a CA-114).
# Estos escenarios son especificación ejecutable; la verificación automatizada vigente se realiza con unittest (ver etiquetas @prueba).

Característica: Contratación, anticipo y devolución del anticipo

  # US-008 - Como Coordinador, quiero preparar el contrato con base en la propuesta aceptada y registrar su firma, para formalizar los servicios y condiciones acordadas con el Cliente.
  @US-008 @CA-015 @positivo
  # @prueba: test_etapa9_casos_de_uso.py, test_h13_criterios_aceptacion.py
  Escenario: CA-015
    Dado que existe una propuesta aceptada
    Cuando el Coordinador prepare el contrato
    Entonces debe tomar como base los servicios y condiciones acordadas

  @US-008 @CA-016 @positivo
  # @prueba: test_etapa9_casos_de_uso.py
  Escenario: CA-016
    Dado que el contrato fue preparado
    Cuando el Cliente lo revise
    Entonces deberá poder consultar los servicios, las condiciones acordadas y la política de no reembolso. El Coordinador deberá comunicar expresamente esta política al Cliente antes de confirmar la contratación

  @US-008 @CA-017 @positivo
  # @prueba: test_h13_criterios_aceptacion.py
  Escenario: CA-017
    Dado que el Coordinador preparó el contrato con base en la propuesta aceptada
    Cuando las partes lo firmen
    Entonces el contrato debe quedar registrado como firmado y vinculado a la propuesta aceptada

  # US-009 - Como Administración, quiero registrar y verificar el anticipo recibido, para llevar un control del pago realizado por el cliente.
  @US-009 @CA-018 @positivo
  # @prueba: test_estado_cuenta_maquina_estados.py, test_h10_anticipo_liquidado.py, test_reglas_corregidas.py
  Escenario: CA-018
    Dado que el contrato fue firmado
    Cuando el Cliente realice el anticipo
    Entonces Administración debe poder registrar y verificar el anticipo

  @US-009 @CA-019 @negativo
  # @prueba: test_anticipo_pagos_parciales_e3_e4.py, test_api_operaciones.py, test_especificaciones_negocio.py, test_estado_cuenta_maquina_estados.py, test_etapa9_casos_de_uso.py, test_h10_anticipo_liquidado.py, test_reglas_anticipo_decisiones_abc.py, test_reglas_corregidas.py
  Escenario: CA-019
    Dado que el Cliente realizó el anticipo
    Cuando Administración verifique el pago
    Entonces deberá comprobar que cubre al menos el 30 % del costo total de la propuesta aceptada. El 30 % es un mínimo que puede cubrirse con varios pagos parciales verificados del mismo contrato, que se acumulan: un pago menor al 30 % no se rechaza como «Importe incorrecto» y el anticipo se liquida cuando lo verificado alcanza el mínimo; un comprobante repetido sobre la misma obligación se rechaza (E-3, decisión del equipo registrada en el ADR-007, sin aprobación externa). Si el monto supera el 30 %, el requisito del anticipo se considera cubierto: el excedente no genera ninguna devolución automática ni se aplica automáticamente al saldo ni a otra obligación. La contratación solo podrá quedar confirmada cuando el anticipo sea correcto, el contrato esté firmado e incluya expresamente la política de no reembolso y se haya comunicado dicha política al Cliente antes de confirmar la contratación

  @US-009 @CA-106 @excepcional
  Escenario: CA-106
    Dado que la contratación se cerró sin confirmarse
    Cuando Administración reciba un pago de anticipo posterior al cierre
    Entonces podrá registrarlo y verificarlo sin reabrir ni confirmar la contratación y sin aplicarlo a ella. Si el Cliente desea continuar con la organización del evento, deberá iniciar un proceso nuevo

  @US-009 @CA-107 @excepcional
  # @prueba: test_anticipo_pagos_parciales_e3_e4.py
  Escenario: CA-107
    Dado que el costo total de la propuesta aceptada es 10 000 y el anticipo requerido es, como mínimo, de 3 000 (30 %)
    Cuando el Cliente pague un único anticipo de 4 000 (40 %)
    Entonces el requisito del anticipo deberá considerarse cubierto, la obligación del anticipo quedará Liquidada y el pago no deberá registrarse como importe incorrecto. No se generará ninguna devolución automática y el saldo del contrato original seguirá siendo de 7 000

  @US-009 @CA-108 @excepcional
  # @prueba: test_anticipo_pagos_parciales_e3_e4.py
  Escenario: CA-108
    Dado que el anticipo requerido es de 3 000 y el Cliente efectúa dos transferencias de anticipo de 3 000 con referencias distintas
    Cuando Administración registre y verifique ambas
    Entonces la obligación del anticipo quedará Liquidada con la primera, la segunda se registrará y verificará sin generar ninguna devolución automática y ninguna de las dos se aplicará al saldo ni a otra obligación

  # US-010 - Como Coordinador, quiero dar seguimiento al anticipo pendiente y contactar al Cliente cuando no se reciba dentro del plazo establecido, comunicándole que dispone de 24 horas naturales para efectuar el pago, para confirmar la situación del pago y evitar continuar con la contratación mientras el anticipo no esté registrado y verificado.
  @US-010 @CA-020 @positivo
  # @prueba: apoyo_maquina_estados_contrato.py, test_contrato_maquina_estados.py, test_h03_consultas_administracion.py, test_h10_anticipo_liquidado.py, test_reglas_corregidas.py
  Escenario: CA-020
    Dado que el contrato fue firmado y el anticipo no ha sido recibido dentro de los tres días hábiles posteriores a la firma
    Cuando el Coordinador dé seguimiento al pago
    Entonces debe contactar al Cliente para confirmar la situación del anticipo y comunicarle que, desde ese contacto, dispone de 24 horas naturales para efectuar el pago

  @US-010 @CA-021 @excepcional
  # @prueba: apoyo_maquina_estados_contrato.py, test_api_operaciones.py, test_contrato_maquina_estados.py, test_estado_cuenta_maquina_estados.py, test_h03_consultas_administracion.py, test_h10_anticipo_liquidado.py, test_reglas_anticipo_decisiones_abc.py, test_reglas_corregidas.py
  Escenario: CA-021
    Dado que el Coordinador contactó al Cliente por la falta de anticipo
    Cuando concluyan las 24 horas naturales posteriores a esa comunicación y se compruebe que el Cliente no efectuó el pago dentro de ellas
    Entonces el proceso de contratación deberá cerrarse, la contratación no deberá considerarse confirmada, no deberá iniciarse la contratación definitiva de los proveedores y el Evento deberá quedar en estado Cerrado sin contratación, no Cancelado. Si el Cliente efectuó el pago dentro de ese plazo, el proceso no deberá cerrarse aunque Administración lo registre o verifique después; la contratación quedará pendiente de esa verificación y solo se confirmará cuando el anticipo esté registrado y verificado correctamente. Al cerrarse así la contratación, no se reabre: el anticipo pendiente pasa a Sin efecto, el que ya estaba Liquidado conserva ese estado y el anticipo recibido se devuelve conforme a CA-102 a CA-105

  # US-032 - Como Administración, quiero registrar y ejecutar la devolución del anticipo recibido cuando la contratación se cierra sin confirmarse, para devolver al Cliente el importe que no se aplicó a una contratación confirmada y dejar constancia de su motivo, importe, fecha y comprobante.
  @US-032 @CA-102 @excepcional
  # @prueba: test_d3_llegada_de_t.py
  Escenario: CA-102
    Dado que la contratación se cerró sin confirmarse y el pago de anticipo ya estaba registrado al cerrarse
    Cuando Administración gestione la devolución
    Entonces deberá devolver el importe recibido como anticipo que no se aplicó a una contratación confirmada, incluida la parte que exceda el 30 %, dentro de los cinco días hábiles posteriores al día del cierre, que es la fecha de referencia y no cuenta en el plazo. Por ejemplo, con la contratación cerrada el viernes 20/11/2026, la devolución vence al final del viernes 27/11/2026, es decir, en el límite exclusivo de las 00:00 del 28/11/2026

  @US-032 @CA-103 @excepcional
  Escenario: CA-103
    Dado que la contratación se cerró sin confirmarse y el pago de anticipo se registra después del cierre
    Cuando Administración lo registre y lo verifique
    Entonces el pago no deberá aplicarse a esa contratación ni reactivarla y la fecha de referencia del plazo de devolución será el día del registro. Por ejemplo, con el pago registrado el lunes 23/11/2026, la devolución vence al final del lunes 30/11/2026

  @US-032 @CA-104 @excepcional
  Escenario: CA-104
    Dado que corresponde la devolución de un anticipo cuyo importe se verifica después de la fecha de referencia
    Cuando Administración realice la verificación
    Entonces el plazo de cinco días hábiles no se reiniciará y la verificación tardía formará parte del plazo ya iniciado. Un anticipo que quedó Liquidado conserva ese estado y también deberá devolverse, porque la contratación no llegó a confirmarse

  @US-032 @CA-105 @negativo
  # @prueba: test_d3_llegada_de_t.py
  Escenario: CA-105
    Dado que corresponde la devolución de un anticipo
    Cuando Administración la efectúe
    Entonces deberá registrar el pago de anticipo al que corresponde, el concepto, el importe, el motivo, la fecha de devolución y el comprobante, e informar al Coordinador. La devolución no podrá superar el importe efectivamente recibido por ese pago y cada pago generará, como máximo, una devolución
