"""Límites de entrada de la API: tamaño máximo del cuerpo (413) y longitudes máximas de los campos del catálogo (422).
Sin PostgreSQL: usa la composición en memoria.
Ejecutar desde la raíz:  python -m unittest tests.test_limites_peticion -v"""
import json, os, sys, unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from fastapi.testclient import TestClient                                                    # noqa: E402
from api.limites import MAXIMO_POR_OMISION, maximo_desde_entorno                             # noqa: E402
from api.main import crear_app                                                               # noqa: E402
from infrastructure.composicion import construir                                              # noqa: E402


class LimitesDeLaPeticion(unittest.TestCase):
    def setUp(self):
        self.http = TestClient(crear_app(construir))

    def test_un_cuerpo_normal_pasa_y_uno_enorme_se_rechaza_con_413_sin_tocar_datos(self):
        self.assertEqual(self.http.post('/proveedores', json={'nombre': 'Banquetes', 'servicios': ['Banquete'], 'contacto': ''}).status_code, 201)
        enorme = json.dumps({'nombre': 'X', 'servicios': [], 'contacto': 'a' * (MAXIMO_POR_OMISION + 10)})
        r = self.http.post('/proveedores', content=enorme, headers={'Content-Type': 'application/json'})
        self.assertEqual((r.status_code, r.json()['tipo']), (413, 'cuerpo_demasiado_grande'))
        self.assertEqual(len(self.http.get('/proveedores').json()['datos']['proveedores']), 1)          # el rechazo no dejó nada

    def test_un_cuerpo_por_trozos_sin_content_length_tambien_se_corta(self):
        def trozos():
            for _ in range(40):
                yield b'x' * 10_000
        r = self.http.post('/proveedores', content=trozos(), headers={'Content-Type': 'application/json'})
        self.assertEqual(r.status_code, 413)

    def test_el_maximo_se_configura_por_entorno_y_un_valor_invalido_usa_el_de_omision(self):
        with mock.patch.dict(os.environ, {'EVENTOSNOVA_TAMANO_MAXIMO_CUERPO': '2048'}):
            self.assertEqual(maximo_desde_entorno(), 2048)
        for malo in ('abc', '0', '-5'):
            with mock.patch.dict(os.environ, {'EVENTOSNOVA_TAMANO_MAXIMO_CUERPO': malo}):
                self.assertEqual(maximo_desde_entorno(), MAXIMO_POR_OMISION)

    def test_el_catalogo_limita_la_longitud_de_nombre_contacto_y_servicios(self):
        for cuerpo in ({'nombre': 'N' * 201, 'servicios': [], 'contacto': ''},
                       {'nombre': 'N', 'servicios': [], 'contacto': 'C' * 301},
                       {'nombre': 'N', 'servicios': ['S' * 101], 'contacto': ''},
                       {'nombre': 'N', 'servicios': [f'S{i}' for i in range(31)], 'contacto': ''}):
            self.assertEqual(self.http.post('/proveedores', json=cuerpo).status_code, 422, str(cuerpo)[:60])
        self.assertEqual(self.http.get('/proveedores').json()['datos']['proveedores'], [])


if __name__ == '__main__':
    unittest.main()
