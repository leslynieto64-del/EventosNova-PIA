"""Mensajes de resultado en español (cabeceras X-Mensaje / X-Mensaje-Tipo) y página /docs con aviso tras cada Execute.

Todo en memoria: no usa PostgreSQL ni ninguna base. Los cuerpos JSON y los códigos HTTP deben seguir siendo EXACTAMENTE los de antes.
Ejecutar desde la raíz:  python -m unittest tests.test_swagger_mensajes -v"""
import os, sys, unittest
from urllib.parse import unquote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
from fastapi.testclient import TestClient                                                    # noqa: E402
from api.documentacion import pagina_swagger                                                 # noqa: E402
from api.main import crear_app                                                               # noqa: E402
from api.mensajes import ADVERTENCIA, ERROR, EXITO, INFO, MensajesDeResultado, describir      # noqa: E402
from application.seguridad import COORDINADOR, ConfiguracionSeguridad           # noqa: E402
from infrastructure.composicion import construir                                              # noqa: E402
from infrastructure.persistencia.errores import ViolacionDeRestriccion                        # noqa: E402

DATOS = {'tipo': 'Boda', 'fecha_hora': '2026-11-20T18:00:00', 'lugar': 'Salón', 'invitados_aproximados': 100}
EVENTO = {'cliente_id': 'CL-1', 'datos': DATOS, 'servicios': ['Banquete']}
CONTENIDO = {'servicios': ['Banquete'], 'proveedores_considerados': ['PV-1'], 'costo_total': '10000.00', 'condiciones': 'Condiciones generales'}
CLAVE = 'una-contrasena-larga-y-unica-1'


def msg(r):
    """(mensaje legible, tipo): X-Mensaje viaja en ASCII (UTF-8 con codificación porcentual)."""
    r.headers['x-mensaje'].encode('ascii')
    return unquote(r.headers['x-mensaje']), r.headers['x-mensaje-tipo']


class Describir(unittest.TestCase):
    """La función pura que compone el mensaje."""
    def test_consulta_con_lista_cuenta_los_elementos(self):
        self.assertEqual(describir('GET', '/eventos', 200, {'eventos': [1, 2, 3]}), (INFO, 'Consulta realizada correctamente. Se encontraron 3 eventos.'))
        self.assertEqual(describir('GET', '/proveedores', 200, {'mensaje': 'x', 'datos': {'proveedores': list(range(6))}})[1],
                         'Consulta realizada correctamente. Se encontraron 6 proveedores.')
        self.assertEqual(describir('GET', '/solicitudes', 200, [1, 2])[1], 'Consulta realizada correctamente. Se encontraron 2 solicitudes.')
        self.assertIn('1 resultado', describir('GET', '/eventos', 200, {'eventos': [1]})[1])

    def test_consulta_sin_registros(self):
        self.assertEqual(describir('GET', '/eventos', 200, {'eventos': []}), (INFO, 'Consulta realizada correctamente. No se encontraron eventos.'))

    def test_consulta_sin_lista_o_con_varias_no_inventa_una_cantidad(self):
        self.assertEqual(describir('GET', '/health', 200, {'estado': 'ok'}), (INFO, 'Consulta realizada correctamente.'))
        self.assertEqual(describir('GET', '/x', 200, {'a': [1], 'b': [2]}), (INFO, 'Consulta realizada correctamente.'))

    def test_operacion_exitosa_usa_la_frase_especifica_solo_si_el_resultado_coincide(self):
        self.assertEqual(describir('POST', '/propuestas/{propuesta_id}/aceptacion', 200, {'mensaje': 'Propuesta aceptada.'}),
                         (EXITO, 'La propuesta fue aceptada correctamente.'))
        self.assertEqual(describir('POST', '/eventos/{evento_id}/cancelacion', 200, {'mensaje': 'Cancelación registrada por el Coordinador.'})[1],
                         'El evento fue cancelado correctamente.')
        # el evento YA estaba cancelado: no se afirma que «fue cancelado correctamente»; se muestra lo que dijo el servicio
        ya = describir('POST', '/eventos/{evento_id}/cancelacion', 200, {'mensaje': 'El evento ya estaba cancelado por esta causa.'})
        self.assertEqual(ya, (EXITO, 'Operación realizada correctamente. El evento ya estaba cancelado por esta causa.'))
        self.assertEqual(describir('POST', '/estados-cuenta/{estado_cuenta_id}/pagos', 200, {'mensaje': 'Pago Verificado.'})[1],
                         'El pago quedó registrado y verificado correctamente.')
        self.assertEqual(describir('POST', '/contratos/{contrato_id}/firma', 200, {'mensaje': 'Contrato firmado.'})[1], 'El contrato se firmó correctamente.')
        self.assertEqual(describir('POST', '/otra', 201, {})[1], 'Operación realizada correctamente.')

    def test_errores_http(self):
        self.assertEqual(describir('POST', '/auth/inicio-sesion', 401, {}), (ERROR, 'No se pudo iniciar sesión. Comprueba tus credenciales.'))
        self.assertIn('sesión expiró', describir('GET', '/usuarios', 401, {})[1])
        self.assertEqual(describir('POST', '/x', 403, {'detalle': 'No tiene permiso para realizar esta operación.'}),
                         (ERROR, 'No tienes permisos para realizar esta operación.'))
        self.assertEqual(describir('GET', '/x', 404, {'detail': 'Not Found'}), (ERROR, 'No se encontró el recurso solicitado.'))
        self.assertEqual(describir('GET', '/x', 404, {'detalle': 'El evento no existe.'})[1], 'No se encontró el recurso solicitado. El evento no existe.')
        self.assertEqual(describir('POST', '/x', 409, None),
                         (ADVERTENCIA, 'La operación no pudo completarse porque existe un conflicto con el estado actual.'))
        self.assertEqual(describir('GET', '/x', 500, None), (ERROR, 'Ocurrió un error interno. Intenta más tarde o contacta al administrador.'))
        self.assertEqual(describir('GET', '/x', 503, None)[0], ADVERTENCIA)

    def test_422_de_regla_de_negocio_y_de_validacion(self):
        tipo, texto = describir('POST', '/x', 422, {'tipo': 'rechazo_de_negocio', 'detalle': 'La fecha ya pasó.', 'pendientes': ['lugar']})
        self.assertEqual((tipo, texto), (ADVERTENCIA, 'No se pudo completar la operación: La fecha ya pasó. Pendiente: lugar.'))
        tipo, texto = describir('POST', '/x', 422, {'detail': [{'loc': ['body', 'cliente_id'], 'type': 'missing', 'msg': 'Field required'},
                                                                 {'loc': ['body', 'datos', 'invitados_aproximados'], 'type': 'int_parsing', 'msg': 'x'}]})
        self.assertEqual(tipo, ADVERTENCIA)
        self.assertEqual(texto, 'Hay datos no válidos en la solicitud: «cliente_id» es obligatorio; «datos.invitados_aproximados» debe ser un número entero.')

    def test_nunca_hay_exito_ni_consulta_con_un_error(self):
        for estado in (400, 401, 403, 404, 409, 422, 429, 500, 503):
            self.assertNotIn(describir('POST', '/x', estado, {})[0], (EXITO, INFO), estado)


class Cabeceras(unittest.TestCase):
    """Con la API real (composición en memoria, sin autenticación)."""
    def setUp(self):
        self.app = crear_app(lambda: construir())
        self.http = TestClient(self.app, raise_server_exceptions=False)

    def test_get_con_resultado_y_cantidad(self):
        self.assertEqual(self.http.post('/eventos', json=EVENTO).status_code, 201)
        r = self.http.get('/eventos', params={'desde': '2026-11-01T00:00:00', 'hasta': '2026-12-01T00:00:00'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(msg(r), ('Consulta realizada correctamente. Se encontró 1 resultado (eventos).', INFO))

    def test_get_sin_registros(self):
        r = self.http.get('/eventos', params={'desde': '2030-01-01T00:00:00', 'hasta': '2030-02-01T00:00:00'})
        self.assertEqual(r.json()['eventos'], [])
        self.assertEqual(msg(r), ('Consulta realizada correctamente. No se encontraron eventos.', INFO))

    def test_post_exitoso(self):
        r = self.http.post('/eventos', json=EVENTO)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(msg(r), ('El evento se registró correctamente.', EXITO))
        p = self.http.post(f"/eventos/{r.json()['evento_id']}/propuestas", json=CONTENIDO)
        self.assertEqual(p.status_code, 201, p.text)
        self.assertEqual(msg(p), ('La propuesta se creó correctamente.', EXITO))

    def test_404(self):
        r = self.http.get('/eventos/EV-NO-EXISTE/administracion')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(msg(r), ('No se encontró el recurso solicitado. El evento no existe.', ERROR))
        self.assertEqual(msg(self.http.get('/ruta-que-no-existe')), ('No se encontró el recurso solicitado.', ERROR))

    def test_422_de_validacion(self):
        r = self.http.post('/eventos', json={})
        self.assertEqual(r.status_code, 422)
        texto, tipo = msg(r)
        self.assertEqual(tipo, ADVERTENCIA)
        self.assertTrue(texto.startswith('Hay datos no válidos en la solicitud:'), texto)
        self.assertIn('«cliente_id» es obligatorio', texto)

    def test_422_de_regla_de_negocio(self):
        r = self.http.post('/eventos', json={**EVENTO, 'datos': {**DATOS, 'lugar': ''}})
        self.assertEqual(r.status_code, 422, r.text)
        self.assertIn('detalle', r.json())
        texto, tipo = msg(r)
        self.assertEqual(tipo, ADVERTENCIA)
        self.assertEqual(texto, 'No se pudo completar la operación: ' + r.json()['detalle'])

    def test_409(self):
        @self.app.get('/_prueba/conflicto')
        def conflicto():
            raise ViolacionDeRestriccion('duplicado', 'uq_x', 't')
        r = self.http.get('/_prueba/conflicto')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(msg(r)[1], ADVERTENCIA)
        self.assertTrue(msg(r)[0].startswith('La operación no pudo completarse porque existe un conflicto con el estado actual.'))

    def test_500_conserva_el_cuerpo_y_no_filtra_trazas_ni_detalles(self):
        @self.app.get('/_prueba/falla')
        def falla():
            raise RuntimeError('secreto-interno-no-debe-salir')
        r = self.http.get('/_prueba/falla')
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.text, 'Internal Server Error')                                     # igual que antes de esta mejora
        self.assertEqual(msg(r), ('Ocurrió un error interno. Intenta más tarde o contacta al administrador.', ERROR))
        self.assertNotIn('secreto-interno', str(r.headers))
        self.assertNotIn('Traceback', r.text)

    def test_los_cuerpos_y_codigos_son_los_mismos_con_y_sin_el_middleware(self):
        sin = crear_app(lambda: construir())
        sin.user_middleware = [m for m in sin.user_middleware if m.cls is not MensajesDeResultado]
        sin.middleware_stack = None
        a, b = self.http, TestClient(sin, raise_server_exceptions=False)
        for metodo, url, cuerpo in [('GET', '/health', None), ('GET', '/ready', None), ('GET', '/', None), ('POST', '/eventos', {}),
                                    ('POST', '/eventos', {**EVENTO, 'datos': {**DATOS, 'lugar': ''}}), ('GET', '/eventos/EV-X/administracion', None),
                                    ('GET', '/ruta-que-no-existe', None), ('GET', '/proveedores', None)]:
            ra, rb = a.request(metodo, url, json=cuerpo), b.request(metodo, url, json=cuerpo)
            self.assertEqual((ra.status_code, ra.json()), (rb.status_code, rb.json()), (metodo, url))
            self.assertNotIn('x-mensaje', rb.headers)
            self.assertIn('x-mensaje', ra.headers)
        ra = a.post('/eventos', json=EVENTO).json()
        rb = b.post('/eventos', json=EVENTO).json()
        self.assertEqual((set(ra), ra['mensaje']), (set(rb), rb['mensaje']))

    def test_la_interfaz_web_no_recibe_mensajes_y_sigue_sirviendose(self):
        for ruta in ('/app/', '/app/css/app.css', '/app/js/main.js'):
            r = self.http.get(ruta)
            self.assertEqual(r.status_code, 200, ruta)
            self.assertNotIn('x-mensaje', r.headers, ruta)

    def test_el_mensaje_cabe_en_una_cabecera(self):
        r = self.http.post('/eventos', json={**EVENTO, 'datos': {**DATOS, 'lugar': 'Salón\r\nX-Inyectada: 1 → «ñ» — “x”'}})
        for valor in r.headers.values():
            self.assertNotIn('\n', valor)
        self.assertNotIn('x-inyectada', r.headers)


class Autenticacion(unittest.TestCase):
    """401 y 403 con la autenticación activa."""
    def setUp(self):
        self.contenedor = construir()
        self.app = crear_app(lambda: self.contenedor, ConfiguracionSeguridad(activa=True))
        self.seg = self.contenedor.servicios.seguridad
        self.http = TestClient(self.app, raise_server_exceptions=False)

    def test_401_al_iniciar_sesion_con_credenciales_incorrectas(self):
        r = self.http.post('/auth/inicio-sesion', json={'correo': 'nadie@ejemplo.mx', 'contrasena': 'x'})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(msg(r), ('No se pudo iniciar sesión. Comprueba tus credenciales.', ERROR))

    def test_401_sin_sesion(self):
        r = self.http.get('/usuarios')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(msg(r)[1], ERROR)
        self.assertIn('Inicia sesión', msg(r)[0])

    def test_403_sin_permiso_y_login_correcto(self):
        self.seg.crear_usuario('coord@ejemplo.mx', 'Coordinadora', COORDINADOR, CLAVE, None)
        entrada = self.http.post('/auth/inicio-sesion', json={'correo': 'coord@ejemplo.mx', 'contrasena': CLAVE})
        self.assertEqual(entrada.status_code, 200)
        self.assertEqual(msg(entrada)[1], EXITO)
        r = self.http.get('/usuarios')                                                         # solo el administrador administra cuentas
        self.assertEqual(r.status_code, 403)
        self.assertEqual(msg(r), ('No tienes permisos para realizar esta operación.', ERROR))


class PaginaDocs(unittest.TestCase):
    def test_con_la_documentacion_habilitada_swagger_incluye_el_aviso(self):
        http = TestClient(crear_app(lambda: construir(), ConfiguracionSeguridad(activa=False, documentacion=True)))
        r = http.get('/docs')
        self.assertEqual(r.status_code, 200)
        self.assertIn('responseInterceptor', r.text)
        self.assertIn("x-mensaje-tipo", r.text)
        self.assertIn('/openapi.json', r.text)
        self.assertEqual(http.get('/openapi.json').status_code, 200)
        self.assertNotIn('x-mensaje', http.get('/docs').headers)

    def test_el_aviso_no_muestra_exito_si_la_respuesta_no_fue_correcta(self):
        pagina = pagina_swagger('Eventos Nova API')
        self.assertIn("if (!res.ok && (tipo === 'exito' || tipo === 'info')) tipo = 'error';", pagina)
        self.assertIn('textContent', pagina)                                                   # el mensaje nunca se interpreta como HTML
        self.assertNotIn('innerHTML', pagina)

    def test_en_produccion_la_documentacion_sigue_oculta(self):
        cfg = ConfiguracionSeguridad(activa=True, entorno='produccion', cookie_segura=True, hsts=True, documentacion=False)
        http = TestClient(crear_app(lambda: construir(), cfg))
        for ruta in ('/docs', '/redoc', '/openapi.json'):
            self.assertEqual(http.get(ruta).status_code, 404, ruta)


if __name__ == '__main__':
    unittest.main()
