"""Blueprint de Render (render.yaml): tres recursos en la misma región, planes vigentes, base privada, migraciones previas, worker real y sin secretos.

No necesita red ni PyYAML: revisa el texto del archivo (sin comentarios). La validación completa contra el esquema JSON oficial de Render se documenta en
docs/manuales/GUIA_DESPLIEGUE_RENDER.md (sección 2).
Ejecutar desde la raíz:  python -m unittest tests.test_render_blueprint -v"""
import os
import re
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def leer(ruta):
    with open(os.path.join(RAIZ, ruta), encoding='utf-8') as f:
        return f.read()


def sin_comentarios(texto):
    return '\n'.join(re.sub(r'\s+#.*$', '', linea).rstrip() for linea in texto.splitlines() if not linea.lstrip().startswith('#'))


def bloques(texto, patron):
    """Divide `texto` en bloques que empiezan en cada línea que cumple `patron`."""
    posiciones = [m.start() for m in re.finditer(patron, texto, re.M)]
    return [texto[a:b] for a, b in zip(posiciones, posiciones[1:] + [len(texto)])]


class BlueprintDeRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texto = sin_comentarios(leer('render.yaml'))
        base, _, servicios = cls.texto.partition('\nservices:')
        cls.base = base
        cls.servicios = {re.search(r'name: (\S+)', b).group(1): b for b in bloques(servicios, r'^  - type:')}

    def test_son_exactamente_los_tres_recursos_previstos(self):
        self.assertEqual(re.findall(r'^  - name: (\S+)', self.base, re.M), ['eventosnova-db'])
        self.assertEqual(sorted(self.servicios), ['eventosnova-api', 'eventosnova-worker'])
        self.assertIn('type: web', self.servicios['eventosnova-api'])
        self.assertIn('type: worker', self.servicios['eventosnova-worker'])
        self.assertEqual(self.texto.count('runtime: docker'), 2)

    def test_los_tres_recursos_estan_en_ohio(self):
        self.assertEqual(re.findall(r'^\s+region: (\S+)', self.texto, re.M), ['ohio', 'ohio', 'ohio'])

    def test_planes_con_identificadores_vigentes_y_de_pago(self):
        self.assertEqual(re.findall(r'^\s+plan: (\S+)', self.texto, re.M), ['0.1c-256mb', '0.5c-512mb', '0.5c-512mb'])
        self.assertNotRegex(self.texto, r'plan: (free|starter|basic-)')                            # ni gratuitos ni nombres heredados

    def test_la_base_es_privada_persistente_y_de_la_misma_version_que_el_ci(self):
        self.assertRegex(self.base, r'postgresMajorVersion: "18"')
        self.assertIn('image: postgres:18', leer('docker-compose.yml'))
        self.assertRegex(self.base, r'ipAllowList: \[\]')                                          # sin conexiones externas
        self.assertRegex(self.base, r'diskSizeGB: 1\b')
        self.assertRegex(self.base, r'storageAutoscalingEnabled: false')
        self.assertNotRegex(self.base, r'plan: free')

    def test_la_api_migra_antes_de_arrancar_y_usa_el_health_check_de_la_base(self):
        api = self.servicios['eventosnova-api']
        self.assertRegex(api, r'healthCheckPath: /ready\b')
        self.assertRegex(api, r'preDeployCommand: python -m alembic upgrade head\b')
        self.assertEqual(self.texto.count('preDeployCommand'), 1)                                  # solo la API migra (evita carreras entre servicios)
        self.assertNotIn('dockerCommand', api)                                                     # usa el CMD de la etapa final del Dockerfile
        self.assertEqual(self.texto.count('autoDeployTrigger: checksPass'), 2)

    def test_el_worker_ejecuta_el_proceso_real_del_proyecto(self):
        worker = self.servicios['eventosnova-worker']
        modulo = re.search(r'dockerCommand: python -m (\S+)', worker).group(1)
        self.assertEqual(modulo, 'infrastructure.persistencia.trabajador_outbox')
        fuente = leer('src/' + modulo.replace('.', '/') + '.py')
        self.assertIn('def main', fuente)
        self.assertIn('--intervalo', fuente)
        self.assertNotIn('preDeployCommand', worker)
        self.assertNotIn('healthCheckPath', worker)                                                # un worker no tiene health check HTTP

    def test_las_variables_estan_vinculadas_y_sin_valores_peligrosos(self):
        for nombre, servicio in self.servicios.items():
            with self.subTest(nombre):
                self.assertRegex(servicio, r'key: DATABASE_URL\s+fromDatabase: \{ name: eventosnova-db, property: connectionString \}')
                self.assertRegex(servicio, r'key: EVENTOSNOVA_PERSISTENCIA\s+value: postgresql\b')
                self.assertRegex(servicio, r'key: EVENTOSNOVA_ENTORNO\s+value: produccion\b')
        self.assertRegex(self.servicios['eventosnova-api'], r'key: FORWARDED_ALLOW_IPS\s+value: "\*"')   # imprescindible detrás del proxy TLS de Render
        self.assertNotIn('FORWARDED_ALLOW_IPS', self.servicios['eventosnova-worker'])
        for prohibida in ('EVENTOSNOVA_DOCS', 'EVENTOSNOVA_AUTENTICACION', 'EVENTOSNOVA_COOKIE_SEGURA', 'EVENTOSNOVA_DISPONIBILIDAD_ARCHIVO', 'TEST_DATABASE_URL'):
            self.assertNotIn(prohibida, self.texto, prohibida)                                      # Swagger se activa a mano; nunca se debilita la seguridad

    def test_no_contiene_secretos_ni_cadenas_de_conexion(self):
        completo = leer('render.yaml')
        self.assertNotRegex(completo, r'(?i)postgres(ql)?(\+psycopg)?://\S*:\S+@')
        self.assertNotRegex(completo, r'(?i)(password|passwd|secret|token|api[_-]?key)\s*:\s*\S')
        self.assertNotRegex(completo, r'(ghp_|gho_|BEGIN (RSA|PRIVATE))')
        valores = set(re.findall(r'^\s+value: (.+)$', self.texto, re.M))
        self.assertEqual(valores, {'postgresql', 'produccion', '"*"'})

    def test_el_dockerfile_construye_por_omision_la_api_y_escucha_en_el_puerto_de_render(self):
        docker = leer('Dockerfile')
        etapas = re.findall(r'^FROM .+ AS (\w+)\s*$', docker, re.M)
        self.assertEqual(etapas[-1], 'runtime')                                                     # Render construye la última etapa
        self.assertRegex(docker, r'--host 0\.0\.0\.0 --port \$\{PORT:-8000\}')
        self.assertIn('USER eventosnova', docker)
        self.assertIn('COPY migraciones', docker)
        self.assertIn('COPY alembic.ini', docker)                                                   # el preDeployCommand los necesita en la imagen

    def test_las_migraciones_tienen_una_sola_cabeza(self):
        carpeta = os.path.join(RAIZ, 'migraciones', 'versions')
        revisiones, anteriores = set(), set()
        for archivo in os.listdir(carpeta):
            if archivo.endswith('.py') and archivo[:4].isdigit():
                fuente = leer(os.path.join('migraciones', 'versions', archivo))
                revisiones.add(re.search(r'^revision\s*=\s*["\'](\w+)["\']', fuente, re.M).group(1))
                previa = re.search(r'^down_revision\s*=\s*(None|["\'](\w+)["\'])', fuente, re.M)
                if previa and previa.group(2):
                    anteriores.add(previa.group(2))
        self.assertEqual(len(revisiones - anteriores), 1, 'Alembic debe tener una sola cabeza: el preDeployCommand falla con varias')


if __name__ == '__main__':
    unittest.main()
