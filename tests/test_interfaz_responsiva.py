"""Reglas estáticas del diseño responsivo de la interfaz (HTML5 + CSS3 sin frameworks): no se agranda con `zoom` ni con transformaciones globales, la
tarjeta de ingreso se centra y tiene un ancho razonable, los cuadros de diálogo caben en pantallas pequeñas y las tablas se adaptan.
La medición con navegador real en 320, 390, 768, 1024 y 1440 px está en scripts/probar_responsivo_navegador.mjs (necesita Chrome, la API y una cuenta de
administrador); estas comprobaciones evitan que un cambio de estilos reintroduzca los defectos conocidos sin ejecutarla.
Ejecutar desde la raíz:  python -m unittest tests.test_interfaz_responsiva -v"""
import os, re, unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB = os.path.join(RAIZ, 'src', 'web')
CSS = open(os.path.join(WEB, 'css', 'app.css'), encoding='utf-8').read()
HTML = open(os.path.join(WEB, 'index.html'), encoding='utf-8').read()


def regla(selector: str) -> str:
    """Contenido de las reglas cuyo selector es exactamente `selector` (la última gana)."""
    sin_comentarios = re.sub(r'/\*.*?\*/', '', CSS, flags=re.S)
    bloques = re.findall(r'(?:^|\})\s*' + re.escape(selector) + r'\s*\{([^}]*)\}', sin_comentarios)
    return ' '.join(bloques)


class DisenoResponsivo(unittest.TestCase):
    def test_no_se_usa_zoom_ni_escalado_global(self):
        self.assertNotRegex(CSS, r'(?i)\bzoom\s*:')
        for selector in ('html', 'body', '.app', '#contenido', '.columna'):
            self.assertNotRegex(regla(selector), r'(?i)transform\s*:\s*scale')
        for f in ('js/main.js', 'js/ui.js', 'index.html'):
            self.assertNotRegex(open(os.path.join(WEB, f), encoding='utf-8').read(), r'(?i)style\.zoom|transform\s*=\s*[\'"]scale')
        self.assertNotRegex(CSS, r'html\s*\{[^}]*font-size\s*:\s*[^};]*(vw|vh)')

    def test_la_ventana_es_adaptable(self):
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', HTML)
        for corte in ('max-width: 900px', 'max-width: 640px'):
            self.assertIn(corte, CSS)
        self.assertNotRegex(regla('html') + regla('body'), r'(?<!min-)\bheight\s*:\s*\d+px')

    def test_la_tarjeta_de_ingreso_se_centra_con_ancho_razonable_y_se_reduce_en_moviles(self):
        ingreso = regla('.ingreso')
        m = re.search(r'max-width\s*:\s*([\d.]+)rem', ingreso)
        self.assertTrue(m, 'el ingreso debe tener un ancho máximo')
        self.assertTrue(400 <= float(m.group(1)) * 16 <= 470, f'ancho máximo fuera de 400–470 px: {float(m.group(1)) * 16}')
        self.assertRegex(ingreso, r'\bwidth\s*:\s*100%')                                  # en móviles ocupa el ancho disponible sin desbordar
        contenedor = regla('body.sin-sesion #contenido')
        self.assertRegex(contenedor, r'place-items\s*:\s*center')                          # centrada, no pegada arriba (antes: «start center»)
        self.assertRegex(contenedor, r'min-height\s*:\s*100(d)?vh')
        self.assertNotRegex(contenedor, r'place-items\s*:\s*start')
        self.assertNotRegex(contenedor, r'padding-top\s*:\s*\d+vh')

    def test_los_campos_y_botones_del_ingreso_son_comodos(self):
        campo = regla('.ingreso-forma input')
        self.assertRegex(campo, r'min-height\s*:\s*(2\.[89]|3)\d*rem')                      # ≥ 44 px
        self.assertRegex(campo, r'font-size\s*:\s*1rem')                                     # 16 px: evita el zoom automático de los móviles
        self.assertRegex(regla('.ingreso-forma .btn'), r'min-height\s*:\s*3rem')

    def test_el_mensaje_de_error_no_deforma_el_formulario(self):
        self.assertRegex(regla('.ingreso-aviso'), r'min-height\s*:\s*[\d.]+rem')            # espacio reservado para el mensaje
        js = open(os.path.join(WEB, 'js', 'paginas', 'ingreso.js'), encoding='utf-8').read()
        self.assertIn("'ingreso-aviso'", js)
        self.assertNotRegex(js, r'<select|name=.rol|ing-rol')                                # sin selector de rol: el rol sale de la cuenta

    def test_los_dialogos_caben_en_pantallas_pequenas(self):
        self.assertRegex(regla('dialog.modal'), r'width\s*:\s*min\(620px,\s*calc\(100vw\s*-\s*1rem\)\)')
        self.assertRegex(regla('dialog.modal'), r'max-height\s*:\s*min\(92vh,\s*calc\(100dvh\s*-\s*1rem\)\)')
        self.assertRegex(regla('dialog.modal[open]'), r'display\s*:\s*flex')
        self.assertRegex(regla('dialog.modal > .modal-cuerpo'), r'overflow-y\s*:\s*auto')    # el cuerpo se desplaza y el pie (botones) siempre se ve

    def test_las_tablas_se_adaptan_y_los_controles_son_tactiles_en_moviles(self):
        self.assertIn('.tabla-contenedor', CSS)
        self.assertRegex(CSS, r'@media \(max-width: 640px\)[^@]*\.tabla td::before')           # tablas como tarjetas
        movil = CSS[CSS.rindex('@media (max-width: 640px)'):]
        self.assertRegex(movil, r'\.btn \{ min-height: 2\.75rem')                              # ≥ 44 px

    def test_todos_los_campos_tienen_estilo_aunque_no_declaren_type(self):
        self.assertIn('input:not([type])', CSS)                                                # p. ej. los filtros y la consulta del proveedor

    def test_el_menu_movil_tiene_fondo_cierre_y_teclado(self):
        self.assertIn('id="menu-fondo"', HTML)
        self.assertIn('id="menu-cerrar"', HTML)
        self.assertRegex(CSS, r'@media \(max-width: 900px\)[^@]*\.menu-fondo \{[^}]*position: fixed; inset: 0')
        self.assertRegex(CSS, r'body\.menu-abierto \.menu-fondo \{ opacity: 1')
        js = open(os.path.join(WEB, 'js', 'main.js'), encoding='utf-8').read()
        for requisito in ("e.key === 'Escape'", "lateral().inert", "'aria-expanded'", "getElementById('menu-fondo').addEventListener('click'", "abrirMenu(false, { devolverFoco: false })"):
            self.assertIn(requisito, js)                                                       # Escape, foco/inert, aria-expanded, clic en el fondo y cierre al navegar
        self.assertRegex(CSS, r'prefers-reduced-motion')


if __name__ == '__main__':
    unittest.main()
