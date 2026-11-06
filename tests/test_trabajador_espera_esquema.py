"""Arranque del trabajador del Outbox cuando la base todavía no está lista (primer despliegue en una plataforma como Render).

El trabajador NO migra: con `--espera-esquema` solo reintenta, con límite de tiempo y registros claros, mientras la base no responda o no tenga la revisión
de Alembic que el código necesita; las migraciones las aplica únicamente el `preDeployCommand` de la API. Las pruebas de la espera no necesitan base de datos
(reloj y espera simulados); la última clase usa la base DESECHABLE `eventosnova_migraciones_test` (la misma de `test_migraciones_ciclo`) y la devuelve a la
última revisión al terminar.
Ejecutar desde la raíz:  python -m unittest tests.test_trabajador_espera_esquema -v"""
import os
import re
import sys
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
from apoyo_bd import motor_de_pruebas  # noqa: E402

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

    def test_la_linea_de_comandos_por_omision_no_espera(self):
        with mock.patch.object(T, 'construir_persistente', side_effect=EsquemaDesactualizado('desactualizada')) as construir:
            with self.assertRaises(EsquemaDesactualizado):
                T.main(['--una-vez'])
        self.assertEqual(construir.call_count, 1)


class EsperaContraUnaBaseRealMigrandoDespues(unittest.TestCase):
    """Con PostgreSQL: el trabajador espera mientras la base está en la 0008 y arranca cuando OTRO proceso aplica la 0009; él no migra."""
    @classmethod
    def setUpClass(cls):
        motor_de_pruebas()                                                                    # omite si PostgreSQL no está disponible
        cls.url = C.url_con_base(C.url_pruebas(), 'eventosnova_migraciones_test')
        asegurar_base_de_pruebas(cls.url)
        if not C.es_base_local_de_pruebas(cls.url) or C.descripcion_segura(cls.url)['base'] == C.descripcion_segura(C.url_pruebas())['base']:
            raise AssertionError('Esta prueba solo puede usar la base desechable de migraciones.')

    def setUp(self):
        aplicar_migraciones(self.url)
        revertir_migraciones(self.url, '0008')
        self.addCleanup(aplicar_migraciones, self.url)                                        # deja la base desechable en la última revisión
        self.motor = construir_persistente(url=self.url, verificar_esquema=False).motor
        self.addCleanup(self.motor.dispose)

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


if __name__ == '__main__':
    unittest.main()
