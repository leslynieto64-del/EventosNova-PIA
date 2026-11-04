"""Decisiones aprobadas por el equipo el 01/11/2026: D-P2 (candidatos, no disponibilidad por fecha), S-7 (inicio automático con respaldo manual
excepcional, finalización y cierre por falta de pago a cargo de Coordinación) y S-8 (Coordinación registra y consulta proveedores; solo
Administración los edita, desactiva y reactiva). Ver docs/architecture/DECISIONES_PROVEEDORES.md y docs/SEGURIDAD_Y_PERMISOS.md.

Se ejecuta con la composición en memoria y con PostgreSQL (base de PRUEBAS aislada), con autenticación activa y llamando directo a la API.
Ejecutar desde la raíz:  python -m unittest tests.test_decisiones_dp2_s7_s8 -v"""
import os, subprocess, sys, tempfile, time, unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
import sqlalchemy as sa                                                                      # noqa: E402
from apoyo_bd import BaseConBD                                                               # noqa: E402
from test_api_operaciones import CONTENIDO, DATOS                                            # noqa: E402
from test_seguridad import CLAVE, Cliente, T0                                                # noqa: E402
from api.dependencias import obtener_reloj                                                   # noqa: E402
from api.main import crear_app                                                               # noqa: E402
from application.seguridad import ADMINISTRADOR, COORDINADOR, PROVEEDOR, ConfiguracionSeguridad, permisos_del_rol   # noqa: E402
from infrastructure.persistencia import configuracion as C                                  # noqa: E402
from infrastructure.composicion import construir                                              # noqa: E402
from infrastructure.persistencia import trabajador_outbox                                    # noqa: E402
from infrastructure.persistencia.composicion_persistente import construir_persistente          # noqa: E402

DIAS = 80
T = T0 + timedelta(days=DIAS)                                    # fecha y hora programadas de los eventos de estas pruebas


class Apoyo:
    """Ayudas comunes (clientes, catálogo y evento En organización); sin pruebas propias."""
    def crear_contenedor(self):                                  # pragma: no cover
        raise NotImplementedError

    def arrancar(self):
        self.contenedor = self.crear_contenedor()
        self.app = crear_app(lambda: self.contenedor, ConfiguracionSeguridad(activa=True))
        self.ahora = T0
        self.app.dependency_overrides[obtener_reloj] = lambda: (lambda: self.ahora)
        self.seg = self.contenedor.servicios.seguridad
        self.seg.reloj = lambda: T0
        self.n = 0
        self.admin, self.coord = self.cliente(ADMINISTRADOR), self.cliente(COORDINADOR)

    def setUp(self):
        self.arrancar()

    def cliente(self, rol, proveedor_id=None):
        self.n += 1
        correo = f'{rol}-{self.n}@ejemplo.mx'
        self.seg.crear_usuario(correo, f'Persona {rol}', rol, CLAVE, proveedor_id)
        c = Cliente(self.app); c.entrar(correo)
        return c

    def proveedor(self, nombre, servicios=('Banquete',), cliente=None):
        r = (cliente or self.coord).post('/proveedores', {'nombre': nombre, 'servicios': list(servicios), 'contacto': ''})
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()['datos']['proveedorId']

    def evento_en_organizacion(self, servicios=('Banquete',), fecha=T):
        """Evento En organización por los flujos reales de la API: propuesta, contrato, política, firma, anticipo verificado."""
        coord, admin = self.coord, self.admin
        r = coord.post('/eventos', {'cliente_id': 'CL-1', 'datos': {**DATOS, 'fecha_hora': fecha.isoformat()}, 'servicios': list(servicios)})
        self.assertEqual(r.status_code, 201, r.text)
        evento = r.json()['evento_id']
        propuesta = coord.post(f'/eventos/{evento}/propuestas', {**CONTENIDO, 'servicios': list(servicios)}).json()['propuesta_id']
        self.assertEqual(coord.post(f'/propuestas/{propuesta}/aceptacion', {'version_id': f'{propuesta}-v1'}).status_code, 200)
        contrato = coord.post(f'/propuestas/{propuesta}/contrato', {'politica_incluida': True}).json()['datos']['contrato_id']
        f = T0.isoformat()
        self.assertEqual(coord.post(f'/contratos/{contrato}/comunicacion-politica-no-reembolso', {'fecha': f}).status_code, 200)
        self.assertEqual(coord.post(f'/contratos/{contrato}/firma', {'fecha': f}).status_code, 200)
        ec = admin.get(f'/eventos/{evento}/pagos').json()['estadosCuenta'][0]['estadoCuentaId']
        ob = next(p for p in admin.get('/pagos-pendientes', params={'evento_id': evento}).json()['pagos'] if p['concepto'] == 'Anticipo')
        pago = admin.post(f'/estados-cuenta/{ec}/pagos', {'obligacion_id': ob['obligacionId'], 'importe': '3000.00', 'fecha': f,
                                                          'comprobante': f'C-{evento}', 'verificar_ahora': True})
        self.assertEqual(pago.status_code, 201, pago.text)
        self.contenedor.despachador.despachar()
        self.assertEqual(self.estado(evento), 'En organización')
        return evento, contrato

    def estado(self, evento):
        return self.admin.get(f'/eventos/{evento}/administracion').json()['estadoEvento']

    def servicios(self, evento):
        return {s['servicio']: s for s in self.coord.get(f'/eventos/{evento}/administracion').json()['proveedores']}


class Base(Apoyo):
    """Pruebas de D-P2, S-7 y S-8."""

    # ======================================================================= D-P2
    def test_dp2_solo_es_candidato_el_proveedor_registrado_activo_que_ofrece_el_servicio(self):
        activo = self.proveedor('Banquetes Activos')
        inactivo = self.proveedor('Banquetes Inactivos')
        otro_servicio = self.proveedor('Fotos Activas', ['Fotografía'])
        self.assertEqual(self.admin.post(f'/proveedores/{inactivo}/desactivacion').status_code, 200)
        evento, _ = self.evento_en_organizacion()
        sid = self.servicios(evento)['Banquete']['servicioContratadoId']
        base = f'/eventos/{evento}/servicios/{sid}'
        r = self.coord.get(f'{base}/disponibilidad')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['datos']['disponibles'], [activo])                         # solo el registrado, activo y que ofrece el servicio
        self.assertIn('la disponibilidad en la fecha la confirma el proveedor', r.json()['mensaje'])   # no se presenta como verificada
        rechazos = {inactivo: 'desactivado', otro_servicio: 'no ofrece el servicio', 'PV-NO-REGISTRADO': 'no está registrado'}
        for proveedor, motivo in rechazos.items():
            rr = self.coord.post(f'{base}/proveedor', {'proveedor_id': proveedor})
            self.assertEqual(rr.status_code, 422, proveedor)
            self.assertIn(motivo, rr.json()['detalle'])
        self.assertEqual(self.servicios(evento)['Banquete']['estado'], 'Sin proveedor asignado')      # los rechazos no cambiaron nada
        self.assertEqual(self.coord.post(f'{base}/proveedor', {'proveedor_id': activo}).status_code, 200)

    def test_dp2_la_disponibilidad_la_confirma_el_proveedor_despues_de_la_asignacion(self):
        pv = self.proveedor('Banquetes Valle')
        evento, _ = self.evento_en_organizacion()
        sid = self.servicios(evento)['Banquete']['servicioContratadoId']
        base = f'/eventos/{evento}/servicios/{sid}'
        self.assertEqual(self.coord.post(f'{base}/proveedor', {'proveedor_id': pv}).status_code, 200)
        self.assertEqual(self.servicios(evento)['Banquete']['estado'], 'Pendiente de confirmación del proveedor')   # candidato ≠ confirmado
        prov = self.cliente(PROVEEDOR, proveedor_id=pv)
        r = prov.post(f'{base}/respuesta-proveedor', {'proveedor_id': pv, 'disponible': True})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.servicios(evento)['Banquete']['estado'], 'Confirmado por el proveedor')

    def test_dp2_el_sistema_no_calcula_disponibilidad_por_fecha(self):
        """Dos eventos el mismo día y a la misma hora pueden asignar al mismo proveedor: el sistema no comprueba compromisos por fecha."""
        pv = self.proveedor('Banquetes Valle')
        for _ in range(2):
            evento, _ = self.evento_en_organizacion()
            sid = self.servicios(evento)['Banquete']['servicioContratadoId']
            self.assertEqual(self.coord.get(f'/eventos/{evento}/servicios/{sid}/disponibilidad').json()['datos']['disponibles'], [pv])
            self.assertEqual(self.coord.post(f'/eventos/{evento}/servicios/{sid}/proveedor', {'proveedor_id': pv}).status_code, 200)

    def test_dp2_un_proveedor_reactivado_vuelve_a_ser_candidato(self):
        pv = self.proveedor('Banquetes Valle')
        evento, _ = self.evento_en_organizacion()
        sid = self.servicios(evento)['Banquete']['servicioContratadoId']
        url = f'/eventos/{evento}/servicios/{sid}/disponibilidad'
        self.admin.post(f'/proveedores/{pv}/desactivacion')
        self.assertEqual(self.coord.get(url).json()['datos']['disponibles'], [])
        self.admin.post(f'/proveedores/{pv}/activacion')
        self.assertEqual(self.coord.get(url).json()['datos']['disponibles'], [pv])

    # ======================================================================= S-8
    def test_s8_permisos_definitivos_del_catalogo(self):
        edicion = {'proveedores.editar'}
        self.assertEqual(edicion & permisos_del_rol(ADMINISTRADOR), edicion)
        self.assertEqual(edicion & permisos_del_rol(COORDINADOR), set())
        self.assertEqual(edicion & permisos_del_rol(PROVEEDOR), set())
        for permiso in ('proveedores.registrar', 'proveedores.consultar'):
            self.assertIn(permiso, permisos_del_rol(ADMINISTRADOR)); self.assertIn(permiso, permisos_del_rol(COORDINADOR))
            self.assertNotIn(permiso, permisos_del_rol(PROVEEDOR))

    def test_s8_administracion_registra_consulta_edita_desactiva_y_reactiva(self):
        pv = self.proveedor('Sonido Nova', ['Música'], cliente=self.admin)                       # registrar
        self.assertEqual(self.admin.get(f'/proveedores/{pv}').json()['datos']['nombre'], 'Sonido Nova')   # consultar
        self.assertEqual(len(self.admin.get('/proveedores').json()['datos']['proveedores']), 1)
        r = self.admin.post(f'/proveedores/{pv}/edicion', {'nombre': 'Sonido Nova Plus', 'servicios': ['Música', 'DJ'], 'contacto': '55 1'})
        self.assertEqual((r.status_code, r.json()['datos']['nombre']), (200, 'Sonido Nova Plus'))   # editar
        self.assertFalse(self.admin.post(f'/proveedores/{pv}/desactivacion').json()['datos']['activo'])    # desactivar
        self.assertTrue(self.admin.post(f'/proveedores/{pv}/activacion').json()['datos']['activo'])        # reactivar

    def test_s8_coordinacion_registra_y_consulta_pero_el_servidor_rechaza_editar_desactivar_y_reactivar(self):
        pv = self.proveedor('Sonido Nova', ['Música'])                                           # Coordinación registra
        self.assertEqual(self.coord.get(f'/proveedores/{pv}').status_code, 200)                  # y consulta
        self.assertEqual(self.coord.get('/proveedores').status_code, 200)
        antes = self.admin.get(f'/proveedores/{pv}').json()['datos']
        for ruta, cuerpo in (('edicion', {'nombre': 'Cambiado', 'servicios': ['X'], 'contacto': ''}), ('desactivacion', {}), ('activacion', {})):
            r = self.coord.post(f'/proveedores/{pv}/{ruta}', cuerpo)
            self.assertEqual((r.status_code, r.json()['tipo']), (403, 'sin_permiso'), ruta)      # directo por API, no solo botones ocultos
        self.assertEqual(self.admin.get(f'/proveedores/{pv}').json()['datos'], antes)            # nada cambió

    def test_s8_el_proveedor_no_administra_el_catalogo(self):
        pv = self.proveedor('Sonido Nova', ['Música'])
        otro = self.proveedor('Otro Proveedor', ['Música'])
        prov = self.cliente(PROVEEDOR, proveedor_id=pv)
        self.assertEqual(prov.post('/proveedores', {'nombre': 'Nuevo', 'servicios': [], 'contacto': ''}).status_code, 403)
        self.assertEqual(prov.get('/proveedores').status_code, 403)
        for destino in (pv, otro):                                                               # ni siquiera el suyo
            for ruta in ('edicion', 'desactivacion', 'activacion'):
                self.assertEqual(prov.post(f'/proveedores/{destino}/{ruta}', {'nombre': 'X', 'servicios': [], 'contacto': ''}).status_code, 403, ruta)

    def test_s8_desactivar_conserva_historial_y_asignaciones_y_excluye_de_nuevas_asignaciones(self):
        pv = self.proveedor('Banquetes Valle', ['Banquete', 'Fotografía'])
        evento, _ = self.evento_en_organizacion(['Banquete', 'Fotografía'])
        s = self.servicios(evento)
        base = lambda nombre: f'/eventos/{evento}/servicios/{s[nombre]["servicioContratadoId"]}'
        self.assertEqual(self.coord.post(f'{base("Banquete")}/proveedor', {'proveedor_id': pv}).status_code, 200)
        self.assertEqual(self.admin.post(f'/proveedores/{pv}/desactivacion').status_code, 200)
        self.assertEqual(self.servicios(evento)['Banquete']['proveedorId'], pv)                  # la asignación existente se conserva
        self.assertEqual(self.servicios(evento)['Banquete']['estado'], 'Pendiente de confirmación del proveedor')
        prov = self.cliente(PROVEEDOR, proveedor_id=pv)                                          # y su cuenta sigue viendo y respondiendo
        self.assertEqual([e['eventoId'] for e in prov.get('/mis-asignaciones').json()['eventos']], [evento])
        self.assertEqual(prov.post(f'{base("Banquete")}/respuesta-proveedor', {'proveedor_id': pv, 'disponible': True}).status_code, 200)
        rechazo = self.coord.post(f'{base("Fotografía")}/proveedor', {'proveedor_id': pv})       # pero no recibe asignaciones nuevas
        self.assertEqual(rechazo.status_code, 422)
        self.assertIn('desactivado', rechazo.json()['detalle'])
        self.assertEqual(self.admin.get(f'/proveedores/{pv}').json()['datos']['nombre'], 'Banquetes Valle')    # el registro no se borró
        self.admin.post(f'/proveedores/{pv}/activacion')
        self.assertEqual(self.coord.post(f'{base("Fotografía")}/proveedor', {'proveedor_id': pv}).status_code, 200)

    # ======================================================================= S-7
    def inicio(self, cliente, evento):
        return cliente.post(f'/eventos/{evento}/inicio')

    def ciclo(self, ahora):
        """Un ciclo real del trabajador (lo mismo que ejecuta el proceso `trabajador_outbox`)."""
        trabajador_outbox.ejecutar(self.contenedor, una_vez=True, reloj=lambda: ahora)

    def test_s7_el_inicio_manual_anticipado_se_rechaza(self):
        evento, _ = self.evento_en_organizacion()
        self.ahora = T - timedelta(seconds=1)
        r = self.inicio(self.coord, evento)
        self.assertEqual(r.status_code, 422, r.text)
        self.assertIn('antes de su fecha y hora', r.json()['detalle'])
        self.assertEqual(self.estado(evento), 'En organización')

    def test_s7_el_trabajador_inicia_a_la_hora_programada_y_no_antes(self):
        evento, _ = self.evento_en_organizacion()
        self.ciclo(T - timedelta(seconds=1))
        self.assertEqual(self.estado(evento), 'En organización')
        self.ciclo(T)                                                                            # límite inclusivo en T
        self.assertEqual(self.estado(evento), 'En ejecución')

    def test_s7_el_inicio_automatico_no_se_duplica_y_el_manual_posterior_se_rechaza(self):
        evento, _ = self.evento_en_organizacion()
        self.ciclo(T)
        inicio = self.contenedor.repos.eventos.obtener_por_id(evento).fecha_inicio
        registros = self.salidas_pendientes()
        self.ciclo(T + timedelta(minutes=5)); self.ciclo(T + timedelta(minutes=10))
        self.ahora = T + timedelta(minutes=15)
        r = self.inicio(self.coord, evento)                                                      # el respaldo manual ya no procede
        self.assertEqual(r.status_code, 422, r.text)
        ev = self.contenedor.repos.eventos.obtener_por_id(evento)
        self.assertEqual((ev.estado.value, ev.fecha_inicio), ('En ejecución', inicio))           # la fecha de inicio no se reescribió
        self.assertEqual(self.salidas_pendientes(), registros)                                   # ni se generaron operaciones nuevas

    def test_s7_el_inicio_manual_excepcional_funciona_si_el_automatico_no_actualizo_el_estado(self):
        evento, _ = self.evento_en_organizacion()
        self.ahora = T + timedelta(hours=1)
        self.assertEqual(self.inicio(self.coord, evento).status_code, 200)
        self.assertEqual(self.estado(evento), 'En ejecución')
        self.ciclo(T + timedelta(hours=2))                                                       # el trabajador posterior no repite nada
        self.assertEqual(self.contenedor.repos.eventos.obtener_por_id(evento).fecha_inicio, T + timedelta(hours=1))

    def test_s7_un_trabajador_que_arranca_despues_recupera_los_eventos_cuya_hora_ya_paso(self):
        evento, _ = self.evento_en_organizacion()
        reiniciado = self.reiniciar_contenedor()                                                 # «reinicio»: contenedor nuevo, mismos datos
        trabajador_outbox.ejecutar(reiniciado, una_vez=True, reloj=lambda: T + timedelta(days=3))
        self.assertEqual(reiniciado.repos.eventos.obtener_por_id(evento).estado.value, 'En ejecución')

    def test_s7_la_finalizacion_la_registra_coordinacion(self):
        evento, _ = self.evento_en_organizacion()
        self.ciclo(T)
        fin = (T + timedelta(hours=5)).isoformat()
        self.assertEqual(self.admin.post(f'/eventos/{evento}/finalizacion', {'fecha': fin}).status_code, 403)
        self.assertEqual(self.cliente(PROVEEDOR, proveedor_id=self.proveedor('P')).post(f'/eventos/{evento}/finalizacion', {'fecha': fin}).status_code, 403)
        self.assertEqual(self.estado(evento), 'En ejecución')
        self.assertEqual(self.coord.post(f'/eventos/{evento}/finalizacion', {'fecha': fin}).status_code, 200)
        self.assertEqual(self.estado(evento), 'Finalizado')

    def test_s7_inicio_finalizacion_y_cierre_por_falta_de_pago_se_rechazan_a_quien_no_es_coordinacion(self):
        evento, contrato = self.evento_en_organizacion()
        prov = self.cliente(PROVEEDOR, proveedor_id=self.proveedor('P'))
        fin = T.isoformat()
        for quien, cliente in (('administrador', self.admin), ('proveedor', prov)):
            for ruta, cuerpo in ((f'/eventos/{evento}/inicio', {}), (f'/eventos/{evento}/finalizacion', {'fecha': fin}),
                                 ('/solicitudes-cambio/SC-X/cierre-por-falta-de-pago', {}),
                                 ('/solicitudes-servicio-adicional/SA-X/cierre-por-falta-de-pago', {})):
                self.assertEqual(cliente.post(ruta, cuerpo).status_code, 403, f'{quien} {ruta}')
        for ruta in ('/solicitudes-cambio/SC-X/cierre-por-falta-de-pago', '/solicitudes-servicio-adicional/SA-X/cierre-por-falta-de-pago'):
            self.assertNotEqual(self.coord.post(ruta, {}).status_code, 403, ruta)                # Coordinación sí está autorizada (404 por no existir)
        self.assertEqual(self.estado(evento), 'En organización')

    def test_s7_cierre_por_falta_de_regularizacion_a_cargo_de_coordinacion_respetando_el_plazo(self):
        evento, contrato = self.evento_en_organizacion()
        coord, admin = self.coord, self.admin
        self.ahora = dia = T0 + timedelta(days=5)
        sc = coord.post('/solicitudes-cambio', {'evento_id': evento, 'contrato_id': contrato, 'descripcion': 'Cambio', 'tarifa_vigente': '500.00'}).json()['datos']['solicitud_id']
        self.assertEqual(coord.post(f'/solicitudes-cambio/{sc}/viabilidad', {'viable': True, 'motivo': '', 'costo_adicional_proveedor': '1000.00'}).status_code, 200)
        decision = lambda actor: {'actor': actor, 'aprobada': True, 'fecha': dia.isoformat(), 'motivo': ''}
        self.assertEqual(coord.post(f'/solicitudes-cambio/{sc}/decision-cliente', decision('Cliente')).status_code, 200)
        self.assertEqual(admin.post(f'/solicitudes-cambio/{sc}/autorizacion', decision('Administración')).status_code, 200)
        self.assertEqual(coord.post(f'/solicitudes-cambio/{sc}/anexo', {'descripcion': 'Anexo'}).status_code, 200)
        self.assertEqual(coord.post(f'/solicitudes-cambio/{sc}/solicitud-pago', {'comunicado_en': dia.isoformat()}).status_code, 200)
        estado = lambda: next(x for x in admin.get('/solicitudes', params={'evento_id': evento}).json()['solicitudes'] if x['solicitudId'] == sc)['estadoActual']
        self.assertEqual(admin.post(f'/solicitudes-cambio/{sc}/cierre-por-falta-de-pago').status_code, 403)    # Administración no cierra
        temprano = coord.post(f'/solicitudes-cambio/{sc}/cierre-por-falta-de-pago')
        self.assertEqual(temprano.status_code, 422, temprano.text)                                 # dentro del plazo no se cierra
        self.assertEqual(estado(), 'Pendiente de pago')
        self.ahora = dia + timedelta(hours=25)
        self.assertEqual(coord.post(f'/solicitudes-cambio/{sc}/cierre-por-falta-de-pago').status_code, 200)
        self.assertEqual(estado(), 'Cerrada por falta de pago')


class DecisionesEnMemoria(Base, unittest.TestCase):
    def crear_contenedor(self):
        return construir()

    def salidas_pendientes(self):
        return len(self.contenedor.repos.eventos.listar_todos())

    def reiniciar_contenedor(self):
        return self.contenedor                                   # en memoria no hay reinicio real; el caso de recuperación se prueba con PostgreSQL


class DecisionesEnPostgreSQL(Base, BaseConBD):
    def setUp(self):
        BaseConBD.setUp(self)
        Base.setUp(self)

    def crear_contenedor(self):
        return construir_persistente(motor=self.motor)

    def salidas_pendientes(self):
        with self.motor.connect() as con:
            return con.execute(sa.text('select count(*) from outbox_evento')).scalar(), con.execute(sa.text('select count(*) from outbox_reaccion')).scalar()

    def reiniciar_contenedor(self):
        return construir_persistente(motor=self.motor)           # contenedor nuevo sobre la misma base: lo que ocurre al reiniciar el trabajador

    def test_s7_el_proceso_real_del_trabajador_inicia_el_evento_cuya_hora_ya_paso_y_un_reinicio_no_lo_duplica(self):
        """Arranca el trabajador TAL COMO lo ejecuta Docker Compose (`python -m infrastructure.persistencia.trabajador_outbox`) contra la base
        de pruebas, con el reloj real de America/Mexico_City. El evento tiene su hora programada en el pasado (como tras una caída del worker)."""
        evento, _ = self.evento_en_organizacion()
        with self.motor.begin() as con:
            con.execute(sa.text('update evento set fecha_hora = :f where evento_id = :e'), {'f': datetime(2026, 1, 1, 12, 0), 'e': evento})
        raiz = os.path.join(os.path.dirname(__file__), '..')
        entorno = {**os.environ, 'DATABASE_URL': C.url_pruebas(), 'PYTHONPATH': os.path.join(raiz, 'src')}
        def consulta():
            with self.motor.connect() as con:
                return tuple(con.execute(sa.text('select estado, fecha_inicio from evento where evento_id = :e'), {'e': evento}).one())

        def arrancar(*args):
            registro = tempfile.TemporaryFile(mode='w+', encoding='utf-8')
            return subprocess.Popen([sys.executable, '-m', 'infrastructure.persistencia.trabajador_outbox', *args], env=entorno, cwd=raiz,
                                    stdout=registro, stderr=subprocess.STDOUT), registro
        proceso, registro = arrancar('--intervalo', '1')
        try:
            limite = time.time() + 60
            while time.time() < limite and consulta()[0] != 'EN_EJECUCION':
                self.assertIsNone(proceso.poll(), 'el trabajador terminó antes de procesar el evento')
                time.sleep(0.5)
        finally:
            proceso.terminate(); proceso.wait(timeout=20)
            registro.seek(0); salida = registro.read(); registro.close()
        estado, inicio = consulta()
        self.assertEqual(estado, 'EN_EJECUCION', salida[-800:])
        self.assertIsNotNone(inicio)
        self.assertIn('Llegada de T', salida)                                                    # el propio trabajador registró la operación
        reinicio, registro2 = arrancar('--una-vez')                                              # «reinicio» del trabajador
        self.assertEqual(reinicio.wait(timeout=60), 0)
        registro2.close()
        self.assertEqual(consulta(), ('EN_EJECUCION', inicio))                                   # nada se repitió ni se reescribió


if __name__ == '__main__':
    unittest.main()
