"""Bloque A de cierre (COR-06, COR-16, COR-17): presentación de conceptos, tipos y estados de pago, y precarga del formulario de cambio.

Se comprueba contra los valores REALES del dominio (no contra listas copiadas), para que un concepto, tipo o estado nuevo sin etiqueta
legible haga fallar la prueba:
1. Cada `ConceptoPago`, `TipoSolicitud` y `TipoDevolucion` tiene una etiqueta legible distinta del valor interno (salvo «Anticipo»).
2. Cada `EstadoPago` tiene explicación (COR-17) y solo «Verificado» se describe como sumado a lo pagado.
3. Las pantallas muestran las etiquetas y conservan el valor interno en la lógica (comparaciones y filtros).
4. El formulario de cambio toma los datos actuales del evento de `c.evento` y no cambia lo que se envía.
La comprobación en navegador real está en scripts/probar_bloque_a_navegador.mjs.
Ejecutar desde la raíz:  python -m unittest tests.test_interfaz_bloque_a -v"""
import json, os, re, shutil, subprocess, sys, tempfile, unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB = os.path.join(RAIZ, 'src', 'web', 'js')
sys.path.insert(0, os.path.join(RAIZ, 'src'))
NODE = shutil.which('node')

from domain.valores import ConceptoPago, EstadoPago, TipoDevolucion, TipoSolicitud  # noqa: E402


def _leer(*partes):
    with open(os.path.join(WEB, *partes), encoding='utf-8') as f:
        return f.read()


@unittest.skipUnless(NODE, 'Node.js no está disponible')
class EtiquetasLegibles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        valores = {'conceptos': [c.value for c in ConceptoPago], 'tipos': [t.value for t in TipoSolicitud],
                   'devoluciones': [t.value for t in TipoDevolucion], 'pagos': [e.value for e in EstadoPago]}
        cls.tmp = tempfile.mkdtemp(prefix='enova-negocio-')
        destino = os.path.join(cls.tmp, 'negocio.mjs')                       # los .js de src/web son módulos ES sin package.json: se prueba una copia .mjs
        shutil.copy(os.path.join(WEB, 'negocio.js'), destino)
        guion = f"""
          import {{ etiquetaConcepto, etiquetaTipoSolicitud, etiquetaTipoDevolucion, AYUDA_PAGO }} from {json.dumps('file:///' + destino.replace(chr(92), '/'))};
          const v = {json.dumps(valores)};
          console.log(JSON.stringify({{
            conceptos: v.conceptos.map((x) => [x, etiquetaConcepto(x)]),
            tipos: v.tipos.map((x) => [x, etiquetaTipoSolicitud(x)]),
            devoluciones: v.devoluciones.map((x) => [x, etiquetaTipoDevolucion(x)]),
            pagos: v.pagos.map((x) => [x, AYUDA_PAGO[x] || null]),
            desconocido: [etiquetaConcepto('Otro'), etiquetaTipoSolicitud('otro'), etiquetaTipoDevolucion('otro')],
          }}));"""
        r = subprocess.run([NODE, '--input-type=module', '-e', guion], capture_output=True, text=True, encoding='utf-8')
        if r.returncode != 0:
            raise RuntimeError(r.stderr)
        cls.res = json.loads(r.stdout)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(getattr(cls, 'tmp', ''), ignore_errors=True)

    def test_cada_concepto_de_pago_tiene_etiqueta_legible(self):
        for interno, etiqueta in self.res['conceptos']:
            self.assertTrue(etiqueta, interno)
            self.assertIsNone(re.search(r'[a-z][A-Z]', etiqueta), f'«{etiqueta}» conserva el nombre interno {interno}')
            self.assertEqual(etiqueta[0], etiqueta[0].upper(), etiqueta)
        self.assertEqual(dict(self.res['conceptos'])['SaldoContratoOriginal'], 'Saldo del contrato original')
        self.assertEqual(dict(self.res['conceptos'])['CargoCambioTardio'], 'Cargo por cambio tardío')

    def test_cada_tipo_de_solicitud_y_de_devolucion_tiene_etiqueta_legible(self):
        for interno, etiqueta in self.res['tipos']:
            self.assertEqual(etiqueta[0], etiqueta[0].upper(), interno)
        for interno, etiqueta in self.res['devoluciones']:
            self.assertNotRegex(etiqueta, r'^[A-Z]{2}-\d+', interno)              # un código de regla no es un nombre para el usuario

    def test_un_valor_desconocido_se_muestra_tal_cual_en_lugar_de_ocultarse(self):
        self.assertEqual(self.res['desconocido'], ['Otro', 'otro', 'otro'])

    def test_cada_estado_de_pago_se_explica_y_solo_verificado_se_suma(self):
        ayuda = dict(self.res['pagos'])
        for estado in (e.value for e in EstadoPago):
            self.assertTrue(ayuda[estado], f'el estado de pago «{estado}» no tiene explicación')
        self.assertIn('pendiente de verificación', ayuda['Registrado'])
        self.assertIn('todavía no se suma', ayuda['Registrado'])
        self.assertIn('ya se suma', ayuda['Verificado'])


class PantallasUsanLasEtiquetas(unittest.TestCase):
    def test_las_tablas_muestran_la_etiqueta_y_la_logica_conserva_el_valor_interno(self):
        evento, otras = _leer('paginas', 'evento.js'), _leer('paginas', 'otras.js')
        for texto in ('etiquetaConcepto(p.concepto)', 'etiquetaConcepto(o.concepto)', 'etiquetaConcepto(d.concepto)', 'etiquetaTipoSolicitud(s.tipoSolicitud)'):
            self.assertIn(texto, evento)
        self.assertIn('etiquetaConcepto(x.concepto)', otras)
        self.assertIn("p.concepto === 'SaldoContratoOriginal'", evento)           # la lógica sigue usando el valor interno
        self.assertIn("accionesDeSolicitud(s.tipoSolicitud, s.estadoActual)", evento)
        self.assertIn("['cambio', 'servicio adicional', 'sustitución de proveedor']", otras)   # el filtro envía el valor interno

    def test_el_estado_de_pago_oficial_no_se_reemplaza_y_se_distingue_el_pendiente_de_verificar(self):
        evento = _leer('paginas', 'evento.js')
        self.assertIn('insignia(p.estado)', evento)                                # sigue mostrándose el estado oficial
        self.assertIn('AYUDA_PAGO[p.estado]', evento)
        self.assertIn("'Pendiente de verificación'", evento)                      # columna «Verificado» de un pago sin verificar
        self.assertIn("p.estado === 'Registrado'", evento)

    def test_el_registro_de_pago_muestra_el_concepto_legible_pero_envia_el_mismo_cuerpo(self):
        acciones = _leer('acciones.js')
        self.assertIn('etiquetaConcepto(o.concepto)', acciones)
        self.assertIn("{ obligacion_id: v.obligacion_id, importe: v.importe, fecha: v.fecha, comprobante: v.comprobante, verificar_ahora: v.verificar_ahora }", acciones)


class AdvertenciaDeExcedente(unittest.TestCase):
    """COR-07: solo advierte; no bloquea ni cambia lo que se envía (las reglas aprobadas permiten el excedente)."""
    def test_la_advertencia_se_destaca_en_un_parrafo_propio_y_solo_cuando_el_importe_supera_el_saldo(self):
        acciones, ui = _leer('acciones.js'), _leer('ui.js')
        self.assertIn("Number(v.importe) > Number(o.saldo)", acciones)
        self.assertIn(r"(excede ? `\nAtención: el importe supera el saldo pendiente", acciones)      # el salto de línea del JS, no uno real
        self.assertIn("p.startsWith('Atención:') ? { class: 'aviso-fuerte', role: 'alert' }", ui)

    def test_el_registro_del_pago_no_se_bloquea_en_el_cliente(self):
        acciones = _leer('acciones.js')
        bloque = acciones[acciones.index('registrarPago: {'):acciones.index('verificarPago: {')]
        self.assertNotIn('throw', bloque)                        # ninguna validación nueva en el formulario de pago
        self.assertNotRegex(bloque, r"Number\(v\.importe\)\s*>\s*Number\(o\.saldo\)\s*\)\s*(\{|return|throw)")


class PrecargaDelFormularioDeCambio(unittest.TestCase):
    def setUp(self):
        self.acciones = _leer('acciones.js')

    def test_los_datos_actuales_del_evento_son_el_valor_inicial(self):
        for campo, origen in (('tipo', 'e.tipoEvento'), ('fecha_hora', 'e.fechaHora'), ('lugar', 'e.lugar')):
            self.assertRegex(self.acciones, rf"f\('{campo}',[^\n]*valor: {re.escape(origen)}")
        self.assertIn("valor: e.invitadosAproximados === undefined ? undefined : String(e.invitadosAproximados)", self.acciones)
        self.assertIn('...datosPropuestos(c)', self.acciones)

    def test_los_datos_solo_se_envian_si_el_usuario_marca_que_el_cambio_los_modifica(self):
        self.assertIn("datos_propuestos: v.cambiar_datos ? { tipo: v.tipo, fecha_hora: v.fecha_hora, lugar: v.lugar, invitados_aproximados: Number(v.invitados_aproximados) } : null", self.acciones)
        self.assertIn("f('cambiar_datos'", self.acciones)
        self.assertNotRegex(self.acciones, r"f\('cambiar_datos',[^\n]*valor: true")    # por omisión no se marca: no se sobrescribe sin una acción explícita

    def test_la_pantalla_del_evento_entrega_los_datos_al_formulario(self):
        self.assertIn('evento: admin', _leer('paginas', 'evento.js'))


if __name__ == '__main__':
    unittest.main()
