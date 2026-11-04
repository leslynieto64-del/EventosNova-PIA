"""Decisiones aprobadas el 01/11/2026: S-1 (tres roles), S-2 (control financiero de Administración), S-3 (cancelación por falta de regularización),
S-4 (consulta financiera de Coordinación), S-5 (procedencia de la respuesta del proveedor), S-6 (integración del importe adicional de una
sustitución) y S-9 (separación de funciones, sin superusuario). Ver docs/ADR/ADR-011-decisiones-aprobadas-s1-s6-s9.md.

Con autenticación activa y llamando directo a la API (no solo la interfaz), con la composición en memoria y con PostgreSQL (base de PRUEBAS aislada).
Ejecutar desde la raíz:  python -m unittest tests.test_decisiones_s1_s9 -v"""
import os, sys, unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
import sqlalchemy as sa                                                                      # noqa: E402
from apoyo_bd import BaseConBD                                                               # noqa: E402
from test_decisiones_dp1_dp3 import DIA, Flujos                                              # noqa: E402
from test_decisiones_dp2_s7_s8 import Apoyo, T                                               # noqa: E402
from test_seguridad import T0                                                                # noqa: E402
from application.seguridad import (ADMINISTRADOR, COORDINADOR, MATRIZ, PROVEEDOR, ROLES, permisos_del_rol)   # noqa: E402
from infrastructure.composicion import construir                                              # noqa: E402
from infrastructure.persistencia.composicion_persistente import construir_persistente          # noqa: E402

# Operaciones financieras que solo Administración puede ejecutar (S-2). El cuerpo es irrelevante: el permiso se comprueba antes.
OPERACIONES_FINANCIERAS = (
    ('POST', '/estados-cuenta/EC-X/pagos'), ('POST', '/estados-cuenta/EC-X/pagos/PG-X/verificacion'),
    ('POST', '/estados-cuenta/EC-X/protocolo-cobro'), ('POST', '/estados-cuenta/EC-X/regularizacion'),
    ('POST', '/estados-cuenta/EC-X/vencimiento-saldo-original'), ('POST', '/estados-cuenta/EC-X/devoluciones/DV-X/ejecucion'),
    ('POST', '/solicitudes-cambio/SC-X/autorizacion'), ('POST', '/solicitudes-servicio-adicional/SA-X/autorizacion'),
    ('POST', '/sustituciones/SP-X/autorizacion'), ('POST', '/sustituciones/SP-X/importe-adicional'),
    ('POST', '/eventos/EV-X/revision-administrativa'))
# Operaciones de Coordinación que Administración no puede crear ni gestionar (S-9).
OPERACIONES_DE_COORDINACION = (
    ('POST', '/eventos'), ('POST', '/eventos/EV-X/propuestas'), ('POST', '/propuestas/PR-X/aceptacion'), ('POST', '/propuestas/PR-X/versiones'),
    ('POST', '/propuestas/PR-X/contrato'), ('POST', '/contratos/CT-X/firma'), ('POST', '/contratos/CT-X/comunicacion-politica-no-reembolso'),
    ('POST', '/solicitudes-cambio'), ('POST', '/solicitudes-cambio/SC-X/viabilidad'), ('POST', '/solicitudes-servicio-adicional'),
    ('POST', '/solicitudes-servicio-adicional/SA-X/disponibilidad'), ('POST', '/sustituciones'), ('POST', '/sustituciones/SP-X/alternativa'),
    ('POST', '/eventos/EV-X/inicio'), ('POST', '/eventos/EV-X/finalizacion'), ('POST', '/eventos/EV-X/cancelacion'),
    ('POST', '/eventos/EV-X/servicios/SV-X/proveedor'))


# Las ayudas de los flujos de D-P3 (sin sus pruebas, que ya corren en test_decisiones_dp1_dp3).
Ayudas = type('Ayudas', (), {k: v for k, v in vars(Flujos).items() if not k.startswith(('test_', '__'))})


class Decisiones(Ayudas):
    def estado_de_cuenta(self, evento):
        return self.coord.get(f'/eventos/{evento}/pagos').json()['estadosCuenta'][0]

    def llamar(self, cliente, metodo, ruta, cuerpo=None):
        return cliente.post(ruta, cuerpo if cuerpo is not None else {}) if metodo == 'POST' else cliente.get(ruta)

    # ======================================================================= S-1
    def test_s1_existen_exactamente_tres_roles_y_ninguna_ruta_los_ignora(self):
        self.assertEqual(set(ROLES), {ADMINISTRADOR, COORDINADOR, PROVEEDOR})
        self.assertEqual((ADMINISTRADOR, COORDINADOR, PROVEEDOR), ('administrador', 'coordinador', 'proveedor'))
        con_acceso = {rol for rol in ROLES for permisos in MATRIZ.values() if permisos & permisos_del_rol(rol)}
        self.assertEqual(con_acceso, set(ROLES))

    def test_s1_no_se_pueden_crear_cuentas_con_otros_roles_ni_para_el_cliente(self):
        for rol in ('cliente', 'superusuario', 'administracion', 'Administrador', ''):
            r = self.admin.post('/usuarios', {'correo': f'x.{abs(hash(rol))}@ejemplo.mx', 'nombre': 'Persona Extra', 'rol': rol, 'contrasena': 'una-contrasena-larga-y-unica-1'})
            self.assertEqual(r.status_code, 422, rol)
        self.assertEqual(self.coord.post('/usuarios', {'correo': 'a@ejemplo.mx', 'nombre': 'Persona Extra', 'rol': 'coordinador', 'contrasena': 'una-contrasena-larga-y-unica-1'}).status_code, 403)

    def test_s1_administracion_administra_las_cuentas_y_las_demas_no(self):
        pv = self.proveedor('Proveedor Uno')
        prov = self.cliente(PROVEEDOR, proveedor_id=pv)
        for quien, cliente in (('coordinador', self.coord), ('proveedor', prov)):
            self.assertEqual(cliente.get('/usuarios').status_code, 403, quien)
            self.assertEqual(cliente.post('/usuarios/US-X/actualizacion', {'nombre': 'X', 'correo': 'x@ejemplo.mx'}).status_code, 403, quien)
            self.assertEqual(cliente.post('/usuarios/US-X/estado', {'activa': False}).status_code, 403, quien)
            self.assertEqual(cliente.post('/usuarios/US-X/contrasena', {'contrasena': 'una-contrasena-larga-y-unica-1'}).status_code, 403, quien)
        self.assertEqual(self.admin.get('/usuarios').status_code, 200)

    # ======================================================================= S-2
    def test_s2_coordinacion_y_proveedor_no_ejecutan_ninguna_operacion_financiera(self):
        prov = self.cliente(PROVEEDOR, proveedor_id=self.proveedor('Proveedor Uno'))
        for metodo, ruta in OPERACIONES_FINANCIERAS:
            for quien, cliente in (('coordinador', self.coord), ('proveedor', prov)):
                self.assertEqual(self.llamar(cliente, metodo, ruta).status_code, 403, f'{quien} {ruta}')
            self.assertNotEqual(self.llamar(self.admin, metodo, ruta).status_code, 403, f'administrador {ruta}')       # Administración sí está autorizada

    def test_s2_administracion_registra_y_verifica_pagos_y_coordinacion_no_aunque_el_importe_sea_correcto(self):
        evento, _ = self.evento_en_organizacion()
        ec = self.estado_de_cuenta(evento)
        saldo = next(o for o in self.admin.get('/pagos-pendientes', params={'evento_id': evento}).json()['pagos'] if o['concepto'] == 'SaldoContratoOriginal')
        cuerpo = {'obligacion_id': saldo['obligacionId'], 'importe': '1000.00', 'fecha': T0.isoformat(), 'comprobante': 'C-S2', 'verificar_ahora': False}
        self.assertEqual(self.coord.post(f"/estados-cuenta/{ec['estadoCuentaId']}/pagos", cuerpo).status_code, 403)
        r = self.admin.post(f"/estados-cuenta/{ec['estadoCuentaId']}/pagos", cuerpo)
        self.assertEqual(r.status_code, 201, r.text)
        pago = r.json()['datos']['pago_id']
        self.assertEqual(self.coord.post(f"/estados-cuenta/{ec['estadoCuentaId']}/pagos/{pago}/verificacion", {'verificado_en': T0.isoformat()}).status_code, 403)
        self.assertEqual(self.admin.post(f"/estados-cuenta/{ec['estadoCuentaId']}/pagos/{pago}/verificacion", {'verificado_en': T0.isoformat()}).status_code, 200)
        self.assertEqual(self.admin.post(f"/estados-cuenta/{ec['estadoCuentaId']}/pagos/{pago}/verificacion", {'verificado_en': T0.isoformat()}).status_code, 422)   # no se verifica dos veces

    def test_s2_un_pago_igual_o_menor_a_cero_se_rechaza_y_un_excedente_de_otro_concepto_no_se_devuelve(self):
        evento, _ = self.evento_en_organizacion()
        ec = self.estado_de_cuenta(evento)
        saldo = next(o for o in self.admin.get('/pagos-pendientes', params={'evento_id': evento}).json()['pagos'] if o['concepto'] == 'SaldoContratoOriginal')
        for importe in ('0', '-5'):
            r = self.admin.post(f"/estados-cuenta/{ec['estadoCuentaId']}/pagos", {'obligacion_id': saldo['obligacionId'], 'importe': importe, 'fecha': T0.isoformat(), 'comprobante': f'C-{importe}', 'verificar_ahora': True})
            self.assertEqual(r.status_code, 422, importe)
        # B-4, B-5 y X-14: un pago mayor al saldo de otro concepto se registra y verifica, sin devolución ni aplicación a otra obligación
        r = self.admin.post(f"/estados-cuenta/{ec['estadoCuentaId']}/pagos", {'obligacion_id': saldo['obligacionId'], 'importe': '8000.00', 'fecha': T0.isoformat(), 'comprobante': 'C-EXC', 'verificar_ahora': True})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(self.admin.get('/devoluciones-pendientes', params={'evento_id': evento}).json()['devoluciones'], [])

    # ======================================================================= S-3
    def saldo_vencido(self):
        evento, contrato = self.evento_en_organizacion()
        ec = self.estado_de_cuenta(evento)['estadoCuentaId']
        limite = datetime.fromisoformat(next(o for o in self.admin.get('/pagos-pendientes', params={'evento_id': evento}).json()['pagos']
                                             if o['concepto'] == 'SaldoContratoOriginal')['fechaLimite'])
        self.ahora = limite + timedelta(hours=1)
        return evento, ec, limite

    def test_s3_cancelacion_por_falta_de_regularizacion_procedimiento_completo_y_protegido(self):
        evento, ec, limite = self.saldo_vencido()
        cancelar = lambda cliente, **extra: cliente.post(f'/eventos/{evento}/cancelacion-por-falta-de-regularizacion', {'motivo': 'Saldo vencido sin regularizar', **extra})
        # anticipada: nadie verificó el vencimiento ni la ausencia de regularización
        r = cancelar(self.coord)
        self.assertEqual(r.status_code, 422, r.text)
        self.assertIn('Administración no ha verificado', r.json()['detalle'])
        self.assertEqual(cancelar(self.admin).status_code, 403)                                         # Administración no cancela
        self.assertEqual(self.estado(evento), 'En organización')
        # 1) el sistema identifica el vencimiento y 2) Administración comprueba la ausencia de regularización
        self.assertEqual(self.admin.post(f'/estados-cuenta/{ec}/vencimiento-saldo-original').status_code, 200)
        comunicado = self.ahora + timedelta(hours=1)
        self.assertEqual(self.admin.post(f'/estados-cuenta/{ec}/protocolo-cobro', {'importe_moratorio': '200.00', 'comunicado_en': comunicado.isoformat(), 'seguimiento': 'Recordatorio'}).status_code, 200)
        self.ahora = comunicado + timedelta(hours=25)
        self.assertEqual(self.admin.post(f'/estados-cuenta/{ec}/regularizacion', {'revisado_en': self.ahora.isoformat()}).status_code, 200)
        # 3) Coordinación registra la cancelación: la cuenta y el momento los fija el servidor, no el cuerpo
        r = cancelar(self.coord, coordinador='Otra Persona', fecha='2020-01-01T00:00:00')
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.estado(evento), 'Cancelado')
        # no se duplica
        r = cancelar(self.coord)
        self.assertEqual(r.status_code, 200)
        self.assertIn('ya estaba cancelado', r.json()['mensaje'])
        self.registro_de_la_cancelacion(evento)

    def registro_de_la_cancelacion(self, evento):
        ev = self.contenedor.repos.eventos.obtener_por_id(evento)
        self.assertEqual(ev.motivo_cancelacion.registrado_por, 'Persona coordinador')               # la cuenta de la sesión, no «Otra Persona»
        self.assertNotEqual(ev.motivo_cancelacion.fecha.year, 2020)                                  # el reloj del servidor
        self.assertEqual(ev.motivo_cancelacion.descripcion, 'Saldo vencido sin regularizar')

    def test_s3_no_hay_cancelacion_injustificada_si_el_saldo_no_esta_vencido_o_el_evento_ya_inicio(self):
        evento, _ = self.evento_en_organizacion()
        r = self.coord.post(f'/eventos/{evento}/cancelacion-por-falta-de-regularizacion', {'motivo': 'Sin justificación'})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.estado(evento), 'En organización')
        r = self.coord.post(f'/eventos/{evento}/cancelacion-por-falta-de-regularizacion', {'motivo': ''})
        self.assertEqual(r.status_code, 422)

    # ======================================================================= S-4
    def test_s4_coordinacion_consulta_la_informacion_financiera_y_no_puede_modificarla(self):
        evento, _ = self.evento_en_organizacion()
        ec = self.estado_de_cuenta(evento)
        self.assertEqual({'anticipo', 'pagosRegistrados', 'saldoContratoOriginal', 'obligacionesAdicionales', 'devoluciones'} - set(ec), set())
        self.assertEqual(ec['anticipo']['estado'], 'Liquidada')
        self.assertEqual(ec['saldoContratoOriginal']['importe'], '7000.00')
        self.assertEqual(ec['saldoContratoOriginal']['saldo'], '7000.00')
        self.assertIsNotNone(ec['saldoContratoOriginal']['fechaLimite'])
        self.assertEqual(ec['pagosRegistrados'][0]['estado'], 'Verificado')
        pendientes = self.coord.get('/pagos-pendientes', params={'evento_id': evento})
        self.assertEqual(pendientes.status_code, 200)
        self.assertEqual(self.coord.get('/devoluciones-pendientes', params={'evento_id': evento}).status_code, 200)
        # la misma información que ve Administración
        self.assertEqual(self.admin.get(f'/eventos/{evento}/pagos').json(), self.coord.get(f'/eventos/{evento}/pagos').json())
        for metodo, ruta in OPERACIONES_FINANCIERAS:
            self.assertEqual(self.llamar(self.coord, metodo, ruta).status_code, 403, ruta)             # ni modificar, ni verificar, ni devolver, ni autorizar

    # ======================================================================= S-5
    def servicio_pendiente(self, nombre='Banquetes Valle'):
        pv = self.proveedor(nombre)
        evento, _ = self.evento_en_organizacion()
        sid = self.servicios(evento)['Banquete']['servicioContratadoId']
        self.assertEqual(self.coord.post(f'/eventos/{evento}/servicios/{sid}/proveedor', {'proveedor_id': pv}).status_code, 200)
        return pv, evento, f'/eventos/{evento}/servicios/{sid}/respuesta-proveedor'

    def test_s5_el_proveedor_responde_directamente_y_queda_registrado_como_directa(self):
        pv, evento, ruta = self.servicio_pendiente()
        prov = self.cliente(PROVEEDOR, proveedor_id=pv)
        r = prov.post(ruta, {'proveedor_id': pv, 'disponible': True})
        self.assertEqual(r.status_code, 200, r.text)
        respuesta = self.coord.get(f'/eventos/{evento}/administracion').json()['proveedores'][0]['respuesta']
        self.assertEqual((respuesta['origen'], respuesta['medio'], respuesta['disponible']), ('Proveedor', None, True))
        self.assertEqual(respuesta['registradoPor'], 'Persona proveedor')
        asignaciones = prov.get('/mis-asignaciones').json()['eventos'][0]['servicios'][0]
        self.assertEqual(asignaciones['respuesta']['origen'], 'Proveedor')

    def test_s5_coordinacion_registra_la_respuesta_con_el_medio_y_queda_distinguida_de_la_directa(self):
        pv, evento, ruta = self.servicio_pendiente()
        sin_medio = self.coord.post(ruta, {'proveedor_id': pv, 'disponible': True})
        self.assertEqual(sin_medio.status_code, 422, sin_medio.text)                                    # el medio es obligatorio
        medio_invalido = self.coord.post(ruta, {'proveedor_id': pv, 'disponible': True, 'medio': 'Paloma mensajera'})
        self.assertEqual(medio_invalido.status_code, 422)
        self.assertEqual(self.servicios(evento)['Banquete']['estado'], 'Pendiente de confirmación del proveedor')
        r = self.coord.post(ruta, {'proveedor_id': pv, 'disponible': True, 'medio': 'Llamada telefónica'})
        self.assertEqual(r.status_code, 200, r.text)
        servicio = self.servicios(evento)['Banquete']
        self.assertEqual(servicio['estado'], 'Confirmado por el proveedor')
        respuesta = servicio['respuesta']
        self.assertEqual((respuesta['origen'], respuesta['medio'], respuesta['disponible'], respuesta['registradoPor']),
                         ('Coordinación', 'Llamada telefónica', True, 'Persona coordinador'))
        self.assertTrue(respuesta['fecha'])
        self.assertTrue(respuesta['registradoPorId'].startswith('US-'))
        otra = self.coord.post(ruta, {'proveedor_id': pv, 'disponible': False, 'medio': 'Correo electrónico'})
        self.assertEqual(otra.status_code, 422)                                                         # ya respondió: no se reescribe

    def test_s5_nadie_suplanta_la_identidad_ni_el_origen_y_no_se_expone_a_otros_proveedores(self):
        pv, evento, ruta = self.servicio_pendiente()
        otro = self.proveedor('Otro Proveedor')
        prov, ajeno = self.cliente(PROVEEDOR, proveedor_id=pv), self.cliente(PROVEEDOR, proveedor_id=otro)
        self.assertEqual(prov.post(ruta, {'proveedor_id': pv, 'disponible': True, 'medio': 'Llamada telefónica'}).status_code, 422)   # un proveedor no declara medio
        self.assertEqual(prov.post(ruta, {'proveedor_id': otro, 'disponible': True}).status_code, 403)                                # ni responde por otro
        self.assertEqual(ajeno.post(ruta, {'proveedor_id': pv, 'disponible': True}).status_code, 403)                                  # otro proveedor tampoco
        self.assertEqual(ajeno.post(ruta, {'proveedor_id': otro, 'disponible': True}).status_code, 422)                               # propio pero no asignado
        self.assertEqual(self.admin.post(ruta, {'proveedor_id': pv, 'disponible': True}).status_code, 403)
        for extra in ({'origen': 'Proveedor'}, {'registrado_por': 'US-X'}, {'registradoPor': 'x'}):
            self.assertEqual(self.coord.post(ruta, {'proveedor_id': pv, 'disponible': True, 'medio': 'Otro', **extra}).status_code, 422, str(extra))
        self.assertEqual(ajeno.get('/mis-asignaciones').json()['eventos'], [])                                                          # no ve lo de otro
        self.assertEqual(self.servicios(evento)['Banquete']['estado'], 'Pendiente de confirmación del proveedor')                       # nada cambió

    def test_s5_la_respuesta_de_no_disponible_por_coordinacion_tambien_conserva_su_procedencia(self):
        pv, evento, ruta = self.servicio_pendiente()
        r = self.coord.post(ruta, {'proveedor_id': pv, 'disponible': False, 'medio': 'Mensaje (WhatsApp o SMS)'})
        self.assertEqual(r.status_code, 200, r.text)
        servicio = self.servicios(evento)['Banquete']
        self.assertEqual(servicio['estado'], 'Proveedor no disponible')
        self.assertEqual((servicio['respuesta']['disponible'], servicio['respuesta']['medio']), (False, 'Mensaje (WhatsApp o SMS)'))

    # ======================================================================= S-6
    def sustitucion_autorizable(self, con_costo=True):
        original, alterno = self.proveedor('Banquetes Originales'), self.proveedor('Banquetes Alternos')
        evento, contrato = self.evento_en_organizacion()
        servicio = self.servicios(evento)['Banquete']['servicioContratadoId']
        self.assertEqual(self.coord.post(f'/eventos/{evento}/servicios/{servicio}/proveedor', {'proveedor_id': original}).status_code, 200)
        self.ahora = DIA
        sid = self.coord.post('/sustituciones', {'evento_id': evento, 'servicio_contratado_id': servicio, 'contrato_id': contrato}).json()['datos']['sustitucion_id']
        alt = {'proveedor_id': alterno, 'condiciones_alternativa': 'Menú equivalente'}
        if con_costo:
            alt['costo_adicional'] = '800.00'
        self.assertEqual(self.coord.post(f'/sustituciones/{sid}/alternativa', alt).status_code, 200)
        return evento, contrato, sid, alterno

    def obligaciones_de(self, evento, sid):
        ec = self.estado_de_cuenta(evento)
        return [o for o in ec['obligacionesAdicionales'] if o.get('origenId') == sid or o['concepto'] == 'SustitucionProveedor']

    def test_s6_administracion_integra_el_importe_autorizado_una_sola_vez_y_con_trazabilidad(self):
        evento, contrato, sid, alterno = self.sustitucion_autorizable()
        integrar = lambda cliente, importe='800.00': cliente.post(f'/sustituciones/{sid}/importe-adicional', {'importe': importe})
        self.assertEqual(integrar(self.admin).status_code, 422)                                         # antes de las autorizaciones
        self.assertEqual(self.coord.post(f'/sustituciones/{sid}/decision-cliente', self.decision('Cliente')).status_code, 200)
        self.assertEqual(integrar(self.admin).status_code, 422)                                         # falta la autorización de Administración
        self.assertEqual(self.coord.post(f'/sustituciones/{sid}/autorizacion', self.decision('Administración')).status_code, 403)
        self.assertEqual(self.admin.post(f'/sustituciones/{sid}/autorizacion', self.decision('Administración')).status_code, 200)
        self.assertEqual(self.coord.post(f'/sustituciones/{sid}/anexo', {'descripcion': 'Anexo reemplazo'}).status_code, 200)
        self.assertEqual(integrar(self.coord).status_code, 403)                                         # Coordinación no integra
        for mal in ('799.99', '800.01', '1.00', '0'):
            self.assertEqual(integrar(self.admin, mal).status_code, 422, mal)                           # solo el importe autorizado
        antes = self.estado_de_cuenta(evento)
        r = integrar(self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        obligacion = r.json()['datos']['obligacion_id']
        despues = self.estado_de_cuenta(evento)
        nuevas = [o for o in despues['obligacionesAdicionales'] if o['obligacionId'] == obligacion]
        self.assertEqual([(o['concepto'], o['importe']) for o in nuevas], [('SustitucionProveedor', '800.00')])
        self.assertEqual(despues['pagosRegistrados'], antes['pagosRegistrados'])                         # no se tocaron pagos anteriores
        self.assertEqual(despues['anticipo'], antes['anticipo'])
        self.assertEqual(integrar(self.admin).status_code, 422)                                         # no se integra dos veces
        self.assertEqual(len(self.estado_de_cuenta(evento)['obligacionesAdicionales']), len(despues['obligacionesAdicionales']))
        self.assertEqual(nuevas[0]['origenId'], sid)                                                    # trazabilidad: sustitución → obligación

    def test_s6_una_sustitucion_sin_costo_adicional_no_crea_ninguna_obligacion(self):
        evento, _, sid, _ = self.sustitucion_autorizable(con_costo=False)
        antes = self.estado_de_cuenta(evento)
        self.assertEqual(self.coord.post(f'/sustituciones/{sid}/decision-cliente', self.decision('Cliente')).status_code, 200)
        r = self.admin.post(f'/sustituciones/{sid}/importe-adicional', {'importe': '0'})
        self.assertEqual(r.status_code, 422)
        self.assertIn('no genera costo adicional', r.json()['detalle'])
        r = self.admin.post(f'/sustituciones/{sid}/importe-adicional', {'importe': '100.00'})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.estado_de_cuenta(evento), antes)                                          # ninguna obligación artificial

    # ======================================================================= S-9
    def test_s9_administracion_no_crea_ni_gestiona_lo_de_coordinacion(self):
        for metodo, ruta in OPERACIONES_DE_COORDINACION:
            self.assertEqual(self.llamar(self.admin, metodo, ruta).status_code, 403, ruta)
            self.assertNotEqual(self.llamar(self.coord, metodo, ruta).status_code, 403, f'coordinador {ruta}')

    def test_s9_administracion_consulta_eventos_propuestas_contratos_solicitudes_y_estados_financieros(self):
        evento, contrato = self.evento_en_organizacion()
        for ruta in ('/eventos?desde=2026-01-01T00:00:00&hasta=2027-12-31T00:00:00', f'/eventos/{evento}/administracion', f'/eventos/{evento}/propuestas',
                     f'/eventos/{evento}/pagos', '/pagos-pendientes', '/solicitudes', '/devoluciones-pendientes'):
            for quien, cliente in (('administrador', self.admin), ('coordinador', self.coord)):
                self.assertEqual(cliente.get(ruta).status_code, 200, f'{quien} {ruta}')
        propuesta = self.admin.get(f'/eventos/{evento}/propuestas').json()['propuestas'][0]
        self.assertEqual((propuesta['estado'], propuesta['servicios'], propuesta['costoTotal']), ('Aceptada', ['Banquete'], '10000.00'))
        self.assertEqual(self.admin.get(f'/eventos/{evento}/administracion').json()['contratos'][0]['contratoId'], contrato)
        prov = self.cliente(PROVEEDOR, proveedor_id=self.proveedor('Proveedor Uno'))
        self.assertEqual(prov.get(f'/eventos/{evento}/propuestas').status_code, 403)
        self.assertEqual(prov.get(f'/eventos/{evento}/pagos').status_code, 403)

    def test_s9_no_existe_superusuario_ningun_rol_tiene_todos_los_permisos(self):
        todos = {p for permisos in MATRIZ.values() for p in permisos}
        for rol in ROLES:
            self.assertNotEqual(permisos_del_rol(rol), todos, rol)
        self.assertEqual(permisos_del_rol(ADMINISTRADOR) & permisos_del_rol(COORDINADOR),
                         {'eventos.consultar', 'pagos.consultar', 'proveedores.consultar', 'proveedores.registrar'})         # lo único compartido
        self.assertFalse(any('super' in p or 'todo' in p for p in todos))


class DecisionesEnMemoria(Decisiones, Apoyo, unittest.TestCase):
    def crear_contenedor(self):
        return construir()

    def salidas_pendientes(self):
        return 0


class DecisionesEnPostgreSQL(Decisiones, Apoyo, BaseConBD):
    def setUp(self):
        BaseConBD.setUp(self)
        Apoyo.setUp(self)

    def crear_contenedor(self):
        return construir_persistente(motor=self.motor)

    def salidas_pendientes(self):
        return 0

    def test_s5_la_procedencia_de_la_respuesta_queda_en_postgresql_y_sobrevive_a_un_reinicio(self):
        pv, evento, ruta = self.servicio_pendiente()
        self.assertEqual(self.coord.post(ruta, {'proveedor_id': pv, 'disponible': True, 'medio': 'Correo electrónico'}).status_code, 200)
        with self.motor.connect() as con:
            fila = con.execute(sa.text('select respuesta_disponible, respuesta_origen, respuesta_medio, respuesta_registrada_por_nombre, respuesta_fecha '
                                       'from evento_servicio_contratado where evento_id = :e'), {'e': evento}).one()
        self.assertEqual((fila[0], fila[1], fila[2], fila[3]), (True, 'Coordinación', 'Correo electrónico', 'Persona coordinador'))
        self.assertIsNotNone(fila[4])
        reiniciado = construir_persistente(motor=self.motor)
        from application.cqrs import ConsultarInformacionAdministrativaEventoQuery
        info = reiniciado.queries.info_administrativa.handle(ConsultarInformacionAdministrativaEventoQuery(evento))
        self.assertEqual(info.proveedores[0]['respuesta']['origen'], 'Coordinación')

    def test_s5_postgresql_rechaza_una_procedencia_incoherente(self):
        pv, evento, ruta = self.servicio_pendiente()
        self.assertEqual(self.coord.post(ruta, {'proveedor_id': pv, 'disponible': True, 'medio': 'Otro'}).status_code, 200)
        for cambio in ("respuesta_medio = NULL", "respuesta_origen = 'Proveedor'", "respuesta_origen = 'Inventado'", "respuesta_registrada_por_id = NULL"):
            with self.assertRaises(sa.exc.IntegrityError, msg=cambio):
                with self.motor.begin() as con:
                    con.execute(sa.text(f'update evento_servicio_contratado set {cambio} where evento_id = :e'), {'e': evento})

    def test_s4_la_informacion_financiera_que_ve_coordinacion_coincide_con_postgresql(self):
        evento, _ = self.evento_en_organizacion()
        ec = self.estado_de_cuenta(evento)
        saldo = next(o for o in self.admin.get('/pagos-pendientes', params={'evento_id': evento}).json()['pagos'] if o['concepto'] == 'SaldoContratoOriginal')
        for i, importe in enumerate(('1000.00', '500.00')):
            self.assertEqual(self.admin.post(f"/estados-cuenta/{ec['estadoCuentaId']}/pagos", {'obligacion_id': saldo['obligacionId'], 'importe': importe, 'fecha': T0.isoformat(),
                                                                                           'comprobante': f'C-{i}', 'verificar_ahora': i == 0}).status_code, 201)
        vista = self.estado_de_cuenta(evento)['saldoContratoOriginal']
        with self.motor.connect() as con:
            importe = con.execute(sa.text("select importe from obligacion_pago where obligacion_id = :o"), {'o': saldo['obligacionId']}).scalar()
            verificado = con.execute(sa.text("select coalesce(sum(importe), 0) from pago where obligacion_id = :o and estado = 'VERIFICADO'"), {'o': saldo['obligacionId']}).scalar()
            registrado = con.execute(sa.text("select coalesce(sum(importe), 0) from pago where obligacion_id = :o and estado = 'REGISTRADO'"), {'o': saldo['obligacionId']}).scalar()
        self.assertEqual((vista['importe'], vista['pagado'], vista['registradoSinVerificar'], vista['saldo']),
                         (str(importe), str(verificado), str(registrado), str(importe - verificado)))


if __name__ == '__main__':
    unittest.main()
