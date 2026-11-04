"""Decisiones aprobadas el 01/11/2026: D-P1 (catálogo sin eliminación) y D-P3 (costos y condiciones de proveedores capturados a mano por
operación: Coordinación registra, Administración revisa y autoriza). Ver docs/ADR/ADR-010-decisiones-aprobadas-dp1-dp3.md.

Con autenticación activa y llamando directo a la API, con la composición en memoria y con PostgreSQL (base de PRUEBAS aislada).
Ejecutar desde la raíz:  python -m unittest tests.test_decisiones_dp1_dp3 -v"""
import os, sys, unittest
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
import sqlalchemy as sa                                                                      # noqa: E402
from apoyo_bd import BaseConBD                                                               # noqa: E402
from test_decisiones_dp2_s7_s8 import Apoyo, T                                                # noqa: E402
from test_seguridad import T0                                                                # noqa: E402
from application.seguridad import ADMINISTRADOR, COORDINADOR, PROVEEDOR, permisos_del_rol   # noqa: E402
from infrastructure.composicion import construir                                              # noqa: E402
from infrastructure.persistencia.composicion_persistente import construir_persistente          # noqa: E402

DIA = T - timedelta(days=30)                                  # holgura sobre los 5 días naturales de un servicio adicional y los 7 de un cambio


class Flujos:
    """Mixin sobre Apoyo (clientes, catálogo y evento En organización)."""

    def solicitud(self, evento, sid):
        filas = self.admin.get('/solicitudes', params={'evento_id': evento}).json()['solicitudes']
        return next(f for f in filas if f['solicitudId'] == sid)

    def decision(self, actor, aprobada=True):
        return {'actor': actor, 'aprobada': aprobada, 'fecha': DIA.isoformat(), 'motivo': ''}

    def adicional(self, servicio='DJ'):
        evento, contrato = self.evento_en_organizacion()
        self.ahora = DIA
        r = self.coord.post('/solicitudes-servicio-adicional', {'evento_id': evento, 'contrato_id': contrato, 'servicio': servicio})
        self.assertEqual(r.status_code, 201, r.text)
        return evento, contrato, r.json()['datos']['solicitud_id']

    def capturar(self, sid, **cuerpo):
        return self.coord.post(f'/solicitudes-servicio-adicional/{sid}/disponibilidad', cuerpo)

    # ======================================================================= D-P3 · servicios adicionales
    def test_dp3_servicio_adicional_con_costo_positivo_se_registra_y_administracion_lo_ve_antes_de_autorizar(self):
        pv = self.proveedor('DJ Nova', ['DJ'])
        evento, _, sid = self.adicional()
        r = self.capturar(sid, disponible=True, proveedor_id=pv, costo='800.00', condiciones='DJ 4 horas con sonido')
        self.assertEqual(r.status_code, 200, r.text)
        fila = self.solicitud(evento, sid)
        self.assertEqual(fila['estadoActual'], 'Pendiente de aprobación del Cliente')
        self.assertEqual(fila['datosProveedor'], {'proveedorId': pv, 'costo': '800.00', 'condiciones': 'DJ 4 horas con sonido'})   # Administración lo ve

    def test_dp3_el_servidor_rechaza_costo_cero_negativo_o_ausente_y_condiciones_vacias(self):
        pv = self.proveedor('DJ Nova', ['DJ'])
        evento, _, sid = self.adicional()
        for costo in ('0', '0.00', '-1', '-0.01', None):
            cuerpo = dict(disponible=True, proveedor_id=pv, condiciones='DJ 4 horas')
            if costo is not None:
                cuerpo['costo'] = costo
            r = self.capturar(sid, **cuerpo)
            self.assertEqual(r.status_code, 422, f'costo={costo}: {r.text}')
        r = self.capturar(sid, disponible=True, proveedor_id=pv, costo='800.00', condiciones='   ')
        self.assertEqual(r.status_code, 422, r.text)
        r = self.capturar(sid, disponible=True, proveedor_id=pv, costo='800.00')
        self.assertEqual(r.status_code, 422, r.text)
        self.assertIn('mayor que cero', self.capturar(sid, disponible=True, proveedor_id=pv, costo='0', condiciones='x').json()['detalle'])
        self.assertEqual(self.solicitud(evento, sid)['estadoActual'], 'Registrada')            # nada cambió
        self.assertIsNone(self.solicitud(evento, sid)['datosProveedor'])

    def test_dp3_el_proveedor_debe_estar_registrado_activo_y_ofrecer_el_servicio(self):
        activo = self.proveedor('DJ Activo', ['DJ'])
        inactivo = self.proveedor('DJ Inactivo', ['DJ'])
        otro_servicio = self.proveedor('Fotos', ['Fotografía'])
        self.admin.post(f'/proveedores/{inactivo}/desactivacion')
        evento, _, sid = self.adicional()
        for proveedor, motivo in ((inactivo, 'desactivado'), (otro_servicio, 'no ofrece el servicio'), ('PV-NO-REGISTRADO', 'no está registrado'), ('', 'Indica el proveedor')):
            r = self.capturar(sid, disponible=True, proveedor_id=proveedor, costo='800.00', condiciones='DJ')
            self.assertEqual(r.status_code, 422, proveedor)
            self.assertIn(motivo, r.json()['detalle'])
        self.assertEqual(self.solicitud(evento, sid)['estadoActual'], 'Registrada')
        self.assertEqual(self.capturar(sid, disponible=True, proveedor_id=activo, costo='800.00', condiciones='DJ').status_code, 200)

    def test_dp3_sin_proveedor_disponible_la_busqueda_continua_y_no_admite_datos_de_mas(self):
        pv = self.proveedor('DJ Nova', ['DJ'])
        evento, _, sid = self.adicional()
        mal = self.capturar(sid, disponible=False, proveedor_id=pv, costo='800.00')
        self.assertEqual(mal.status_code, 422, mal.text)
        self.assertEqual(self.capturar(sid, disponible=False).status_code, 200)
        self.assertEqual(self.solicitud(evento, sid)['estadoActual'], 'En búsqueda de proveedor')
        self.assertEqual(self.capturar(sid, disponible=True, proveedor_id=pv, costo='800.00', condiciones='DJ').status_code, 200)   # luego aparece uno

    def test_dp3_solo_coordinacion_captura_costos_y_condiciones(self):
        pv = self.proveedor('DJ Nova', ['DJ'])
        evento, _, sid = self.adicional()
        prov = self.cliente(PROVEEDOR, proveedor_id=pv)
        cuerpo = dict(disponible=True, proveedor_id=pv, costo='800.00', condiciones='DJ')
        for quien, cliente in (('administrador', self.admin), ('proveedor', prov)):
            r = cliente.post(f'/solicitudes-servicio-adicional/{sid}/disponibilidad', cuerpo)
            self.assertEqual(r.status_code, 403, quien)
            r = cliente.post(f'/solicitudes-cambio/SC-X/viabilidad', {'viable': True, 'condiciones_proveedor': 'x'})
            self.assertEqual(r.status_code, 403, quien)
            r = cliente.post('/sustituciones/SP-X/alternativa', {'proveedor_id': pv, 'condiciones_alternativa': 'x'})
            self.assertEqual(r.status_code, 403, quien)
        self.assertEqual(self.solicitud(evento, sid)['estadoActual'], 'Registrada')
        self.assertEqual(self.capturar(sid, **cuerpo).status_code, 200)

    def test_dp3_servicio_adicional_de_principio_a_fin_el_importe_es_solo_el_costo_del_proveedor(self):
        pv = self.proveedor('DJ Nova', ['DJ'])
        evento, contrato, sid = self.adicional()
        base = f'/solicitudes-servicio-adicional/{sid}'
        self.assertEqual(self.capturar(sid, disponible=True, proveedor_id=pv, costo='800.00', condiciones='DJ 4 horas').status_code, 200)
        self.assertEqual(self.coord.post(f'{base}/aprobacion-cliente', self.decision('Cliente')).status_code, 200)
        self.assertEqual(self.coord.post(f'{base}/autorizacion', self.decision('Administración')).status_code, 403)     # Coordinación no autoriza
        self.assertEqual(self.admin.post(f'{base}/autorizacion', self.decision('Administración')).status_code, 200)     # Administración sí
        self.assertEqual(self.solicitud(evento, sid)['estadoActual'], 'Autorizada')
        self.assertEqual(self.coord.post(f'{base}/anexo', {'descripcion': 'Anexo DJ'}).status_code, 200)
        pago = {'concepto': 'ServicioAdicional', 'comunicado_en': DIA.isoformat()}
        for mal in ('900.00', '799.99', '1.00'):                                                         # solo el costo del proveedor, sin cargo propio
            r = self.coord.post(f'{base}/solicitud-pago', {**pago, 'importe': mal})
            self.assertEqual(r.status_code, 422, mal)
        r = self.coord.post(f'{base}/solicitud-pago', {**pago, 'importe': '800.00'})
        self.assertEqual(r.status_code, 200, r.text)
        ob = r.json()['datos']['obligacion_id']
        ec = self.admin.get(f'/eventos/{evento}/pagos').json()['estadosCuenta'][0]
        propias = [o for o in ec['obligacionesAdicionales'] if o['concepto'] == 'ServicioAdicional']
        self.assertEqual([o['importe'] for o in propias], ['800.00'])                                    # una sola obligación, sin cargo de gestión
        self.ahora = DIA + timedelta(hours=2)
        p = self.admin.post(f"/estados-cuenta/{ec['estadoCuentaId']}/pagos", {'obligacion_id': ob, 'importe': '800.00', 'fecha': self.ahora.isoformat(),
                                                                                'comprobante': 'C-DJ', 'verificar_ahora': True})
        self.assertEqual(p.status_code, 201, p.text)
        r = self.coord.post(f'{base}/confirmacion')
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.solicitud(evento, sid)['estadoActual'], 'Confirmada')
        self.assertEqual(self.solicitud(evento, sid)['datosProveedor']['costo'], '800.00')               # los datos registrados se conservan

    # ======================================================================= D-P3 · cambios
    def cambio(self):
        evento, contrato = self.evento_en_organizacion()
        self.ahora = DIA
        r = self.coord.post('/solicitudes-cambio', {'evento_id': evento, 'contrato_id': contrato, 'descripcion': 'Cambio de menú', 'tarifa_vigente': '500.00'})
        self.assertEqual(r.status_code, 201, r.text)
        return evento, r.json()['datos']['solicitud_id']

    def test_dp3_cambio_con_condiciones_opcionales_visibles_para_administracion(self):
        evento, sid = self.cambio()
        r = self.coord.post(f'/solicitudes-cambio/{sid}/viabilidad', {'viable': True, 'costo_adicional_proveedor': '1000.00',
                                                                       'condiciones_proveedor': '  Pago del proveedor por adelantado  '})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.solicitud(evento, sid)['datosProveedor'], {'proveedorId': None, 'costo': '1000.00', 'condiciones': 'Pago del proveedor por adelantado'})
        self.assertEqual(self.coord.post(f'/solicitudes-cambio/{sid}/decision-cliente', self.decision('Cliente')).status_code, 200)
        self.assertEqual(self.coord.post(f'/solicitudes-cambio/{sid}/autorizacion', self.decision('Administración')).status_code, 403)
        self.assertEqual(self.admin.post(f'/solicitudes-cambio/{sid}/autorizacion', self.decision('Administración')).status_code, 200)

    def test_dp3_las_condiciones_de_un_cambio_son_opcionales(self):
        for cuerpo in ({'viable': True, 'costo_adicional_proveedor': '1000.00'},
                       {'viable': True, 'costo_adicional_proveedor': '1000.00', 'condiciones_proveedor': None},
                       {'viable': True, 'costo_adicional_proveedor': '1000.00', 'condiciones_proveedor': ''},
                       {'viable': True, 'costo_adicional_proveedor': '1000.00', 'condiciones_proveedor': '   '}):
            evento, sid = self.cambio()
            r = self.coord.post(f'/solicitudes-cambio/{sid}/viabilidad', cuerpo)
            self.assertEqual(r.status_code, 200, f'{cuerpo}: {r.text}')
            self.assertEqual(self.solicitud(evento, sid)['datosProveedor'], {'proveedorId': None, 'costo': '1000.00', 'condiciones': None}, str(cuerpo))

    def test_dp3_las_condiciones_de_un_cambio_tienen_limite_y_un_cambio_no_viable_no_las_conserva(self):
        evento, sid = self.cambio()
        r = self.coord.post(f'/solicitudes-cambio/{sid}/viabilidad', {'viable': True, 'condiciones_proveedor': 'x' * 1001})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.solicitud(evento, sid)['estadoActual'], 'Registrada')
        r = self.coord.post(f'/solicitudes-cambio/{sid}/viabilidad', {'viable': False, 'motivo': 'El proveedor no puede', 'condiciones_proveedor': 'se descarta'})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIsNone(self.solicitud(evento, sid)['datosProveedor'])

    # ======================================================================= D-P3 · sustituciones
    def sustitucion(self, original):
        evento, contrato = self.evento_en_organizacion()
        sid_serv = self.servicios(evento)['Banquete']['servicioContratadoId']
        self.assertEqual(self.coord.post(f'/eventos/{evento}/servicios/{sid_serv}/proveedor', {'proveedor_id': original}).status_code, 200)
        self.ahora = DIA
        r = self.coord.post('/sustituciones', {'evento_id': evento, 'servicio_contratado_id': sid_serv, 'contrato_id': contrato})
        self.assertEqual(r.status_code, 201, r.text)
        return evento, r.json()['datos']['sustitucion_id']

    def test_dp3_sustitucion_con_proveedor_del_catalogo_condiciones_y_costo_visibles_para_administracion(self):
        original, alterno = self.proveedor('Banquetes Originales'), self.proveedor('Banquetes Alternos')
        evento, sid = self.sustitucion(original)
        r = self.coord.post(f'/sustituciones/{sid}/alternativa', {'proveedor_id': alterno, 'condiciones_alternativa': 'Menú equivalente', 'costo_adicional': '800.00'})
        self.assertEqual(r.status_code, 200, r.text)
        fila = self.solicitud(evento, sid)
        self.assertEqual(fila['datosProveedor'], {'proveedorId': alterno, 'costo': '800.00', 'condiciones': 'Menú equivalente'})
        self.assertEqual(self.coord.post(f'/sustituciones/{sid}/decision-cliente', self.decision('Cliente')).status_code, 200)
        self.assertEqual(self.admin.post(f'/sustituciones/{sid}/autorizacion', self.decision('Administración')).status_code, 200)

    def test_dp3_sustitucion_rechaza_proveedores_inactivos_ajenos_al_servicio_no_registrados_o_el_mismo_original(self):
        original, alterno = self.proveedor('Banquetes Originales'), self.proveedor('Banquetes Alternos')
        inactivo, fotos = self.proveedor('Banquetes Inactivos'), self.proveedor('Fotos', ['Fotografía'])
        self.admin.post(f'/proveedores/{inactivo}/desactivacion')
        evento, sid = self.sustitucion(original)
        casos = ((inactivo, 'desactivado'), (fotos, 'no ofrece el servicio'), ('PV-NO-REGISTRADO', 'no está registrado'), (original, 'distinto'))
        for proveedor, motivo in casos:
            r = self.coord.post(f'/sustituciones/{sid}/alternativa', {'proveedor_id': proveedor, 'condiciones_alternativa': 'Menú'})
            self.assertEqual(r.status_code, 422, proveedor)
            self.assertIn(motivo, r.json()['detalle'])
        r = self.coord.post(f'/sustituciones/{sid}/alternativa', {'proveedor_id': alterno, 'condiciones_alternativa': 'Menú', 'costo_adicional': '-5'})
        self.assertEqual(r.status_code, 422)
        self.assertIsNone(self.solicitud(evento, sid)['datosProveedor'])
        self.assertEqual(self.solicitud(evento, sid)['estadoActual'], 'En búsqueda de alternativa')

    # ======================================================================= no se amplían permisos (S-5 y S-6 siguen pendientes)
    def test_dp3_no_amplia_los_permisos_que_siguen_pendientes_s5_y_s6(self):
        self.assertEqual({p for p in permisos_del_rol(COORDINADOR) if p.startswith('proveedores.')},
                         {'proveedores.asignar', 'proveedores.consultar', 'proveedores.registrar', 'proveedores.responder'})   # igual que antes de D-P3
        self.assertIn('solicitudes.importe_adicional', permisos_del_rol(ADMINISTRADOR))
        self.assertNotIn('solicitudes.importe_adicional', permisos_del_rol(COORDINADOR))                         # S-6 sigue como estaba
        self.assertEqual(self.coord.post('/sustituciones/SP-X/importe-adicional', {'importe': '10'}).status_code, 403)

    # ======================================================================= D-P1
    def test_dp1_el_catalogo_no_ofrece_eliminar_proveedores(self):
        for ruta, operaciones in self.app.openapi()['paths'].items():
            if ruta.startswith('/proveedores'):
                self.assertNotIn('delete', operaciones, ruta)
        r = self.admin.http.delete('/proveedores/PV-X', headers={'X-CSRF-Token': self.admin.csrf})
        self.assertIn(r.status_code, (404, 405))


class DP3EnMemoria(Flujos, Apoyo, unittest.TestCase):
    def crear_contenedor(self):
        return construir()

    def salidas_pendientes(self):
        return 0

    def reiniciar_contenedor(self):
        return self.contenedor


class DP3EnPostgreSQL(Flujos, Apoyo, BaseConBD):
    def setUp(self):
        BaseConBD.setUp(self)
        Apoyo.setUp(self)

    def crear_contenedor(self):
        return construir_persistente(motor=self.motor)

    def salidas_pendientes(self):
        return 0

    def reiniciar_contenedor(self):
        return construir_persistente(motor=self.motor)

    def test_dp3_los_costos_y_condiciones_quedan_en_postgresql_y_sobreviven_a_un_reinicio(self):
        pv, original = self.proveedor('DJ Nova', ['DJ']), self.proveedor('Banquetes Originales')
        evento, _, sa_id = self.adicional()
        self.assertEqual(self.capturar(sa_id, disponible=True, proveedor_id=pv, costo='800.00', condiciones='DJ 4 horas').status_code, 200)
        cev, csid = self.cambio()
        self.assertEqual(self.coord.post(f'/solicitudes-cambio/{csid}/viabilidad', {'viable': True, 'costo_adicional_proveedor': '1000.00',
                                                                                     'condiciones_proveedor': 'Pago adelantado'}).status_code, 200)
        sev, ssid = self.sustitucion(original)
        alterno = self.proveedor('Banquetes Alternos')
        self.assertEqual(self.coord.post(f'/sustituciones/{ssid}/alternativa', {'proveedor_id': alterno, 'condiciones_alternativa': 'Menú equivalente',
                                                                                 'costo_adicional': '250.50'}).status_code, 200)
        with self.motor.connect() as con:
            sa_fila = con.execute(sa.text('select disponibilidad_proveedor_id, disponibilidad_costo, disponibilidad_condiciones from solicitud_servicio_adicional where solicitud_id=:i'), {'i': sa_id}).one()
            cambio = con.execute(sa.text('select costo_proveedor, condiciones_proveedor from solicitud_cambio where solicitud_id=:i'), {'i': csid}).one()
            alt = con.execute(sa.text('select disponibilidad_proveedor_id, disponibilidad_costo, disponibilidad_condiciones from sustitucion_alternativa where sustitucion_id=:i'), {'i': ssid}).one()
        self.assertEqual((sa_fila[0], str(sa_fila[1]), sa_fila[2]), (pv, '800.00', 'DJ 4 horas'))
        self.assertEqual((str(cambio[0]), cambio[1]), ('1000.00', 'Pago adelantado'))
        self.assertEqual((alt[0], alt[2]), (alterno, 'Menú equivalente'))
        # «reinicio»: un contenedor nuevo sobre la misma base devuelve los mismos datos a Administración
        nuevo = self.reiniciar_contenedor()
        from application.cqrs import ConsultarSolicitudesPorEstadoQuery
        filas = {f.solicitudId: f.datosProveedor for f in nuevo.queries.solicitudes_por_estado.handle(ConsultarSolicitudesPorEstadoQuery()).solicitudes}
        self.assertEqual(filas[sa_id]['costo'], '800.00')
        self.assertEqual(filas[csid]['condiciones'], 'Pago adelantado')
        self.assertEqual(filas[ssid]['proveedorId'], alterno)


if __name__ == '__main__':
    unittest.main()
