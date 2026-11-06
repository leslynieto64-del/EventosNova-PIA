"""Arranque del trabajador del Outbox cuando la base todavía no está lista (primer despliegue en una plataforma como Render).

El trabajador NO migra: con `--espera-esquema` solo reintenta, con límite de tiempo y registros claros, mientras la base no responda o no tenga la revisión
de Alembic que el código necesita; las migraciones las aplica únicamente el `preDeployCommand` de la API. Las pruebas de la espera no necesitan base de datos
(reloj y espera simulados, sin ninguna conexión: se bloquea `create_engine` y `DATABASE_URL` apunta a una base protegida para demostrar que no se usa); la
clase con PostgreSQL usa la base DESECHABLE `eventosnova_migraciones_test` (la misma de `test_migraciones_ciclo`) y la devuelve a la última revisión al terminar.
Esa clase exige `TEST_DATABASE_URL` explícita (nunca usa `DATABASE_URL`), valida el nombre de la base ANTES de conectar, rechaza las bases protegidas y comprueba
con `current_database()` que la conexión abierta es la validada.
Ejecutar desde la raíz:  python -m unittest tests.test_trabajador_espera_esquema -v"""
import os
import re
import sys
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

import sqlalchemy as sa

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
from infrastructure.persistencia import configuracion as C  # noqa: E402
from infrastructure.persistencia import trabajador_outbox as T  # noqa: E402
from infrastructure.persistencia.composicion_persistente import construir_persistente  # noqa: E402
from infrastructure.persistencia.errores import (  # noqa: E402
    ErrorDeConexion,
    ErrorDePersistencia,
    EsquemaDesactualizado,
)
from infrastructure.persistencia.preparacion import (  # noqa: E402
    aplicar_migraciones,
    asegurar_base_de_pruebas,
    revertir_migraciones,
    revision_actual,
)

SENTINELA = SimpleNamespace(nombre='contenedor')
BASES_PROHIBIDAS = ('eventosnova', 'eventosnova_manual_test')
BASE_DESECHABLE = 'eventosnova_migraciones_test'
URL_DE_DESARROLLO_FALSA = 'postgresql+psycopg://usuario:SECRETO-XYZ-123@127.0.0.1:5432/eventosnova'


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
        raise AssertionError(f'La base «{base}» está protegida: estas pruebas no pueden usarla.')
    if not C.es_base_local_de_pruebas(normalizada):
        raise AssertionError(f'La base «{base}» no cumple las reglas de seguridad del proyecto (servidor local, nombre terminado en «_test» y sin «manual»).')
    return base


class Reloj:
    """Reloj y 'detener' simulados: esperar avanza el tiempo sin dormir."""
    def __init__(self, detenido_en=None):
        self.t, self.esperas, self.detenido_en = 0.0, [], detenido_en

    def __call__(self):
        return self.t

    def wait(self, segundos):
        self.esperas.append(segundos)
        self.t += segundos
        return self.detenido_en is not None and len(self.esperas) >= self.detenido_en


def falla_n_veces(n, error):
    llamadas = []

    def construir():
        llamadas.append(1)
        if len(llamadas) <= n:
            raise error
        return SENTINELA
    construir.llamadas = llamadas
    return construir


class EsperaDelEsquema(unittest.TestCase):
    def setUp(self):
        """Estas pruebas no pueden tocar ninguna base: `DATABASE_URL` apunta a una base protegida y cualquier intento de crear un motor o de construir el
        contenedor real falla. Las pruebas que necesitan un contenedor lo sustituyen de forma explícita."""
        for parche in (mock.patch.dict(os.environ, {'DATABASE_URL': URL_DE_DESARROLLO_FALSA}),
                       mock.patch('sqlalchemy.create_engine', side_effect=AssertionError('las pruebas unitarias no deben conectar con ninguna base')),
                       mock.patch.object(T, 'construir_persistente', side_effect=AssertionError('contenedor real no permitido en pruebas unitarias'))):
            parche.start()
            self.addCleanup(parche.stop)

    def esperar(self, construir, espera_max=60.0, intervalo=5.0, reloj=None):
        reloj = reloj or Reloj()
        return T.construir_esperando_esquema(espera_max, intervalo, reloj, construir=construir, reloj=reloj), reloj

    def test_espera_a_que_la_base_alcance_la_revision_y_entonces_arranca(self):
        construir = falla_n_veces(3, EsquemaDesactualizado('La base de datos está en la revisión «ninguna» y se necesita «0009».'))
        with self.assertLogs('eventosnova.trabajador', level='INFO') as registros:
            contenedor, reloj = self.esperar(construir)
        self.assertIs(contenedor, SENTINELA)
        self.assertEqual(len(construir.llamadas), 4)
        self.assertEqual(reloj.esperas, [5.0, 5.0, 5.0])
        texto = '\n'.join(registros.output)
        self.assertIn('Esperando a que la base de datos esté lista (EsquemaDesactualizado)', texto)
        self.assertIn('«ninguna» y se necesita «0009»', texto)
        self.assertIn('no ejecuta migraciones', texto)
        self.assertIn('La base de datos está lista tras 15 s (4 intentos)', texto)
        self.assertEqual(len([r for r in registros.output if 'WARNING' in r]), 1)             # un aviso al principio: no inunda el log

    def test_tambien_espera_si_la_base_todavia_no_responde(self):
        construir = falla_n_veces(2, ErrorDeConexion('No se pudo conectar con la base de datos: connection refused'))
        with self.assertLogs('eventosnova.trabajador', level='INFO') as registros:
            contenedor, _ = self.esperar(construir)
        self.assertIs(contenedor, SENTINELA)
        self.assertIn('ErrorDeConexion', '\n'.join(registros.output))

    def test_el_aviso_se_repite_cada_treinta_segundos_aproximadamente(self):
        construir = falla_n_veces(13, EsquemaDesactualizado('desactualizada'))
        with self.assertLogs('eventosnova.trabajador', level='INFO') as registros:
            self.esperar(construir, espera_max=300.0)
        self.assertEqual(len([r for r in registros.output if 'WARNING' in r]), 3)             # intentos 1, 6 y 12

    def test_al_vencer_el_plazo_registra_el_motivo_y_falla_sin_pasarse_del_limite(self):
        error = EsquemaDesactualizado('La base de datos está en la revisión «0008» y se necesita «0009».')
        construir = falla_n_veces(10 ** 6, error)
        reloj = Reloj()
        with self.assertLogs('eventosnova.trabajador', level='INFO') as registros:
            with self.assertRaises(EsquemaDesactualizado) as cm:
                T.construir_esperando_esquema(30.0, 5.0, reloj, construir=construir, reloj=reloj)
        self.assertIs(cm.exception, error)
        self.assertLessEqual(reloj.t, 30.0)
        self.assertEqual(sum(reloj.esperas), 30.0)
        self.assertEqual(len(construir.llamadas), 7)
        self.assertIn('no estuvo lista en 30 s (7 intentos)', '\n'.join(registros.output))
        self.assertIn('«0008» y se necesita «0009»', '\n'.join(registros.output))

    def test_sin_espera_hace_un_solo_intento_como_antes(self):
        construir = falla_n_veces(5, EsquemaDesactualizado('desactualizada'))
        reloj = Reloj()
        with self.assertRaises(EsquemaDesactualizado):
            T.construir_esperando_esquema(0.0, 5.0, reloj, construir=construir, reloj=reloj)
        self.assertEqual((len(construir.llamadas), reloj.esperas), (1, []))

    def test_un_error_de_configuracion_no_espera(self):
        construir = falla_n_veces(5, ErrorDePersistencia('Defina DATABASE_URL (vea .env.example) para usar la persistencia en PostgreSQL.'))
        reloj = Reloj()
        with self.assertRaises(ErrorDePersistencia):
            T.construir_esperando_esquema(600.0, 5.0, reloj, construir=construir, reloj=reloj)
        self.assertEqual((len(construir.llamadas), reloj.esperas), (1, []))

    def test_si_se_pide_detener_mientras_espera_termina_sin_error(self):
        construir = falla_n_veces(10 ** 6, EsquemaDesactualizado('desactualizada'))
        reloj = Reloj(detenido_en=2)
        with self.assertLogs('eventosnova.trabajador', level='INFO') as registros:
            resultado = T.construir_esperando_esquema(600.0, 5.0, reloj, construir=construir, reloj=reloj)
        self.assertIsNone(resultado)
        self.assertEqual(len(construir.llamadas), 2)
        self.assertIn('Detenido mientras esperaba', '\n'.join(registros.output))

    def test_nunca_ejecuta_migraciones(self):
        construir = falla_n_veces(2, EsquemaDesactualizado('desactualizada'))
        with mock.patch('infrastructure.persistencia.preparacion.aplicar_migraciones', side_effect=AssertionError('no debe migrar')), \
                mock.patch('alembic.command.upgrade', side_effect=AssertionError('no debe migrar')):
            self.esperar(construir)
        with open(T.__file__, encoding='utf-8') as f:
            fuente = f.read()
        self.assertNotRegex(fuente, r'aplicar_migraciones|command\.upgrade|alembic upgrade(?! head\b)')
        self.assertEqual(len(re.findall(r'preDeployCommand', fuente)), 1)                    # solo se menciona quién migra

    def test_la_linea_de_comandos_espera_y_luego_procesa(self):
        contenedor = mock.MagicMock()                                                          # contenedor simulado: solo importa que se construya y se cierre
        contenedor.despachador.despachar.return_value = 0
        construir = falla_n_veces(2, EsquemaDesactualizado('desactualizada'))
        construir.resultado = contenedor

        def fabrica():
            construir()
            return contenedor
        with mock.patch.object(T, 'construir_persistente', fabrica), mock.patch.object(T, 'INTERVALO_ESPERA_S', 0.01):
            self.assertEqual(T.main(['--una-vez', '--espera-esquema', '5']), 0)
        self.assertEqual(len(construir.llamadas), 3)
        contenedor.cerrar.assert_called_once()

    def test_el_contenedor_real_se_resuelve_al_llamar_y_nunca_con_database_url(self):
        """Regresión: `construir` ya no se fija al definir la función; así `T.construir_persistente` es sustituible y una prueba no llega por accidente a la base
        de desarrollo (antes `main(['--una-vez'])` consultó `DATABASE_URL`)."""
        import inspect
        self.assertIsNone(inspect.signature(T.construir_esperando_esquema).parameters['construir'].default)
        with mock.patch.object(T, 'construir_persistente', return_value=SENTINELA) as fabrica:
            self.assertIs(T.construir_esperando_esquema(0.0, 5.0, threading.Event()), SENTINELA)
        fabrica.assert_called_once_with()                                                    # sin URL: la fábrica real es la que lee la configuración
        self.assertEqual(os.environ['DATABASE_URL'], URL_DE_DESARROLLO_FALSA)                 # y aquí ni siquiera se consultó

    def test_sin_sustituir_el_contenedor_una_prueba_unitaria_falla_antes_de_conectar(self):
        with self.assertRaises(AssertionError) as cm:
            T.main(['--una-vez'])
        self.assertIn('contenedor real no permitido', str(cm.exception))
        self.assertNotIn('SECRETO', str(cm.exception))

    def test_la_linea_de_comandos_por_omision_no_espera(self):
        with mock.patch.object(T, 'construir_persistente', side_effect=EsquemaDesactualizado('desactualizada')) as construir:
            with self.assertRaises(EsquemaDesactualizado):
                T.main(['--una-vez'])
        self.assertEqual(construir.call_count, 1)


class EsperaContraUnaBaseRealMigrandoDespues(unittest.TestCase):
    """Con PostgreSQL: el trabajador espera mientras la base está en la 0008 y arranca cuando OTRO proceso aplica la 0009; él no migra."""
    @classmethod
    def setUpClass(cls):
        url_pruebas = C.url_pruebas()                                                         # TEST_DATABASE_URL (entorno o .env); jamás DATABASE_URL
        if not url_pruebas:
            if os.environ.get('EVENTOSNOVA_REQUIERE_BD') == '1':
                raise AssertionError('TEST_DATABASE_URL es obligatoria (EVENTOSNOVA_REQUIERE_BD=1) y no está definida.')
            raise unittest.SkipTest('TEST_DATABASE_URL no está definida: esta prueba no usa ninguna otra URL como alternativa.')
        base_pruebas = exigir_base_de_pruebas(url_pruebas)                                    # 1) se valida el nombre ANTES de abrir ninguna conexión
        cls.url = C.url_con_base(url_pruebas, BASE_DESECHABLE)
        if exigir_base_de_pruebas(cls.url) != BASE_DESECHABLE or base_pruebas == BASE_DESECHABLE:
            raise AssertionError('Esta prueba solo puede usar la base desechable de migraciones, distinta de la de pruebas de integración.')
        try:
            asegurar_base_de_pruebas(cls.url)                                                 # crea la base desechable solo si no existe
            cls.motor = construir_persistente(url=cls.url, verificar_esquema=False).motor
            with cls.motor.connect() as con:
                real = con.execute(sa.text('select current_database()')).scalar()
        except AssertionError:
            raise
        except Exception as e:                                                                # servicio detenido, sin red, etc.
            if os.environ.get('EVENTOSNOVA_REQUIERE_BD') == '1':
                raise AssertionError(f'La base de pruebas es obligatoria y no está disponible: {type(e).__name__}') from None
            raise unittest.SkipTest(f'PostgreSQL de pruebas no disponible ({type(e).__name__})') from None
        if real != BASE_DESECHABLE:                                                           # 2) y la conexión abierta debe ser la validada
            cls.motor.dispose()
            raise AssertionError(f'La conexión abierta apunta a «{real}», no a la base validada «{BASE_DESECHABLE}»: se detiene la ejecución.')
        exigir_base_de_pruebas(C.url_con_base(url_pruebas, real))

    @classmethod
    def tearDownClass(cls):
        motor = cls.__dict__.get('motor')
        if motor is not None:
            motor.dispose()

    def setUp(self):
        aplicar_migraciones(self.url)
        revertir_migraciones(self.url, '0008')
        self.addCleanup(aplicar_migraciones, self.url)                                        # deja la base desechable en la última revisión
        self.motor = self.__class__.motor

    def test_sin_espera_falla_y_no_migra(self):
        with self.assertRaises(EsquemaDesactualizado) as cm:
            T.construir_esperando_esquema(0.0, 0.1, threading.Event(), construir=lambda: construir_persistente(url=self.url))
        self.assertIn('0008', str(cm.exception))
        self.assertEqual(revision_actual(self.motor), '0008')

    def test_el_plazo_vence_sin_haber_migrado(self):
        with self.assertLogs('eventosnova.trabajador', level='INFO') as registros:
            with self.assertRaises(EsquemaDesactualizado):
                T.construir_esperando_esquema(0.6, 0.2, threading.Event(), construir=lambda: construir_persistente(url=self.url))
        self.assertIn('no estuvo lista', '\n'.join(registros.output))
        self.assertEqual(revision_actual(self.motor), '0008')                                 # esperar no cambia la base

    def test_arranca_cuando_otro_proceso_aplica_la_migracion(self):
        resultado = {}

        def trabajador():
            resultado['contenedor'] = T.construir_esperando_esquema(30.0, 0.2, threading.Event(), construir=lambda: construir_persistente(url=self.url))
        hilo = threading.Thread(target=trabajador)
        with self.assertLogs('eventosnova.trabajador', level='INFO') as registros:
            hilo.start()
            hilo.join(1.0)
            self.assertTrue(hilo.is_alive(), 'el trabajador debería seguir esperando mientras la base está en la 0008')
            self.assertEqual(revision_actual(self.motor), '0008')
            aplicar_migraciones(self.url)                                                      # lo que haría el preDeployCommand de la API
            hilo.join(20.0)
        self.assertFalse(hilo.is_alive())
        contenedor = resultado['contenedor']
        self.assertEqual(revision_actual(self.motor), '0009')
        self.assertIn('está lista tras', '\n'.join(registros.output))
        contenedor.cerrar()


class ProteccionDeBasesDePruebas(unittest.TestCase):
    """No necesitan base de datos: la prueba con PostgreSQL se detiene ante cualquier destino que no sea una base de pruebas."""
    PRUEBA = 'postgresql+psycopg://usuario:SECRETO-XYZ-123@127.0.0.1:5432/{}'
    CLASE = EsperaContraUnaBaseRealMigrandoDespues

    def test_admite_las_bases_de_pruebas_del_ci_y_las_propias(self):
        for base in ('eventosnova_test', 'eventosnova_demo_ensayo_test', 'eventosnova_regresion_test', BASE_DESECHABLE):
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
        for requiere, excepcion in (('0', unittest.SkipTest), ('1', AssertionError)):
            with mock.patch.object(C, 'url_pruebas', return_value=None), \
                    mock.patch.dict(os.environ, {'DATABASE_URL': URL_DE_DESARROLLO_FALSA, 'EVENTOSNOVA_REQUIERE_BD': requiere}), \
                    mock.patch(f'{__name__}.asegurar_base_de_pruebas') as asegurar, mock.patch(f'{__name__}.construir_persistente') as construir:
                with self.assertRaises(excepcion) as cm:
                    self.CLASE.setUpClass()
                asegurar.assert_not_called()                                              # ni se intenta crear, migrar ni conectar
                construir.assert_not_called()
                self.assertNotIn('SECRETO-XYZ-123', str(cm.exception))

    def test_un_destino_protegido_se_detiene_antes_de_conectar_o_migrar(self):
        for base in ('eventosnova', 'eventosnova_manual_test'):
            with mock.patch.object(C, 'url_pruebas', return_value=self.PRUEBA.format(base)), \
                    mock.patch(f'{__name__}.asegurar_base_de_pruebas') as asegurar, mock.patch(f'{__name__}.construir_persistente') as construir:
                with self.assertRaises(AssertionError) as cm:
                    self.CLASE.setUpClass()
                asegurar.assert_not_called()
                construir.assert_not_called()
                self.assertNotIn('SECRETO-XYZ-123', str(cm.exception))

    def test_la_base_desechable_no_puede_ser_la_de_pruebas_de_integracion(self):
        with mock.patch.object(C, 'url_pruebas', return_value=self.PRUEBA.format(BASE_DESECHABLE)), \
                mock.patch(f'{__name__}.asegurar_base_de_pruebas') as asegurar:
            with self.assertRaises(AssertionError) as cm:
                self.CLASE.setUpClass()
        asegurar.assert_not_called()
        self.assertIn('distinta de la de pruebas de integración', str(cm.exception))

    def test_la_conexion_abierta_debe_ser_la_base_validada(self):
        motor = mock.MagicMock()
        motor.connect.return_value.__enter__.return_value.execute.return_value.scalar.return_value = 'eventosnova_manual_test'
        contenedor = SimpleNamespace(motor=motor)
        try:
            with mock.patch.object(C, 'url_pruebas', return_value=self.PRUEBA.format('eventosnova_test')), \
                    mock.patch(f'{__name__}.asegurar_base_de_pruebas'), mock.patch(f'{__name__}.construir_persistente', return_value=contenedor):
                with self.assertRaises(AssertionError) as cm:
                    self.CLASE.setUpClass()
        finally:
            if 'motor' in self.CLASE.__dict__:                                            # no deja el motor simulado en la clase
                del self.CLASE.motor
        self.assertIn('no a la base validada', str(cm.exception))
        self.assertNotIn('SECRETO-XYZ-123', str(cm.exception))
        motor.dispose.assert_called_once()


if __name__ == '__main__':
    unittest.main()
