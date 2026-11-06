"""Siembra de datos de demostración (scripts/sembrar_datos_demo.py): modos, idempotencia, recuperación, permisos, seguridad y destino.

El script se ejecuta contra la API REAL en proceso (TestClient de FastAPI) y la base de PRUEBAS aislada (`TEST_DATABASE_URL`, nombre terminado en `_test`):
nunca contra un servidor ni una base de desarrollo, manual o de producción. Las contraseñas y las confirmaciones se simulan con funciones inyectadas.
Ejecutar desde la raíz:  python -m unittest tests.test_sembrar_datos_demo -v"""
import contextlib
import importlib.util
import io
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
import httpx  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from anyio.from_thread import start_blocking_portal  # noqa: E402
from apoyo_bd import BaseConBD  # noqa: E402
from argon2 import PasswordHasher  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api.main import crear_app  # noqa: E402
from application.seguridad import MATRIZ, ConfiguracionSeguridad, autoriza  # noqa: E402
from infrastructure.persistencia import configuracion as C  # noqa: E402
from infrastructure.persistencia.composicion_persistente import construir_persistente  # noqa: E402

RUTA_SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'sembrar_datos_demo.py'
_spec = importlib.util.spec_from_file_location('sembrar_datos_demo', RUTA_SCRIPT)
S = importlib.util.module_from_spec(_spec)
sys.modules['sembrar_datos_demo'] = S
_spec.loader.exec_module(S)

CORREO_ADMIN = 'admin.ensayo@eventosnova.example'
CLAVES = {'administrador': 'Admin-ensayo-clave-larga-1', 'coordinador': 'Coord-ensayo-clave-larga-2', 'proveedor': 'Prov-ensayo-clave-larga-3'}
URL = 'http://127.0.0.1:8002'
URL_PROD = 'https://demo.eventosnova.example'
AHORA = datetime(2026, 11, 5, 12, 0, 0)


class Interrupcion(BaseException):
    """Simula la caída del proceso en mitad de la siembra."""


class Proxy:
    """Cliente HTTP en proceso que anota cada llamada (método, ruta, cabeceras) y, si se pide, 'cae' antes o después de enviar un POST."""
    def __init__(self, http, llamadas, regla=None):
        self.http, self.llamadas, self.regla = http, llamadas, regla

    def request(self, metodo, ruta, **kw):
        self.llamadas.append((metodo, ruta.split('?')[0], dict(kw.get('headers') or {})))
        r = self.regla
        if r and metodo == 'POST' and not r['hecho'] and re.search(r['patron'], ruta):
            r['visto'] += 1
            if r['visto'] == r.get('n', 1):
                r['hecho'] = True
                if r['cuando'] == 'despues':
                    self.http.request(metodo, ruta, **kw)              # el servidor lo procesa; el proceso cae antes de leer la respuesta
                raise Interrupcion()
        return self.http.request(metodo, ruta, **kw)


def caida(patron, cuando='despues', n=1):
    return {'patron': patron, 'cuando': cuando, 'n': n, 'visto': 0, 'hecho': False}


class Api:
    """Cliente de comprobación (independiente del script) con su propia sesión."""
    def __init__(self, app, url=URL):
        self.http, self.csrf, self.url = TestClient(app, base_url=url), None, url

    def entrar(self, rol):
        correo = {'administrador': CORREO_ADMIN, 'coordinador': S.CORREO_COORDINADOR, 'proveedor': S.CORREO_PROVEEDOR}[rol]
        r = self.http.post('/auth/inicio-sesion', json={'correo': correo, 'contrasena': CLAVES[rol]})
        assert r.status_code == 200, r.text
        self.csrf = r.json()['datos']['csrf']
        return self

    def get(self, ruta, **kw):
        return self.http.get(ruta, **kw)

    def post(self, ruta, cuerpo=None):
        return self.http.post(ruta, json=cuerpo or {}, headers={'X-CSRF-Token': self.csrf, 'Origin': self.url})


BASES_PROHIBIDAS = ('eventosnova', 'eventosnova_manual_test')


def exigir_base_de_pruebas(url):
    """Devuelve el nombre de la base si `url` es una base LOCAL de pruebas admitida (la del CI, `eventosnova_test`, o una propia terminada en `_test`).
    En cualquier otro caso lanza AssertionError. El mensaje nunca incluye la cadena de conexión ni credenciales (solo el nombre de la base)."""
    if not url or not isinstance(url, str):
        raise AssertionError('TEST_DATABASE_URL no está definida.')
    try:
        normalizada = C.normalizar_url(url)
        base = str(C.descripcion_segura(normalizada)['base'])
    except Exception:
        raise AssertionError('TEST_DATABASE_URL no es una URL de base de datos válida.') from None
    if not normalizada.startswith('postgresql+psycopg://') or not base:
        raise AssertionError('TEST_DATABASE_URL debe ser una URL de PostgreSQL con el nombre de la base.')
    if base in BASES_PROHIBIDAS or base in C.bases_protegidas():
        raise AssertionError(f'La base «{base}» está protegida: estas pruebas vacían sus tablas y no pueden usarla.')
    if not C.es_base_local_de_pruebas(normalizada):
        raise AssertionError(f'La base «{base}» no cumple las reglas de seguridad del proyecto (servidor local, nombre terminado en «_test» y sin «manual»).')
    return base


class BaseSiembra(BaseConBD):
    @classmethod
    def setUpClass(cls):
        """Estas pruebas VACÍAN tablas. Exigen TEST_DATABASE_URL explícita (nunca DATABASE_URL como alternativa) y demuestran, ANTES de conectar y de nuevo con
        la conexión abierta, que el destino es una base de pruebas; si no pueden demostrarlo, se detienen sin tocar nada."""
        url = C.url_pruebas()                                             # TEST_DATABASE_URL (entorno o .env); jamás DATABASE_URL
        if not url:
            if os.environ.get('EVENTOSNOVA_REQUIERE_BD') == '1':
                raise AssertionError('TEST_DATABASE_URL es obligatoria (EVENTOSNOVA_REQUIERE_BD=1) y no está definida.')
            raise unittest.SkipTest('TEST_DATABASE_URL no está definida: estas pruebas no usan ninguna otra URL como alternativa.')
        esperada = exigir_base_de_pruebas(url)
        super().setUpClass()
        with cls.motor.connect() as con:
            real = con.execute(sa.text('select current_database()')).scalar()
        if real != esperada:
            raise AssertionError(f'La conexión abierta apunta a «{real}», no a la base validada «{esperada}»: se detiene la ejecución.')
        exigir_base_de_pruebas(C.url_con_base(url, real))

    def setUp(self):
        super().setUp()
        self.cont = construir_persistente(motor=self.motor)
        self.app = crear_app(lambda: self.cont, ConfiguracionSeguridad(activa=True))
        self.cont.servicios.seguridad._hasher = PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)       # solo pruebas: Argon2 más barato
        self.cont.servicios.seguridad.crear_usuario(CORREO_ADMIN, 'Administrador de ensayo', 'administrador', CLAVES['administrador'])
        self.dir = tempfile.mkdtemp(prefix='sembrado_')
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.llamadas, self.prompts, self.ahora = [], [], AHORA

    # -- ejecución del script
    def correr(self, *args, url=URL, entorno='local', entradas=(), regla=None, claves=None):
        salida, errores, entradas = [], [], list(entradas)
        claves = claves or CLAVES

        def pedir_clave(prompt):
            self.prompts.append(prompt)
            for rol, clave in claves.items():
                if rol in prompt.lower():
                    return clave
            raise AssertionError('Solicitud de contraseña inesperada: ' + prompt)

        def pedir_texto(prompt):
            self.prompts.append(prompt)
            if not entradas:
                raise EOFError()                                          # sin entrada disponible: confirmación ausente
            return entradas.pop(0)

        with start_blocking_portal() as portal:                      # un solo bucle de eventos para todas las peticiones: la suite es mucho más rápida
            def fabrica(d):
                cliente = TestClient(self.app, base_url=d.base_url, follow_redirects=False)
                cliente.portal = portal
                return Proxy(cliente, self.llamadas, regla)
            codigo = S.main(['--base-url', url, '--entorno', entorno, '--admin-correo', CORREO_ADMIN, *args], fabrica_http=fabrica, getpass_fn=pedir_clave,
                            input_fn=pedir_texto, salida=salida.append, error=errores.append, directorio_estado=Path(self.dir),
                            ahora_fn=lambda: self.ahora, esperar=lambda s: None, registro_http=self.registro)
        return codigo, '\n'.join(salida), '\n'.join(errores)

    @property
    def registro(self):
        if not hasattr(self, '_registro'):
            self._registro = []
        return self._registro

    def posts(self, contiene=None):
        return [r for r in self.registro if r[1] == 'POST' and (contiene is None or contiene in r[2])]

    def sembrar(self, *args, **kw):
        codigo, salida, error = self.correr('--aplicar', *args, **kw)
        self.assertEqual(codigo, 0, error)
        return salida

    def nuevo_ciclo(self):
        self.registro.clear()
        self.llamadas.clear()
        self.prompts.clear()

    # -- consultas de comprobación
    def eventos(self):
        r = Api(self.app).entrar('administrador').get('/eventos', params={'desde': S.VENTANA_DESDE, 'hasta': S.VENTANA_HASTA})
        return {e['clienteId']: e for e in r.json()['eventos']}

    def admin(self, eid):
        return Api(self.app).entrar('administrador').get(f'/eventos/{eid}/administracion').json()

    def crear_coordinador(self):
        self.cont.servicios.seguridad.crear_usuario(S.CORREO_COORDINADOR, S.NOMBRE_COORDINADOR, 'coordinador', CLAVES['coordinador'])


class PrimeraYSegundaEjecucion(BaseSiembra):
    def test_simular_no_inicia_sesion_ni_escribe(self):
        codigo, salida, _ = self.correr()                                       # --simular es el modo por omisión
        self.assertEqual(codigo, 0)
        self.assertIn('SIMULACIÓN', salida)
        self.assertEqual(self.prompts, [])                                     # ni contraseñas ni confirmaciones
        self.assertEqual({(m, ruta) for _, m, ruta, _ in self.registro}, {('GET', '/health'), ('GET', '/ready')})
        self.assertEqual([self.contar(t) for t in ('usuario', 'sesion', 'proveedor', 'evento')], [1, 0, 0, 0])
        self.assertEqual(os.listdir(self.dir), [])                             # ni progreso ni candado
        c2, _, _ = self.correr('--simular')
        self.assertEqual(c2, 0)

    def test_verificar_estado_inicia_sesion_y_solo_hace_get_de_negocio(self):
        codigo, salida, error = self.correr('--verificar-estado')
        self.assertEqual(codigo, 0, error)
        self.assertIn('REGISTRA UNA SESIÓN', salida)
        self.assertEqual([r[2] for r in self.posts()], ['/auth/inicio-sesion'])      # el único POST es el inicio de sesión
        self.assertEqual(len(self.prompts), 1)                                     # solo la contraseña del administrador
        self.assertEqual([self.contar(t) for t in ('usuario', 'proveedor', 'evento', 'sesion')], [1, 0, 0, 1])
        self.assertEqual(os.listdir(self.dir), [])                             # no escribe progreso ni candado
        self.assertIn('PENDIENTE', salida)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.correr('--verificar-estado', '--simular')[0], 2)      # modos excluyentes (argparse)

    def test_primera_ejecucion_crea_el_conjunto_aprobado(self):
        self.sembrar()
        self.assertEqual([self.contar(t) for t in ('usuario', 'proveedor', 'evento', 'propuesta', 'contrato', 'pago')], [3, 6, 3, 3, 2, 2])
        ev = self.eventos()
        self.assertEqual(sorted(ev), ['CL-DEMO-01', 'CL-DEMO-02', 'CL-DEMO-03'])
        self.assertEqual([ev[e.cliente_id]['fechaHora'] for e in S.EVENTOS], ['2027-03-20T18:00:00', '2027-04-17T18:00:00', '2027-05-22T18:00:00'])
        self.assertTrue(all('[DEMO]' in e['tipoEvento'] and '[DEMO]' in e['lugar'] for e in ev.values()))
        e1, e2, e3 = (self.admin(ev[c]['eventoId']) for c in ('CL-DEMO-01', 'CL-DEMO-02', 'CL-DEMO-03'))
        self.assertEqual((e1['estadoEvento'], e1['contratos']), ('En gestión', []))
        self.assertEqual((e2['estadoEvento'], e2['contratos'][0]['estado'], e2['pagosRealizados'], e2['saldoPendienteContratoOriginal']),
                         ('En organización', 'Contratación confirmada', '3000.00', '7000.00'))
        self.assertEqual(e3['estadoEvento'], 'Cancelado')
        api = Api(self.app).entrar('administrador')
        self.assertEqual(api.get(f"/eventos/{ev['CL-DEMO-01']['eventoId']}/propuestas").json()['propuestas'][0]['estado'], 'En revisión del Cliente')
        banquete = next(s for s in e2['proveedores'] if s['servicio'] == 'Banquete')
        self.assertEqual(banquete['estado'], 'Pendiente de confirmación del proveedor')            # D-1: queda pendiente por omisión
        self.assertTrue(all('[DEMO]' in p['nombre'] for p in api.get('/proveedores').json()['datos']['proveedores']))
        # contraseñas: administrador 1 vez (existe); coordinador y proveedor, cuentas nuevas, dos veces cada una
        self.assertEqual([sum(1 for p in self.prompts if rol in p.lower()) for rol in ('administrador', 'coordinador', 'proveedor')], [1, 2, 2])
        pasos = json.loads(next(Path(self.dir).glob('sembrado_demo_progreso_*.json')).read_text(encoding='utf-8'))['pasos']
        self.assertEqual({pasos[k]['estado'] for k in ('E2.politica', 'E2.firma', 'E2.anticipo', 'E3.cancelacion', 'E3.revision')}, {'hecho'})
        self.assertEqual(pasos['E3.revision']['pagos_realizados'], '3000.00')

    def test_segunda_ejecucion_no_duplica_ni_escribe(self):
        self.sembrar()
        antes = [self.contar(t) for t in ('usuario', 'proveedor', 'evento', 'propuesta', 'contrato', 'pago')]
        self.nuevo_ciclo()
        salida = self.sembrar()
        self.assertEqual([r[2] for r in self.posts()], ['/auth/inicio-sesion'] * 3)           # solo los tres inicios de sesión
        self.assertEqual([self.contar(t) for t in ('usuario', 'proveedor', 'evento', 'propuesta', 'contrato', 'pago')], antes)
        self.assertIn('0 creados', salida)
        self.assertEqual([sum(1 for p in self.prompts if rol in p.lower()) for rol in ('administrador', 'coordinador', 'proveedor')], [1, 1, 1])
        self.nuevo_ciclo()
        codigo, salida, _ = self.correr('--verificar-estado', '--incluir-proveedor')
        self.assertEqual(codigo, 0)
        self.assertIn('0 pendientes', salida)

    def test_coherencia_de_eventos_propuestas_contratos_y_pagos(self):
        self.sembrar()
        ev = self.eventos()
        api = Api(self.app).entrar('administrador')
        for cliente in ('CL-DEMO-02', 'CL-DEMO-03'):
            eid = ev[cliente]['eventoId']
            adm = self.admin(eid)
            props = api.get(f'/eventos/{eid}/propuestas').json()['propuestas']
            self.assertEqual([p['estado'] for p in props], ['Aceptada'])
            self.assertEqual([c['costoTotal'] for c in adm['contratos']], ['10000.00'])
            anticipo = api.get(f'/eventos/{eid}/pagos').json()['estadosCuenta'][0]['anticipo']
            self.assertEqual((anticipo['estado'], anticipo['pagado']), ('Liquidada', '3000.00'))
            self.assertEqual(adm['pagosRealizados'], '3000.00')
        self.assertEqual([c for c in self.admin(ev['CL-DEMO-01']['eventoId'])['contratos']], [])


class RecuperacionDeInterrupciones(BaseSiembra):
    def interrumpir(self, patron, cuando='despues', n=1):
        with self.assertRaises(Interrupcion):
            self.correr('--aplicar', regla=caida(patron, cuando, n))
        self.assertFalse(list(Path(self.dir).glob('*.lock')))                  # el candado se libera aunque el proceso se interrumpa (salvo un kill)
        self.nuevo_ciclo()

    def contar_estado(self):
        return [self.contar(t) for t in ('usuario', 'proveedor', 'evento', 'propuesta', 'contrato', 'pago')]

    def test_respuesta_perdida_al_crear_un_evento_no_lo_duplica(self):
        self.interrumpir(r'^/eventos$', 'despues', n=2)
        self.assertEqual(self.contar('evento'), 2)
        self.sembrar()
        self.assertEqual(len(self.posts('/eventos')) - len(self.posts('/eventos/')), 1)         # solo se crea el tercero
        self.assertEqual(self.contar_estado(), [3, 6, 3, 3, 2, 2])

    def test_respuesta_perdida_al_crear_un_proveedor_no_lo_duplica(self):
        self.interrumpir(r'^/proveedores$', 'despues', n=3)
        self.sembrar()
        self.assertEqual(len([r for r in self.posts('/proveedores') if r[2] == '/proveedores']), 3)
        self.assertEqual(self.contar('proveedor'), 6)

    def test_politica_perdida_detiene_y_exige_recuperacion_explicita(self):
        self.interrumpir(r'comunicacion-politica', 'despues')
        codigo, _, error = self.correr('--aplicar')
        self.assertEqual(codigo, 1)
        self.assertIn('NO se repite automáticamente', error)
        self.assertEqual(self.posts('comunicacion-politica'), [])                 # jamás se reenvía sola
        self.assertEqual(self.posts('/firma'), [])
        self.nuevo_ciclo()
        self.assertEqual(self.correr('--aplicar', '--reanudar-politica', 'CL-DEMO-02', entradas=['no es la frase'])[0], 1)
        self.assertEqual(self.posts('comunicacion-politica'), [])
        self.nuevo_ciclo()
        self.assertEqual(self.correr('--aplicar', '--reanudar-politica', 'CL-DEMO-02', entradas=[S.FRASE_POLITICA])[0], 0)
        self.assertEqual(len(self.posts('comunicacion-politica')), 2)             # E2 (reanudada, una vez) + E3 (normal)
        self.assertEqual(self.contar_estado(), [3, 6, 3, 3, 2, 2])
        pasos = json.loads(next(Path(self.dir).glob('sembrado_demo_progreso_*.json')).read_text(encoding='utf-8'))['pasos']
        self.assertTrue(pasos['E2.politica']['repetida_con_autorizacion'])
        self.assertNotIn('repetida_con_autorizacion', pasos['E3.politica'])

    def test_interrupcion_antes_de_la_firma_no_repite_la_politica(self):
        self.interrumpir(r'/firma$', 'antes')
        self.sembrar()
        self.assertEqual(len(self.posts('comunicacion-politica')), 1)             # solo la de E3
        self.assertEqual(len(self.posts('/firma')), 2)                            # la pendiente de E2 y la de E3

    def test_pago_perdido_no_se_repite(self):
        self.interrumpir(r'/pagos$', 'despues')
        self.assertEqual(self.contar('pago'), 1)
        self.sembrar()
        self.assertEqual(len(self.posts('/pagos')), 1)                            # solo el de E3
        self.assertEqual(self.contar('pago'), 2)

    def test_cancelacion_perdida_no_se_repite_y_la_revision_continua(self):
        self.interrumpir(r'/cancelacion$', 'despues')
        self.sembrar()
        self.assertEqual(self.posts('/cancelacion'), [])
        self.assertEqual(len(self.posts('revision-administrativa')), 1)

    def test_revision_perdida_detiene_y_exige_recuperacion_explicita(self):
        self.interrumpir(r'revision-administrativa', 'despues')
        codigo, _, error = self.correr('--aplicar')
        self.assertEqual(codigo, 1)
        self.assertIn('revisión administrativa', error)
        self.assertEqual(self.posts('revision-administrativa'), [])
        self.nuevo_ciclo()
        self.assertEqual(self.correr('--aplicar', '--reanudar-revision', entradas=[S.FRASE_REVISION])[0], 0)
        self.assertEqual(len(self.posts('revision-administrativa')), 1)

    def test_progreso_perdido_con_cancelacion_existente_no_repite_la_revision(self):
        self.sembrar()
        for f in Path(self.dir).glob('sembrado_demo_progreso_*.json'):
            f.unlink()
        self.nuevo_ciclo()
        codigo, _, error = self.correr('--aplicar')
        self.assertEqual(codigo, 1)                                                # sin historial no hay forma de saber si la revisión se registró
        self.assertEqual(self.posts('revision-administrativa'), [])
        self.assertEqual(self.posts('comunicacion-politica'), [])
        self.assertEqual(self.contar_estado(), [3, 6, 3, 3, 2, 2])


class DatosAmbiguos(BaseSiembra):
    def setUp(self):
        super().setUp()
        self.crear_coordinador()

    def coordinador(self):
        return Api(self.app).entrar('coordinador')

    def evento(self, lugar='[DEMO] Salón Jardín Nova', cliente='CL-DEMO-01'):
        e = S.EVENTOS[0]
        r = self.coordinador().post('/eventos', {'cliente_id': cliente, 'servicios': list(e.servicios),
                                                 'datos': {'tipo': e.tipo, 'fecha_hora': e.fecha_hora, 'lugar': lugar, 'invitados_aproximados': e.invitados}})
        self.assertEqual(r.status_code, 201, r.text)

    def test_evento_con_datos_distintos_detiene(self):
        self.evento(lugar='Otro lugar')
        codigo, _, error = self.correr('--aplicar')
        self.assertEqual(codigo, 1)
        self.assertIn('datos distintos', error)
        self.assertEqual([r for r in self.posts('/eventos') if r[2] == '/eventos'], [])
        self.assertEqual(self.contar('evento'), 1)

    def test_varios_eventos_del_mismo_cliente_detienen(self):
        self.evento()
        self.evento()
        codigo, _, error = self.correr('--aplicar')
        self.assertEqual(codigo, 1)
        self.assertIn('ambiguo', error)
        self.assertEqual(self.contar('evento'), 2)

    def test_proveedor_con_el_mismo_nombre_y_otros_servicios_detiene(self):
        r = self.coordinador().post('/proveedores', {'nombre': '[DEMO] Banquetes Nova', 'servicios': ['Música'], 'contacto': 'x'})
        self.assertEqual(r.status_code, 201)
        codigo, _, error = self.correr('--aplicar')
        self.assertEqual(codigo, 1)
        self.assertIn('otros datos', error)
        self.assertEqual(self.contar('evento'), 0)

    def test_cuenta_existente_con_otro_rol_detiene(self):
        self.cont.servicios.seguridad.crear_usuario(S.CORREO_PROVEEDOR, 'Otra persona', 'administrador', CLAVES['proveedor'])
        codigo, _, error = self.correr('--aplicar')
        self.assertEqual(codigo, 1)
        self.assertIn('difieren', error)


class PermisosYProveedor(BaseSiembra):
    def plantilla(self, metodo, ruta):
        for (m, plantilla) in MATRIZ:
            if m == metodo and re.fullmatch(re.sub(r'\{[^}]+\}', '[^/]+', plantilla), ruta):
                return plantilla
        return None

    def test_cada_peticion_la_hace_el_rol_autorizado_por_la_matriz(self):
        self.sembrar()
        negocio = [r for r in self.registro if r[0] != 'publico' and r[2] != '/auth/inicio-sesion']
        self.assertGreater(len(negocio), 60)
        for rol, metodo, ruta, estado in negocio:
            plantilla = self.plantilla(metodo, ruta)
            self.assertIsNotNone(plantilla, (metodo, ruta))
            self.assertTrue(autoriza(rol, metodo, plantilla), f'{rol} no está autorizado para {metodo} {plantilla}')
            self.assertIn(estado, (200, 201), (rol, metodo, ruta))
        roles = {(r[0], r[1], self.plantilla(r[1], r[2])) for r in negocio}
        self.assertIn(('administrador', 'POST', '/estados-cuenta/{estado_cuenta_id}/pagos'), roles)         # el pago lo registra Administración
        self.assertIn(('coordinador', 'POST', '/eventos'), roles)
        self.assertNotIn(('administrador', 'POST', '/eventos'), roles)

    def test_los_roles_no_autorizados_son_rechazados(self):
        self.sembrar()
        ev = self.eventos()['CL-DEMO-02']
        servicio = next(s for s in self.admin(ev['eventoId'])['proveedores'] if s['servicio'] == 'Banquete')
        adm, coord, prov = (Api(self.app).entrar(r) for r in ('administrador', 'coordinador', 'proveedor'))
        cuerpo_evento = {'cliente_id': 'CL-X', 'servicios': ['Banquete'], 'datos': {'tipo': 't', 'fecha_hora': '2027-06-01T18:00:00', 'lugar': 'l', 'invitados_aproximados': 5}}
        self.assertEqual(adm.post('/eventos', cuerpo_evento).status_code, 403)                          # el administrador no registra eventos
        self.assertEqual(coord.post('/usuarios', {'correo': 'x@eventosnova.example', 'nombre': 'x', 'rol': 'coordinador', 'contrasena': 'una-clave-larga-1'}).status_code, 403)
        self.assertEqual(prov.get('/usuarios').status_code, 403)
        self.assertEqual(prov.post('/proveedores', {'nombre': 'Intruso', 'servicios': [], 'contacto': ''}).status_code, 403)
        otro = self.admin(ev['eventoId'])['proveedores'][0]
        ajeno = prov.post(f"/eventos/{ev['eventoId']}/servicios/{servicio['servicioContratadoId']}/respuesta-proveedor",
                          {'proveedor_id': 'PV-AJENO', 'disponible': True})
        self.assertEqual(ajeno.status_code, 403)                                                        # solo responde por su propio proveedor
        self.assertIsNotNone(otro)

    def test_la_asignacion_queda_pendiente_visible_y_se_responde_con_los_endpoints_reales(self):
        salida = self.sembrar()
        self.assertEqual(self.posts('respuesta-proveedor'), [])
        self.assertIn('pendiente por diseño', salida)
        prov = Api(self.app).entrar('proveedor')
        asign = prov.get('/mis-asignaciones').json()['eventos']
        self.assertEqual(len(asign), 1)
        servicio = asign[0]['servicios'][0]
        self.assertEqual((asign[0]['tipoEvento'], servicio['servicio'], servicio['estado']),
                         (S.EVENTOS[1].tipo, 'Banquete', 'Pendiente de confirmación del proveedor'))
        yo = prov.get('/auth/yo').json()['datos']['usuario']['proveedorId']
        ruta = f"/eventos/{asign[0]['eventoId']}/servicios/{servicio['servicioContratadoId']}/respuesta-proveedor"
        self.assertEqual(prov.post(ruta, {'proveedor_id': yo, 'disponible': True}).status_code, 200)    # respuesta manual en la demostración
        self.assertEqual(prov.get('/mis-asignaciones').json()['eventos'][0]['servicios'][0]['estado'], 'Confirmado por el proveedor')
        self.assertEqual(prov.post(ruta, {'proveedor_id': yo, 'disponible': True}).status_code, 422)    # repetirla se rechaza
        self.nuevo_ciclo()
        self.sembrar()                                                                                  # la siembra vuelve a ejecutarse sin tocar nada

    def test_responder_como_proveedor_es_explicito_e_idempotente(self):
        self.sembrar('--responder-como-proveedor')
        self.assertEqual(len(self.posts('respuesta-proveedor')), 1)
        self.assertEqual(Api(self.app).entrar('proveedor').get('/mis-asignaciones').json()['eventos'][0]['servicios'][0]['estado'],
                         'Confirmado por el proveedor')
        self.nuevo_ciclo()
        self.sembrar('--responder-como-proveedor')
        self.assertEqual(self.posts('respuesta-proveedor'), [])


class SeguridadYDestino(BaseSiembra):
    def test_destino_valido_e_invalido(self):
        ok = S.validar_destino('http://127.0.0.1:8002', 'local')
        self.assertEqual((ok.host, ok.puerto, ok.origin), ('127.0.0.1', 8002, 'http://127.0.0.1:8002'))
        self.assertEqual(S.validar_destino('https://demo.eventosnova.example/', 'produccion').origin, 'https://demo.eventosnova.example')
        malos = [('http://localhost:8000', 'produccion'), ('https://localhost', 'produccion'), ('https://127.0.0.1', 'produccion'),
                 ('http://demo.eventosnova.example', 'produccion'), ('https://10.0.0.5', 'produccion'), ('https://servidor', 'produccion'),
                 ('https://api.interno.local', 'produccion'), ('https://203.0.113.9', 'produccion'), ('https://u:p@demo.eventosnova.example', 'produccion'),
                 ('https://demo.eventosnova.example/docs', 'produccion'), ('https://demo.eventosnova.example?x=1', 'produccion'),
                 ('https://localhost.', 'produccion'), ('https://LOCALHOST.', 'produccion'), ('https://demo.eventosnova.example.', 'produccion'),
                 ('https://demo_eventos.example', 'produccion'), ('https://-demo.example', 'produccion'), ('http://localhost.', 'local'),
                 ('https://127.0.0.1', 'local'), ('http://demo.eventosnova.example', 'local'), ('ftp://127.0.0.1', 'local'), ('', 'local'), ('http://127.0.0.1', 'otro')]
        for url, entorno in malos:
            with self.subTest(url=url, entorno=entorno):
                with self.assertRaises(S.Detener) as cm:
                    S.validar_destino(url, entorno)
                self.assertEqual(cm.exception.codigo, 2)
        for url, entorno in (('https://localhost', 'produccion'), ('http://demo.eventosnova.example', 'local')):
            self.assertEqual(self.correr(url=url, entorno=entorno)[0], 2)
        self.assertEqual(self.registro, [])                                         # ninguna petición a un destino rechazado

    def test_produccion_exige_la_confirmacion_escrita_del_dominio(self):
        codigo, _, error = self.correr('--aplicar', url=URL_PROD, entorno='produccion', entradas=['sí'])
        self.assertEqual(codigo, 2)
        self.assertIn('no se escribe nada', error)
        self.assertEqual(self.posts(), [])
        self.assertEqual(self.contar('usuario'), 1)
        self.nuevo_ciclo()
        codigo, salida, error = self.correr('--aplicar', url=URL_PROD, entorno='produccion', entradas=['SEMBRAR DEMO EN demo.eventosnova.example'])
        self.assertEqual(codigo, 0, error)
        self.assertIn('ESCRIBIR datos de demostración en demo.eventosnova.example', salida)
        self.assertEqual(self.contar('evento'), 3)
        escrituras = [(m, ruta, h) for m, ruta, h in self.llamadas if m == 'POST']
        self.assertTrue(all(h.get('Origin') == URL_PROD for _, _, h in escrituras))                       # Origin = la URL real
        self.assertTrue(all(h.get('X-CSRF-Token') for _, ruta, h in escrituras if ruta != '/auth/inicio-sesion'))
        self.assertEqual({r[3] for r in self.registro if r[1] == 'POST'}, {200, 201})

    def test_verificar_estado_en_produccion_exige_la_confirmacion_escrita(self):
        host = 'demo.eventosnova.example'
        frase = f'VERIFICAR ESTADO EN {host}'
        incorrectas = (('ausente (sin entrada)', []), ('vacía', ['']), ('incorrecta', ['sí']), ('otro dominio', ['VERIFICAR ESTADO EN otro.example']),
                       ('en minúsculas', [frase.lower()]), ('la frase de sembrar', [f'SEMBRAR DEMO EN {host}']))
        for nombre, entradas in incorrectas:
            with self.subTest(nombre):
                self.nuevo_ciclo()
                codigo, salida, error = self.correr('--verificar-estado', url=URL_PROD, entorno='produccion', entradas=entradas)
                self.assertEqual(codigo, 2)
                self.assertIn(f'inicia sesión (POST /auth/inicio-sesion) en {host} (PRODUCCIÓN)', salida)     # la advertencia se muestra antes de pedir la frase
                self.assertIn('no se inicia sesión', error)
                self.assertEqual({(m, ruta) for _, m, ruta, _ in self.registro}, {('GET', '/health'), ('GET', '/ready')})   # ni login ni GET privado
                self.assertFalse(any('contraseña' in p.lower() for p in self.prompts))                         # ni siquiera pide la contraseña
                self.assertEqual(self.contar('sesion'), 0)
        self.nuevo_ciclo()
        codigo, salida, error = self.correr('--verificar-estado', url=URL_PROD, entorno='produccion', entradas=[frase])
        self.assertEqual(codigo, 0, error)
        self.assertIn('CREA UNA SESIÓN y ACTUALIZA EL ÚLTIMO ACCESO', salida)
        self.assertEqual([r[2] for r in self.posts()], ['/auth/inicio-sesion'])                                # el único POST es el login
        self.assertEqual(self.contar('sesion'), 1)
        self.assertEqual([self.contar(t) for t in ('usuario', 'proveedor', 'evento')], [1, 0, 0])             # y no escribe datos de negocio

    def test_simular_en_produccion_no_pide_confirmacion_ni_inicia_sesion(self):
        codigo, salida, _ = self.correr('--simular', url=URL_PROD, entorno='produccion')
        self.assertEqual(codigo, 0)
        self.assertEqual(self.prompts, [])
        self.assertEqual({(m, ruta) for _, m, ruta, _ in self.registro}, {('GET', '/health'), ('GET', '/ready')})
        self.assertEqual(self.contar('sesion'), 0)
        self.assertIn('SIMULACIÓN', salida)

    def test_verificar_estado_en_local_no_pide_la_frase(self):
        codigo, _, error = self.correr('--verificar-estado')
        self.assertEqual(codigo, 0, error)
        self.assertEqual([p for p in self.prompts if 'Escriba exactamente' in p], [])

    def test_login_fallido_se_intenta_una_sola_vez(self):
        codigo, _, error = self.correr('--aplicar', claves={**CLAVES, 'administrador': 'Clave-incorrecta-123'})
        self.assertEqual(codigo, 3)
        self.assertIn('No se reintenta', error)
        self.assertEqual([r[2] for r in self.posts()], ['/auth/inicio-sesion'])
        self.assertEqual(self.contar('usuario'), 1)

    def test_cuenta_bloqueada_429_detiene_sin_reintentar(self):
        malo = Api(self.app)
        for _ in range(8):
            malo.http.post('/auth/inicio-sesion', json={'correo': CORREO_ADMIN, 'contrasena': 'incorrecta-incorrecta'})
        codigo, _, error = self.correr('--aplicar')
        self.assertEqual(codigo, 3)
        self.assertIn('bloqueada', error)
        self.assertEqual([r[2:] for r in self.posts()], [('/auth/inicio-sesion', 429)])

    def test_sin_credenciales_en_archivos_salida_ni_logs(self):
        registros = []

        class Captura(logging.Handler):
            def emit(self, record):
                registros.append(record.getMessage())
        h = Captura(level=logging.DEBUG)
        previos = []
        for nombre in ('httpx', 'httpcore', 'eventosnova', 'eventosnova.api', 'eventosnova.seguridad'):
            lg = logging.getLogger(nombre)
            previos.append((lg, lg.level, lg.propagate))
            lg.addHandler(h)
            lg.setLevel(logging.DEBUG)
            lg.propagate = False                                                    # solo para capturar: no ensucia la salida de la suite

        def restaurar():
            for lg, nivel, propaga in previos:
                lg.removeHandler(h)
                lg.setLevel(nivel)
                lg.propagate = propaga
        self.addCleanup(restaurar)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            salida = self.sembrar()
            self.nuevo_ciclo()
            self.correr('--aplicar', claves={**CLAVES, 'coordinador': 'Clave-incorrecta-xyz'})
        texto = '\n'.join([salida, out.getvalue(), err.getvalue(), '\n'.join(registros)])
        archivos = [p.read_text(encoding='utf-8') for p in Path(self.dir).iterdir()]
        self.assertTrue(archivos)
        todo = texto + '\n'.join(archivos) + json.dumps(self.registro) + '\n'.join(self.prompts)
        for secreto in list(CLAVES.values()) + ['Clave-incorrecta-xyz']:
            self.assertNotIn(secreto, todo)
        self.assertNotRegex(todo, r'(?i)csrf["\']?\s*[:=]\s*["\'][A-Za-z0-9_-]{20,}')
        self.assertNotIn('cookie', '\n'.join(archivos).lower())
        fuente = RUTA_SCRIPT.read_text(encoding='utf-8')
        self.assertNotRegex(fuente, r'os\.environ|getenv')                         # las contraseñas nunca salen del entorno
        self.assertEqual(sorted(len(r) for r in self.registro), [4] * len(self.registro))         # el registro solo guarda rol, método, ruta y estado

    def test_sin_operaciones_externas(self):
        with mock.patch.object(httpx.HTTPTransport, 'handle_request', side_effect=AssertionError('transporte real')):
            self.sembrar()
        self.assertEqual({type(self.cont.notificador).__name__}, {'NotificadorEnMemoria'})
        con_motor = self.cont.servicios
        self.assertIsNotNone(con_motor)
        visitados = []

        def manejador(peticion):
            visitados.append(peticion.url.host)
            return httpx.Response(302, headers={'Location': 'https://otro-dominio.example/robo'})
        d = S.validar_destino(URL, 'local')
        cliente = httpx.Client(base_url=d.base_url, transport=httpx.MockTransport(manejador), follow_redirects=False)
        with self.assertRaises(S.Detener) as cm:
            S.Sesion('administrador', d, cliente, []).get('/usuarios')
        self.assertEqual((cm.exception.codigo, visitados), (4, ['127.0.0.1']))
        real = S.fabrica_httpx(d)
        self.assertFalse(real.follow_redirects)
        self.assertEqual(str(real.base_url).rstrip('/'), URL)
        real.close()
        self.assertEqual({r[0] for r in self.registro}, {'publico', 'administrador', 'coordinador', 'proveedor'})


class FechasCandadoYCarpeta(BaseSiembra):
    def test_las_fechas_son_fijas_y_no_dependen_del_reloj(self):
        self.sembrar()
        self.ahora = datetime(2026, 12, 15, 9, 30, 0)
        self.nuevo_ciclo()
        self.sembrar()
        self.assertEqual([r for r in self.posts('/eventos') if r[2] == '/eventos'], [])         # los encontró: no creó ninguno
        self.assertEqual(self.contar('evento'), 3)
        fuente = RUTA_SCRIPT.read_text(encoding='utf-8')
        self.assertNotIn('timedelta', fuente)
        self.assertEqual([e.fecha_hora for e in S.EVENTOS], ['2027-03-20T18:00:00', '2027-04-17T18:00:00', '2027-05-22T18:00:00'])

    def test_vencido_el_periodo_de_validez_se_niega_a_sembrar(self):
        self.ahora = datetime(2027, 3, 13, 0, 0, 0)
        for modo in ('--simular', '--verificar-estado', '--aplicar'):
            self.nuevo_ciclo()
            codigo, _, error = self.correr(modo)
            self.assertEqual(codigo, 2, modo)
            self.assertIn('ya no son válidas', error)
            self.assertEqual(self.registro, [])
        self.assertEqual(self.prompts, [])

    def test_un_candado_existente_impide_la_ejecucion_simultanea_y_no_se_borra(self):
        destino = S.validar_destino(URL, 'local')
        candado = Path(self.dir) / f'sembrado_demo_{destino.clave}.lock'
        candado.write_text('{}', encoding='utf-8')
        codigo, _, error = self.correr('--aplicar')
        self.assertEqual(codigo, 1)
        self.assertIn('candado', error)
        self.assertTrue(candado.exists())                                          # lo retira una persona, nunca el script
        self.assertEqual(self.posts(), [])
        self.assertEqual(self.prompts, [])
        candado.unlink()
        self.sembrar()
        self.assertFalse(candado.exists())                                         # y se libera al terminar

    def test_la_carpeta_del_progreso_debe_estar_ignorada_por_git(self):
        if shutil.which('git') is None or not (S.RAIZ / '.git').exists():
            self.skipTest('Git no disponible')
        S.verificar_directorio_ignorado(S.DIRECTORIO_ESTADO)                       # scratchpad/ está en .gitignore
        with self.assertRaises(S.Detener) as cm:
            S.verificar_directorio_ignorado(S.RAIZ / 'docs')
        self.assertEqual(cm.exception.codigo, 2)

    def test_un_progreso_dañado_o_de_otro_destino_detiene_sin_escribir(self):
        self.sembrar()
        ruta = next(Path(self.dir).glob('sembrado_demo_progreso_*.json'))
        original = ruta.read_text(encoding='utf-8')
        datos = json.loads(original)
        casos = {'json roto': '{"version": 1,', 'no es un objeto': '[1, 2]', 'otro destino': json.dumps({**datos, 'destino': 'otro-servidor:9'}),
                 'sin pasos': json.dumps({k: v for k, v in datos.items() if k != 'pasos'}),
                 'estado de paso desconocido': json.dumps({**datos, 'pasos': {**datos['pasos'], 'E2.politica': {'estado': 'raro'}}}),
                 'ids mal formados': json.dumps({**datos, 'ids': {'eventos': 'texto'}})}
        for nombre, contenido in casos.items():
            with self.subTest(nombre):
                ruta.write_text(contenido, encoding='utf-8')
                self.nuevo_ciclo()
                for modo in ('--simular', '--aplicar'):
                    codigo, _, error = self.correr(modo)
                    self.assertEqual(codigo, 1, (modo, error))
                self.assertEqual(self.posts(), [])
                self.assertEqual(self.prompts, [])
                self.assertEqual(ruta.read_text(encoding='utf-8'), contenido)              # el script no «corrige» el progreso
        ruta.write_text(original, encoding='utf-8')

    def test_sin_terminal_interactiva_no_pide_contrasenas(self):
        salida, errores = [], []
        falso = mock.Mock()
        falso.isatty.return_value = False
        with mock.patch.object(sys, 'stdin', falso):
            codigo = S.main(['--base-url', URL, '--entorno', 'local', '--admin-correo', CORREO_ADMIN, '--verificar-estado'],
                            fabrica_http=lambda d: self.fail('no debe abrir ninguna conexión'), salida=salida.append, error=errores.append,
                            directorio_estado=Path(self.dir), ahora_fn=lambda: self.ahora)
        self.assertEqual(codigo, 2)
        self.assertIn('terminal interactiva', '\n'.join(errores))

    def test_un_error_inesperado_no_muestra_trazas_y_libera_el_candado(self):
        original, llamadas = S.Sesion.get, []

        def falla(sesion, *a, **k):
            llamadas.append(1)
            if len(llamadas) > 2:                                    # tras /health y /ready
                raise KeyError('respuesta inesperada')
            return original(sesion, *a, **k)
        with mock.patch.object(S.Sesion, 'get', falla):
            codigo, _, error = self.correr('--aplicar')
        self.assertEqual(codigo, 4)
        self.assertIn('error inesperado (KeyError)', error)
        self.assertNotIn('Traceback', error)
        self.assertEqual(list(Path(self.dir).glob('*.lock')), [])

    def test_no_usa_los_csv_oficiales(self):
        fuente = RUTA_SCRIPT.read_text(encoding='utf-8')
        self.assertNotRegex(fuente, r'paquete_pia|\.csv|ejecucion_paquete')


class ProteccionDeBasesDePruebas(unittest.TestCase):
    """No necesitan base de datos: comprueban que las pruebas que vacían tablas se detienen ante cualquier destino que no sea una base de pruebas."""
    PRUEBA = 'postgresql+psycopg://usuario:SECRETO-XYZ-123@127.0.0.1:5432/{}'

    def test_admite_las_bases_de_pruebas_del_ci_y_las_propias(self):
        for base in ('eventosnova_test', 'eventosnova_demo_ensayo_test', 'eventosnova_regresion_test'):
            self.assertEqual(exigir_base_de_pruebas(self.PRUEBA.format(base)), base)
        self.assertEqual(exigir_base_de_pruebas('postgresql://u:p@db:5432/eventosnova_test'), 'eventosnova_test')       # Docker Compose

    def test_rechaza_bases_protegidas_y_las_que_no_cumplen_las_reglas(self):
        malas = [self.PRUEBA.format(b) for b in ('eventosnova', 'eventosnova_manual_test', 'postgres', 'eventosnova_prod', 'otra_manual_test', '')]
        malas += ['postgresql+psycopg://usuario:SECRETO-XYZ-123@db.render.com:5432/eventosnova_test',          # servidor que no es local
                  'mysql://usuario:SECRETO-XYZ-123@127.0.0.1/eventosnova_test', 'basura SECRETO-XYZ-123', '', None]
        for url in malas:
            with self.subTest(url=url if not url or 'SECRETO' not in url else 'url con credenciales'):
                with self.assertRaises(AssertionError) as cm:
                    exigir_base_de_pruebas(url)
                mensaje = str(cm.exception)
                self.assertNotIn('SECRETO-XYZ-123', mensaje)
                self.assertNotIn('://', mensaje)                                         # nunca la cadena de conexión
        with mock.patch.dict(os.environ, {'EVENTOSNOVA_BASES_PROTEGIDAS': 'eventosnova_demo_ensayo_test'}):
            with self.assertRaises(AssertionError):
                exigir_base_de_pruebas(self.PRUEBA.format('eventosnova_demo_ensayo_test'))                    # las bases protegidas por configuración

    def test_sin_test_database_url_no_usa_ninguna_alternativa(self):
        desarrollo = 'postgresql+psycopg://usuario:SECRETO-XYZ-123@127.0.0.1:5432/eventosnova'
        for requiere, excepcion in (('0', unittest.SkipTest), ('1', AssertionError)):
            with mock.patch.object(C, 'url_pruebas', return_value=None), \
                    mock.patch.dict(os.environ, {'DATABASE_URL': desarrollo, 'EVENTOSNOVA_REQUIERE_BD': requiere}), \
                    mock.patch('apoyo_bd.motor_de_pruebas') as motor:
                with self.assertRaises(excepcion) as cm:
                    BaseSiembra.setUpClass()
                motor.assert_not_called()                                                # ni siquiera se intenta conectar
                self.assertNotIn('SECRETO-XYZ-123', str(cm.exception))

    def test_un_destino_protegido_se_detiene_antes_de_conectar_o_migrar(self):
        for base in ('eventosnova', 'eventosnova_manual_test'):
            with mock.patch.object(C, 'url_pruebas', return_value=self.PRUEBA.format(base)), \
                    mock.patch('apoyo_bd.motor_de_pruebas') as motor, mock.patch('apoyo_bd.asegurar_base_de_pruebas') as asegurar:
                with self.assertRaises(AssertionError) as cm:
                    BaseSiembra.setUpClass()
                motor.assert_not_called()
                asegurar.assert_not_called()
                self.assertNotIn('SECRETO-XYZ-123', str(cm.exception))

    def test_la_conexion_abierta_debe_ser_la_base_validada(self):
        motor = mock.MagicMock()
        motor.connect.return_value.__enter__.return_value.execute.return_value.scalar.return_value = 'eventosnova_manual_test'
        try:
            with mock.patch.object(C, 'url_pruebas', return_value=self.PRUEBA.format('eventosnova_test')), \
                    mock.patch('apoyo_bd.motor_de_pruebas', return_value=motor):
                with self.assertRaises(AssertionError) as cm:
                    BaseSiembra.setUpClass()
        finally:
            if 'motor' in BaseSiembra.__dict__:                       # no deja el motor simulado en la clase base
                del BaseSiembra.motor
        self.assertIn('no a la base validada', str(cm.exception))
        self.assertNotIn('SECRETO-XYZ-123', str(cm.exception))


if __name__ == '__main__':
    unittest.main()
