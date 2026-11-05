# language: es
# Escenarios complementarios de las decisiones aprobadas S-1 a S-9 y D-P1 a D-P3 (ADR-009, ADR-010, ADR-011).
# Cada escenario corresponde a una prueba automatizada existente indicada en @prueba.

Característica: Cuentas, catálogo de proveedores y procedencia de respuestas

  # HC-01
  @HC-01 @HC-01-E1 @positivo
  # @prueba: test_seguridad.py
  Escenario: HC-01-E1 - El Administrador crea una cuenta con uno de los tres roles
    Dado que el Administrador inició sesión
    Cuando registre una cuenta con rol Coordinador
    Entonces la cuenta queda activa con ese rol y sin permisos administrativos

  @HC-01 @HC-01-E2 @negativo
  # @prueba: test_decisiones_s1_s9.py
  Escenario: HC-01-E2 - No se puede crear una cuenta para el Cliente ni con un rol inexistente
    Dado que el Administrador inició sesión
    Cuando intente crear una cuenta con un rol distinto de Administrador, Coordinador o Proveedor
    Entonces el sistema rechaza la operación

  @HC-01 @HC-01-E3 @excepcional
  # @prueba: test_seguridad.py
  Escenario: HC-01-E3 - El sistema no puede quedar sin administrador
    Dado que existe una sola cuenta activa de Administrador
    Cuando se intente desactivarla
    Entonces el sistema rechaza la operación

  # HC-02
  @HC-02 @HC-02-E1 @positivo
  # @prueba: test_seguridad.py
  Escenario: HC-02-E1 - Inicio de sesión con credenciales válidas
    Dado que existe una cuenta activa
    Cuando la persona inicie sesión con su correo y contraseña
    Entonces recibe una sesión con cookie HttpOnly y un token CSRF
    Y solo puede ejecutar las operaciones de su rol

  @HC-02 @HC-02-E2 @negativo
  # @prueba: test_seguridad.py
  Escenario: HC-02-E2 - Credenciales incorrectas
    Dado que existe una cuenta activa
    Cuando se intente iniciar sesión con una contraseña incorrecta
    Entonces el sistema rechaza el acceso con el mismo mensaje que para un correo inexistente

  @HC-02 @HC-02-E3 @excepcional
  # @prueba: test_seguridad.py
  Escenario: HC-02-E3 - Bloqueo por intentos fallidos
    Dado que se registraron 5 intentos fallidos para el mismo correo e IP
    Cuando se intente iniciar sesión otra vez
    Entonces el acceso queda bloqueado durante 15 minutos

  # HC-03
  @HC-03 @HC-03-E1 @positivo
  # @prueba: test_decisiones_dp2_s7_s8.py
  Escenario: HC-03-E1 - Coordinación registra un proveedor en el catálogo
    Dado que el Coordinador inició sesión
    Cuando registre un proveedor con nombre y servicios
    Entonces el proveedor queda activo y puede consultarse

  @HC-03 @HC-03-E2 @negativo
  # @prueba: test_decisiones_dp2_s7_s8.py
  Escenario: HC-03-E2 - Coordinación no edita ni desactiva proveedores
    Dado que el Coordinador inició sesión
    Cuando intente editar, desactivar o reactivar un proveedor
    Entonces el servidor rechaza la operación por falta de permiso

  @HC-03 @HC-03-E3 @excepcional
  # @prueba: test_decisiones_dp2_s7_s8.py
  Escenario: HC-03-E3 - Un proveedor desactivado conserva su historial
    Dado que un proveedor tiene asignaciones
    Cuando el Administrador lo desactive
    Entonces conserva su historial y sus asignaciones
    Y deja de ofrecerse como candidato para nuevas asignaciones

  # HC-04
  @HC-04 @HC-04-E1 @positivo
  # @prueba: test_decisiones_s1_s9.py
  Escenario: HC-04-E1 - El proveedor responde directamente
    Dado que un servicio está asignado al proveedor y pendiente de confirmación
    Cuando el Proveedor registre su respuesta con su cuenta
    Entonces la respuesta queda con origen Proveedor
    Y el servicio queda Confirmado por el proveedor o Proveedor no disponible

  @HC-04 @HC-04-E2 @positivo
  # @prueba: test_decisiones_s1_s9.py
  Escenario: HC-04-E2 - Coordinación registra la respuesta con su procedencia
    Dado que el proveedor respondió por teléfono, mensaje o correo
    Cuando el Coordinador registre la respuesta indicando el medio
    Entonces la respuesta queda con origen Coordinación, medio, persona que la registró y fecha

  @HC-04 @HC-04-E3 @negativo
  # @prueba: test_decisiones_s1_s9.py; test_seguridad.py
  Escenario: HC-04-E3 - Nadie suplanta el origen ni responde por otro proveedor
    Dado que un servicio está asignado a un proveedor
    Cuando otra cuenta de proveedor intente responder o enviar otro origen
    Entonces el sistema rechaza la operación y no expone información de otros proveedores

  # HC-05
  @HC-05 @HC-05-E1 @positivo
  # @prueba: test_decisiones_dp1_dp3.py
  Escenario: HC-05-E1 - Coordinación captura costo y condiciones
    Dado que un servicio adicional está registrado y hay un proveedor activo del catálogo que ofrece el servicio
    Cuando el Coordinador registre el costo y las condiciones del proveedor
    Entonces Administración puede verlos antes de autorizar

  @HC-05 @HC-05-E2 @negativo
  # @prueba: test_decisiones_dp1_dp3.py
  Escenario: HC-05-E2 - Costo inválido
    Dado que un servicio adicional está registrado
    Cuando se capture un costo cero, negativo o ausente, o condiciones vacías
    Entonces el servidor rechaza la captura

  # HC-06
  @HC-06 @HC-06-E1 @positivo
  # @prueba: test_decisiones_s1_s9.py
  Escenario: HC-06-E1 - Importe adicional de una sustitución
    Dado que una sustitución autorizada tiene costo adicional
    Cuando el Administrador integre el importe adicional
    Entonces se crea una sola obligación con concepto SustitucionProveedor y trazabilidad

  @HC-06 @HC-06-E2 @excepcional
  # @prueba: test_decisiones_s1_s9.py
  Escenario: HC-06-E2 - Sustitución sin costo adicional
    Dado que una sustitución autorizada no tiene costo adicional
    Cuando se confirme la sustitución
    Entonces no se crea ninguna obligación de pago
