"""Formulario «Crear cuenta» de la interfaz web: el campo «Proveedor al que pertenece» solo aplica al rol Proveedor.

Defecto que se corrigió: el CSS `.campo { display: flex }` anulaba el atributo `hidden`, así que el campo (y su proveedor preseleccionado) se veía
también con Coordinación o Administración. Además el selector obligatorio no tenía opción vacía y elegía solo el primer proveedor, y el valor
no se reiniciaba al cambiar de rol.

1. Estático: reglas de CSS y definición del formulario (se ejecutan siempre, sin navegador).
2. Navegador real (Chrome por DevTools, API en memoria sin base de datos; no crea cuentas): scripts/probar_formulario_cuentas_navegador.mjs.
   Es opcional: se ejecuta con EVENTOSNOVA_PRUEBAS_NAVEGADOR=1 y se omite si no hay Node o Chrome.
La validación del backend (solo el rol proveedor admite proveedor_id) está en tests/test_seguridad.py.
Ejecutar desde la raíz:  python -m unittest tests.test_interfaz_formulario_cuentas -v"""
import os, re, shutil, subprocess, sys, unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB = os.path.join(RAIZ, 'src', 'web')


def _leer(*partes):
    with open(os.path.join(WEB, *partes), encoding='utf-8') as f:
        return f.read()


CSS = re.sub(r'/\*.*?\*/', '', _leer('css', 'app.css'), flags=re.S)
ACCIONES = _leer('js', 'acciones.js')
UI = _leer('js', 'ui.js')


def _definicion_crear_cuenta():
    inicio = ACCIONES.index('ACCIONES.crearCuenta = {')
    return ACCIONES[inicio:ACCIONES.index('ACCIONES.desactivarCuenta', inicio)]


def _campo(definicion, nombre):
    m = re.search(r"f\('" + nombre + r"',[^\n]*(?:\n[^\n]*?)*?\)(?:,|\])", definicion)
    return m.group(0) if m else ''


class OcultarCamposDelFormulario(unittest.TestCase):
    def test_el_atributo_hidden_siempre_oculta(self):
        self.assertRegex(CSS, r'(?m)^\[hidden\]\s*\{[^}]*display\s*:\s*none\s*!important')

    def test_ninguna_regla_de_campo_puede_mostrar_lo_oculto_por_el_motor_de_formularios(self):
        """El motor oculta con `fila.hidden`; la regla global anterior debe preceder o igualar a cualquier `display` de `.campo`."""
        self.assertLess(CSS.index('[hidden]'), CSS.index('.campo {'))

    def test_el_motor_reinicia_los_campos_marcados_cuando_dejan_de_aplicar(self):
        bloque = UI[UI.index('function actualizarVisibilidad'):]
        bloque = bloque[:bloque.index('\n    }\n') + 7]
        self.assertIn('c.reiniciarAlOcultar', bloque)
        self.assertRegex(bloque, r"ctl\.value\s*=\s*''")


class FormularioCrearCuenta(unittest.TestCase):
    def setUp(self):
        self.definicion = _definicion_crear_cuenta()
        self.campo = _campo(self.definicion, 'proveedor_id')

    def test_el_campo_proveedor_existe_y_solo_es_visible_con_el_rol_proveedor(self):
        self.assertNotEqual(self.campo, '', 'no se encontró el campo proveedor_id')
        self.assertRegex(self.campo, r"visibleSi:\s*\(v\)\s*=>\s*v\.rol\s*===\s*'proveedor'")

    def test_para_el_rol_proveedor_es_obligatorio_y_exige_elegir_sin_preseleccion(self):
        self.assertIn('requerido: true', self.campo)
        self.assertIn("vacio: 'Selecciona un proveedor'", self.campo)      # sin opción vacía el navegador elegía el primer proveedor

    def test_al_ocultarse_el_campo_pierde_su_valor(self):
        self.assertIn('reiniciarAlOcultar: true', self.campo)

    def test_los_roles_ofrecidos_son_solo_los_de_las_cuentas(self):
        opciones = re.findall(r"valor: '([a-z]+)', texto: '([^']+)'", self.definicion.split("f('proveedor_id'")[0])
        self.assertEqual(sorted(v for v, _ in opciones), ['administrador', 'coordinador', 'proveedor'])   # el Cliente no tiene cuenta

    def test_la_carga_util_solo_lleva_proveedor_para_el_rol_proveedor(self):
        self.assertRegex(self.definicion, r"\.\.\.\(v\.rol === 'proveedor' \? \{ proveedor_id: v\.proveedor_id \} : \{\}\)")


NODE = shutil.which('node')
CHROME = next((p for p in (os.environ.get('CHROME_PATH'), 'C:/Program Files/Google/Chrome/Application/chrome.exe',
                           shutil.which('google-chrome'), shutil.which('chromium')) if p and os.path.exists(p)), None)


@unittest.skipUnless(os.environ.get('EVENTOSNOVA_PRUEBAS_NAVEGADOR') == '1', 'Prueba con navegador: defina EVENTOSNOVA_PRUEBAS_NAVEGADOR=1')
@unittest.skipUnless(NODE and CHROME, 'Hace falta Node.js y Google Chrome')
class FormularioCrearCuentaEnNavegador(unittest.TestCase):
    def test_visibilidad_obligatoriedad_valor_y_carga_util_segun_el_rol(self):
        r = subprocess.run([NODE, os.path.join(RAIZ, 'scripts', 'probar_formulario_cuentas_navegador.mjs'), RAIZ, sys.executable],
                           capture_output=True, text=True, encoding='utf-8', timeout=180)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main()
