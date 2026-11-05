"""CQRS básico (Etapa 6): los Command Handlers delegan en la Service Layer; los Query Handlers solo leen."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from domain.valores import (ContenidoPropuesta, EstadoPago, ConceptoPago, EstadoObligacionPago, ErrorDominio,
                            EstadoSolicitudCambio, EstadoSolicitudServicioAdicional, EstadoSustitucionProveedor,
                            EstadoServicioContratado)
from .puertos import (IEstadoCuentaRepository, ISolicitudCambioRepository, ISolicitudServicioAdicionalRepository,
                      ISustitucionProveedorRepository, IEventoRepository, IContratoRepository, IPropuestaRepository)


# ------------------------------------------------------------------ Commands
@dataclass(frozen=True)
class GenerarNuevaVersionPropuestaCommand:
    propuesta_id: str
    modificaciones: ContenidoPropuesta


@dataclass(frozen=True)
class ConfirmarCambioCommand:
    solicitud_id: str


@dataclass(frozen=True)
class DarSeguimientoAnticipoPendienteCommand:
    contrato_id: str
    fecha: datetime
    resultado_contacto: str
    sin_pago_tras_seguimiento: bool


@dataclass(frozen=True)
class RegistrarCancelacionPorFaltaDeRegularizacionCommand:
    evento_id: str
    motivo: str
    coordinador: str
    fecha: datetime


class RegistrarCancelacionPorFaltaDeRegularizacionHandler:
    """Intención explícita del Coordinador; distinta del cierre por anticipo no recibido."""
    def __init__(self, servicio):           # GestionCierreEventoService
        self.servicio = servicio
    def handle(self, cmd: RegistrarCancelacionPorFaltaDeRegularizacionCommand):
        return self.servicio.registrar_cancelacion_por_falta_de_regularizacion(cmd.evento_id, cmd.motivo, cmd.coordinador, cmd.fecha)


class GenerarNuevaVersionPropuestaHandler:
    def __init__(self, servicio):           # GestionPropuestaService
        self.servicio = servicio
    def handle(self, cmd: GenerarNuevaVersionPropuestaCommand, ahora: datetime):
        return self.servicio.generar_nueva_version(cmd.propuesta_id, cmd.modificaciones, ahora)


class ConfirmarCambioHandler:
    def __init__(self, servicio):           # GestionCambiosEventoService
        self.servicio = servicio
    def handle(self, cmd: ConfirmarCambioCommand, ahora: datetime):
        return self.servicio.confirmar_cambio(cmd.solicitud_id, ahora)


class DarSeguimientoAnticipoPendienteHandler:
    def __init__(self, servicio):           # FormalizarContratacionService
        self.servicio = servicio
    def handle(self, cmd: DarSeguimientoAnticipoPendienteCommand):
        return self.servicio.dar_seguimiento_anticipo_pendiente(cmd.contrato_id, cmd.fecha, cmd.resultado_contacto,
                                                                cmd.sin_pago_tras_seguimiento)


# ------------------------------------------------------------------ View Models
@dataclass
class EstadoCuentaResumenViewModel:
    estadoCuentaId: str
    contratoId: str
    anticipo: dict
    pagosRegistrados: List[dict]
    saldoContratoOriginal: dict
    obligacionesAdicionales: List[dict]
    devoluciones: List[dict] = field(default_factory=list)      # H-09: cada una con su fecha límite (SE-012)


@dataclass
class EstadoPagosViewModel:
    eventoId: str
    estadosCuenta: List[EstadoCuentaResumenViewModel] = field(default_factory=list)


@dataclass
class SolicitudPendienteViewModel:
    tipoSolicitud: str
    solicitudId: str
    servicioAfectado: Optional[str]
    estadoActual: str
    accionPendiente: str
    estadoPago: Optional[str]                     # estado de la primera obligación de la solicitud (compatibilidad)
    obligaciones: List[dict] = field(default_factory=list)   # E3G: cada concepto con su importe y estado, por separado


@dataclass
class SolicitudesPendientesViewModel:
    eventoId: str
    solicitudes: List[SolicitudPendienteViewModel] = field(default_factory=list)


# ------------------------------------------------------------------ Queries
@dataclass(frozen=True)
class ConsultarEstadoPagosQuery:
    eventoId: str
    ahora: Optional[datetime] = None       # con reloj, cada obligación informa si su plazo ya venció (CA-023)


@dataclass(frozen=True)
class ConsultarSolicitudesPendientesQuery:
    eventoId: str


def _cobertura(ec, o) -> dict:
    """Cuánto cubre cada obligación: solo cuentan los pagos Verificados; un pago Registrado aún sin verificar se informa aparte."""
    pagado = ec.importe_pagado(o.obligacion_id)
    sin_verificar = sum((p.importe.cantidad for p in ec.pagos
                         if p.obligacion_id == o.obligacion_id and p.estado == EstadoPago.REGISTRADO), Decimal(0))
    return {"obligacionId": o.obligacion_id, "pagado": str(pagado), "registradoSinVerificar": str(sin_verificar),
            "saldo": str(max(o.importe.cantidad - pagado, Decimal(0)))}


class ConsultarEstadoPagosHandler:
    """No escribe ni usa IUnitOfWork; no presupone un único EstadoCuenta por evento."""
    def __init__(self, estados_cuenta: IEstadoCuentaRepository):
        self.ec = estados_cuenta

    def handle(self, q: ConsultarEstadoPagosQuery) -> EstadoPagosViewModel:
        vm = EstadoPagosViewModel(q.eventoId)
        for ec in self.ec.listar_por_evento_id(q.eventoId):
            def ob(concepto):
                o = next((o for o in ec.obligaciones.values() if o.concepto == concepto), None)
                if o is None:
                    return {}
                datos = {"importe": str(o.importe.cantidad), "fechaLimite": o.plazo.vence.isoformat() if o.plazo else None, "estado": o.estado.value}
                datos.update(_cobertura(ec, o))
                if q.ahora is not None:       # CA-023: «si el plazo ya venció», aunque el vencimiento aún no se haya registrado
                    datos["plazoVencido"] = bool(o.plazo is not None and o.estado in (EstadoObligacionPago.PENDIENTE, EstadoObligacionPago.VENCIDA)
                                                 and o.plazo.vencido(q.ahora))
                return datos
            adicionales = [{"concepto": o.concepto.value, "importe": str(o.importe.cantidad), "plazo": o.plazo.vence.isoformat() if o.plazo else None,
                            "estado": o.estado.value, "origenId": o.origen_id, **_cobertura(ec, o)} for o in ec.obligaciones.values()
                           if o.concepto not in (ConceptoPago.ANTICIPO, ConceptoPago.SALDO_CONTRATO_ORIGINAL)]
            pagos = [{"concepto": ec.obligaciones[p.obligacion_id].concepto.value, "importe": str(p.importe.cantidad),
                      "fecha": p.fecha.isoformat(), "estado": p.estado.value,
                      "registradoEn": p.registrado_en.isoformat() if p.registrado_en else None,
                      "verificadoEn": p.verificado_en.isoformat() if p.verificado_en else None} for p in ec.pagos]
            saldo = ob(ConceptoPago.SALDO_CONTRATO_ORIGINAL)
            if ec.resultado_regularizacion:
                saldo["resultadoRegularizacion"] = ec.resultado_regularizacion
            devoluciones = [{"devolucionId": d.devolucion_id, "solicitudId": d.solicitud_id, "concepto": d.concepto.value,
                             "importe": str(d.importe.cantidad), "estado": d.estado.value,
                             "fechaCierre": d.fecha_cierre.isoformat(), "fechaLimite": d.fecha_limite.isoformat(),
                             "fechaDevolucion": d.fecha_devolucion.isoformat() if d.fecha_devolucion else None,
                             "comprobante": d.comprobante, "enPlazo": d.en_plazo, "tipo": d.tipo.value, "pagoId": d.pago_id}
                             for d in ec.devoluciones]
            vm.estadosCuenta.append(EstadoCuentaResumenViewModel(ec.id, ec.contrato_id, ob(ConceptoPago.ANTICIPO), pagos,
                                                                 saldo, adicionales, devoluciones))
        return vm


ACCION = {
    "Registrada": "evaluación", "Detenida por saldo vencido": "regularización del saldo", "En evaluación": "evaluación",
    "En búsqueda de proveedor": "evaluación", "En búsqueda de alternativa": "evaluación",
    "Pendiente de aprobación del Cliente": "aprobación", "Pendiente de autorización": "autorización",
    "Pendiente de formalización": "formalización", "Autorizada": "formalización", "Pendiente de pago": "pago pendiente",
}


class ConsultarSolicitudesPendientesHandler:
    """Solo lectura. Los datos financieros del contrato permanecen en EstadoPagosViewModel (H-06)."""
    def __init__(self, cambios: ISolicitudCambioRepository, adicionales: ISolicitudServicioAdicionalRepository,
                 sustituciones: ISustitucionProveedorRepository, estados_cuenta: IEstadoCuentaRepository):
        self.cambios, self.adicionales, self.sustituciones, self.ec = cambios, adicionales, sustituciones, estados_cuenta

    def _obligaciones(self, s) -> List[dict]:
        """Una entrada por concepto de pago de la solicitud (un cambio puede tener costo del proveedor y cargo tardío)."""
        if not s.obligacion_pago_id:
            return []
        ec = self.ec.obtener_por_id(s.estado_cuenta_id)
        return [{"concepto": o.concepto.value, "importe": str(o.importe.cantidad), "estado": o.estado.value}
                for o in ec.obligaciones_de(s.id)]

    def handle(self, q: ConsultarSolicitudesPendientesQuery) -> SolicitudesPendientesViewModel:
        vm = SolicitudesPendientesViewModel(q.eventoId)
        for tipo, repo, servicio in (("cambio", self.cambios, lambda s: None),
                                     ("servicio adicional", self.adicionales, lambda s: s.servicio),
                                     ("sustitución de proveedor", self.sustituciones, lambda s: s.servicio_contratado_id)):
            for s in repo.listar_pendientes_por_evento_id(q.eventoId):
                obligaciones = self._obligaciones(s)
                vm.solicitudes.append(SolicitudPendienteViewModel(
                    tipo, s.id, servicio(s), s.estado.value, ACCION.get(s.estado.value, "seguimiento"),
                    obligaciones[0]["estado"] if obligaciones else None, obligaciones))
        return vm


# ------------------------------------------------------------------ Consulta del Proveedor (US-015, CA-033, CA-034)
@dataclass(frozen=True)
class ConsultarServicioAsignadoQuery:
    proveedorId: str
    eventoId: str


@dataclass
class ServicioAsignadoViewModel:
    servicioContratadoId: str
    servicio: str
    estado: str                     # situación del proveedor respecto del servicio
    respuesta: Optional[dict] = None   # S-5: la respuesta y su procedencia (None mientras el proveedor no haya respondido)


def _respuesta_dict(sc) -> Optional[dict]:
    """S-5: la respuesta de disponibilidad de un servicio y quién la registró (directa del proveedor o capturada por Coordinación)."""
    r = getattr(sc, "respuesta", None)
    if r is None:
        return None
    return {"disponible": r.disponible, "origen": r.origen, "medio": r.medio, "registradoPor": r.registrado_por_nombre,
            "registradoPorId": r.registrado_por_id, "fecha": r.fecha.isoformat()}


@dataclass
class InformacionEventoProveedorViewModel:
    eventoId: str
    tipoEvento: str
    fecha: str
    hora: str
    lugar: str
    invitadosAproximados: int
    servicios: List[ServicioAsignadoViewModel] = field(default_factory=list)
    estadoEvento: str = ""


class ConsultarServicioAsignadoHandler:
    """Solo lectura. El Proveedor ve los datos del Evento y únicamente los servicios que tiene asignados (BN-007). Si el
    evento no existe o el proveedor no tiene servicios asignados en él, devuelve None: no revela datos del evento."""
    def __init__(self, eventos: IEventoRepository):
        self.eventos = eventos

    def handle(self, q: ConsultarServicioAsignadoQuery) -> Optional[InformacionEventoProveedorViewModel]:
        ev = self.eventos.obtener_por_id(q.eventoId)
        if ev is None:
            return None
        propios = [s for s in ev.servicios.values() if s.proveedor_id == q.proveedorId]
        if not propios:
            return None
        d = ev.datos
        return InformacionEventoProveedorViewModel(
            ev.id, d.tipo, d.fecha_hora.date().isoformat(), d.fecha_hora.strftime("%H:%M"), d.lugar, d.invitados_aproximados,
            [ServicioAsignadoViewModel(s.servicio_contratado_id, s.servicio, s.estado.value, _respuesta_dict(s))
             for s in propios], ev.estado.value)


@dataclass(frozen=True)
class ConsultarPropuestasEventoQuery:
    eventoId: str


@dataclass
class PropuestaViewModel:
    propuestaId: str
    estado: str
    versionVigenteId: str
    numeroVersion: int
    servicios: List[str]
    proveedoresConsiderados: List[str]
    costoTotal: str
    condiciones: str
    motivoCierre: Optional[str] = None


@dataclass
class PropuestasEventoViewModel:
    eventoId: str
    propuestas: List[PropuestaViewModel] = field(default_factory=list)


class ConsultarPropuestasEventoHandler:
    """Solo lectura (S-9): las propuestas de un evento con su versión vigente. Devuelve None si el evento no existe."""
    def __init__(self, eventos: IEventoRepository, propuestas: IPropuestaRepository):
        self.eventos, self.propuestas = eventos, propuestas

    def handle(self, q: ConsultarPropuestasEventoQuery) -> Optional[PropuestasEventoViewModel]:
        if self.eventos.obtener_por_id(q.eventoId) is None:
            return None
        vm = PropuestasEventoViewModel(q.eventoId)
        for p in sorted(self.propuestas.listar_por_evento_id(q.eventoId), key=lambda p: p.id):
            v = next(v for v in p.versiones if v.version_id == p.version_vigente_id)
            c = v.contenido
            vm.propuestas.append(PropuestaViewModel(p.id, p.estado.value, v.version_id, v.numero, list(c.servicios), list(c.proveedores_considerados),
                                                    str(c.costo_total.cantidad), c.condiciones, p.motivo_cierre))
        return vm


@dataclass(frozen=True)
class ConsultarMisAsignacionesQuery:
    proveedorId: str


@dataclass
class AsignacionesProveedorViewModel:
    proveedorId: str
    eventos: List[InformacionEventoProveedorViewModel] = field(default_factory=list)


class ConsultarMisAsignacionesHandler:
    """Solo lectura. Todos los eventos donde el proveedor tiene al menos un servicio asignado, con únicamente esos servicios
    (BN-007). La identidad la entrega la API desde la cuenta autenticada; aquí nunca se lee de un dato libre del cliente."""
    def __init__(self, eventos: IEventoRepository):
        self.eventos = eventos

    def handle(self, q: ConsultarMisAsignacionesQuery) -> AsignacionesProveedorViewModel:
        vm = AsignacionesProveedorViewModel(q.proveedorId)
        unico = ConsultarServicioAsignadoHandler(self.eventos)
        for ev in sorted(self.eventos.listar_todos(), key=lambda e: (e.datos.fecha_hora, e.id)):
            if any(s.proveedor_id == q.proveedorId for s in ev.servicios.values()):
                info = unico.handle(ConsultarServicioAsignadoQuery(q.proveedorId, ev.id))
                vm.eventos.append(info)
        return vm


# ------------------------------------------------------------------ Consultas de Administración (US-022, US-012; H-03)
# Todas son de solo lectura: no usan IUnitOfWork, no registran pagos y no ejecutan transiciones. Las solicitudes se
# muestran con sus estados originales; la agrupación de CA-058 («pendientes, autorizadas, rechazadas…») no se define
# aquí porque las fuentes no precisan en qué categoría caen «Pendiente de pago», «No aprobada» ni los cierres.
TIPOS_SOLICITUD = ("cambio", "servicio adicional", "sustitución de proveedor")


@dataclass(frozen=True)
class ConsultarInformacionAdministrativaEventoQuery:
    eventoId: str


@dataclass
class InformacionAdministrativaEventoViewModel:
    eventoId: str
    estadoEvento: str
    tipoEvento: str
    fechaHora: str
    lugar: str
    invitadosAproximados: int
    contratos: List[dict] = field(default_factory=list)                 # contratoId, estado, costoTotal
    pagosRealizados: str = "0"                                          # suma de pagos Verificados de los estados de cuenta
    saldoPendienteContratoOriginal: str = "0"
    estadosCuenta: List[EstadoCuentaResumenViewModel] = field(default_factory=list)   # importes por concepto, por separado
    obligacionesPendientes: List[dict] = field(default_factory=list)
    proveedores: List[dict] = field(default_factory=list)               # servicio, proveedor y estado del servicio
    serviciosSolicitados: List[str] = field(default_factory=list)       # los pedidos al registrar el evento (aún sin proveedor ni contratación)
    cambiosPendientesAutorizacion: List[dict] = field(default_factory=list)
    serviciosAdicionales: List[dict] = field(default_factory=list)      # todos, con su estado original
    solicitudesPendientes: List[SolicitudPendienteViewModel] = field(default_factory=list)


@dataclass(frozen=True)
class ConsultarEventosProximosQuery:
    desde: datetime
    hasta: datetime


@dataclass
class EventoProximoViewModel:
    eventoId: str
    estadoEvento: str
    tipoEvento: str
    fechaHora: str
    lugar: str
    clienteId: str


@dataclass
class EventosProximosViewModel:
    desde: str
    hasta: str
    eventos: List[EventoProximoViewModel] = field(default_factory=list)


@dataclass(frozen=True)
class ConsultarSolicitudesPorEstadoQuery:
    estado: Optional[str] = None           # estado original (p. ej. «Pendiente de autorización»); None = todos
    eventoId: Optional[str] = None         # None = todos los eventos
    tipo: Optional[str] = None             # uno de TIPOS_SOLICITUD; None = los tres


@dataclass
class SolicitudPorEstadoViewModel:
    tipoSolicitud: str
    solicitudId: str
    eventoId: str
    servicioAfectado: Optional[str]
    estadoActual: str
    pendiente: bool
    # D-P3: lo que Coordinación registró de la cotización del proveedor, para que Administración lo revise antes de autorizar. None si aún
    # no se ha registrado nada. Claves: proveedorId (si aplica), costo (texto decimal o None) y condiciones (texto o None).
    datosProveedor: Optional[dict] = None


@dataclass
class SolicitudesPorEstadoViewModel:
    solicitudes: List[SolicitudPorEstadoViewModel] = field(default_factory=list)


@dataclass(frozen=True)
class ConsultarPagosPendientesQuery:
    eventoId: Optional[str] = None         # None = todos los eventos


@dataclass
class PagoPendienteViewModel:
    eventoId: str
    estadoCuentaId: str
    contratoId: str
    obligacionId: str
    concepto: str
    importe: str
    pagado: str
    saldo: str
    fechaLimite: Optional[str]
    estado: str                            # Pendiente o Vencida
    origenId: str


@dataclass
class PagosPendientesViewModel:
    pagos: List[PagoPendienteViewModel] = field(default_factory=list)


@dataclass(frozen=True)
class ConsultarServiciosPendientesConfirmacionQuery:
    eventoId: Optional[str] = None         # None = todos los eventos


@dataclass
class ServicioPendienteViewModel:
    eventoId: str
    estadoEvento: str
    servicioContratadoId: str
    servicio: str
    proveedorId: Optional[str]
    estado: str
    proveedorNombre: Optional[str] = None      # nombre en el catálogo; None si no hay proveedor o su id no figura en el catálogo


@dataclass
class ServiciosPendientesConfirmacionViewModel:
    servicios: List[ServicioPendienteViewModel] = field(default_factory=list)          # sin confirmar por el proveedor
    solicitudes: List[SolicitudPorEstadoViewModel] = field(default_factory=list)       # cambios, adicionales y sustituciones en trámite


def _nombres_de_proveedores(proveedores) -> dict:
    """{proveedor_id: nombre} del catálogo (vacío si no hay catálogo): solo para mostrar nombres legibles; no filtra nada."""
    return {p.proveedor_id: p.nombre for p in proveedores.listar_todos()} if proveedores is not None else {}


def _repo_de(repo, evento_id):
    return repo.listar_por_evento_id(evento_id) if evento_id else repo.listar_todas()


def _servicio_afectado(tipo, s):
    return None if tipo == "cambio" else (s.servicio if tipo == "servicio adicional" else s.servicio_contratado_id)


def _datos_proveedor(tipo, s) -> Optional[dict]:
    """D-P3: costo y condiciones que comunicó el proveedor y registró Coordinación en cada flujo (solo lectura)."""
    if tipo == "cambio":
        if s.costo_proveedor is None and not s.condiciones_proveedor:
            return None
        return {"proveedorId": None, "costo": None if s.costo_proveedor is None else str(s.costo_proveedor.cantidad),
                "condiciones": s.condiciones_proveedor}
    if tipo == "servicio adicional":
        d = s.disponibilidad
        if d is None or not d.disponible:
            return None
        return {"proveedorId": d.proveedor_id, "costo": None if d.costo is None else str(d.costo.cantidad),
                "condiciones": None if d.condiciones is None else d.condiciones.descripcion}
    alt = s.alternativa_vigente
    if alt is None:
        return None
    cond = alt.disponibilidad.condiciones if alt.disponibilidad is not None else None
    return {"proveedorId": alt.proveedor_id, "costo": None if s.costo_adicional is None else str(s.costo_adicional.cantidad),
            "condiciones": None if cond is None else cond.descripcion}


class ConsultarInformacionAdministrativaEventoHandler:
    """Vista integral de un evento para Administración (CA-055 a CA-057). Devuelve None si el evento no existe."""
    def __init__(self, eventos: IEventoRepository, contratos: IContratoRepository, estados_cuenta: IEstadoCuentaRepository,
                 cambios: ISolicitudCambioRepository, adicionales: ISolicitudServicioAdicionalRepository,
                 sustituciones: ISustitucionProveedorRepository, proveedores=None):
        self.proveedores = proveedores
        self.eventos, self.contratos, self.ec = eventos, contratos, estados_cuenta
        self.cambios, self.adicionales = cambios, adicionales
        self._pagos = ConsultarEstadoPagosHandler(estados_cuenta)
        self._pendientes = ConsultarSolicitudesPendientesHandler(cambios, adicionales, sustituciones, estados_cuenta)

    def handle(self, q: ConsultarInformacionAdministrativaEventoQuery) -> Optional[InformacionAdministrativaEventoViewModel]:
        ev = self.eventos.obtener_por_id(q.eventoId)
        if ev is None:
            return None
        d = ev.datos
        vm = InformacionAdministrativaEventoViewModel(ev.id, ev.estado.value, d.tipo, d.fecha_hora.isoformat(), d.lugar,
                                                      d.invitados_aproximados)
        vm.contratos = [{"contratoId": c.id, "estado": c.estado.value, "costoTotal": str(c.condiciones.costo_total.cantidad)}
                        for c in sorted(self.contratos.listar_por_evento_id(q.eventoId), key=lambda c: c.id)]
        estados = sorted(self.ec.listar_por_evento_id(q.eventoId), key=lambda x: x.id)
        vm.pagosRealizados = str(sum((x.pagos_realizados().cantidad for x in estados), Decimal(0)))
        vm.saldoPendienteContratoOriginal = str(sum((x.saldo_pendiente_contrato().cantidad for x in estados), Decimal(0)))
        vm.estadosCuenta = self._pagos.handle(ConsultarEstadoPagosQuery(q.eventoId)).estadosCuenta
        vm.obligacionesPendientes = [
            {"concepto": o.concepto.value, "importe": str(o.importe.cantidad),
             "pagado": str(x.importe_pagado(o.obligacion_id)), "estado": o.estado.value,
             "fechaLimite": o.plazo.vence.isoformat() if o.plazo else None, "origenId": o.origen_id}
            for x in estados for o in x.obligaciones.values()
            if o.estado in (EstadoObligacionPago.PENDIENTE, EstadoObligacionPago.VENCIDA)]
        vm.serviciosSolicitados = list(ev.servicios_solicitados)
        nombres = _nombres_de_proveedores(self.proveedores)
        vm.proveedores = [{"servicioContratadoId": s.servicio_contratado_id, "servicio": s.servicio,
                           "proveedorId": s.proveedor_id, "estado": s.estado.value, "respuesta": _respuesta_dict(s),
                           **({"proveedorNombre": nombres[s.proveedor_id]} if s.proveedor_id in nombres else {})}   # solo si figura en el catálogo
                          for s in sorted(ev.servicios.values(), key=lambda s: s.servicio_contratado_id)]
        vm.cambiosPendientesAutorizacion = [
            {"solicitudId": s.id, "descripcion": s.descripcion}
            for s in sorted(self.cambios.listar_por_evento_id(q.eventoId), key=lambda s: s.id)
            if s.estado == EstadoSolicitudCambio.PENDIENTE_AUTORIZACION]
        vm.serviciosAdicionales = [
            {"solicitudId": s.id, "servicio": s.servicio, "estado": s.estado.value, "pendiente": s.pendiente}
            for s in sorted(self.adicionales.listar_por_evento_id(q.eventoId), key=lambda s: s.id)]
        vm.solicitudesPendientes = self._pendientes.handle(ConsultarSolicitudesPendientesQuery(q.eventoId)).solicitudes
        return vm


class ConsultarEventosProximosHandler:
    """Eventos cuya fecha y hora caen en la ventana [desde, hasta] recibida; no se define aquí qué es «próximo» (D-D).
    Se muestran todos los estados del evento, con su estado, para que Administración decida."""
    def __init__(self, eventos: IEventoRepository):
        self.eventos = eventos

    def handle(self, q: ConsultarEventosProximosQuery) -> EventosProximosViewModel:
        if q.hasta < q.desde:
            raise ErrorDominio("La ventana de fechas no es válida: «hasta» es anterior a «desde».")
        vm = EventosProximosViewModel(q.desde.isoformat(), q.hasta.isoformat())
        for ev in sorted(self.eventos.listar_todos(), key=lambda e: (e.datos.fecha_hora, e.id)):
            if q.desde <= ev.datos.fecha_hora <= q.hasta:
                vm.eventos.append(EventoProximoViewModel(ev.id, ev.estado.value, ev.datos.tipo, ev.datos.fecha_hora.isoformat(),
                                                         ev.datos.lugar, ev.cliente_id))
        return vm


class ConsultarSolicitudesPorEstadoHandler:
    """Solicitudes de cambio, servicio adicional y sustitución filtradas por estado original, evento y tipo."""
    def __init__(self, cambios: ISolicitudCambioRepository, adicionales: ISolicitudServicioAdicionalRepository,
                 sustituciones: ISustitucionProveedorRepository):
        self.repos = (("cambio", cambios), ("servicio adicional", adicionales), ("sustitución de proveedor", sustituciones))

    def handle(self, q: ConsultarSolicitudesPorEstadoQuery) -> SolicitudesPorEstadoViewModel:
        validos = {e.value for enum in (EstadoSolicitudCambio, EstadoSolicitudServicioAdicional, EstadoSustitucionProveedor)
                   for e in enum}
        if q.estado is not None and q.estado not in validos:
            raise ErrorDominio(f"El estado «{q.estado}» no existe en las solicitudes.")
        if q.tipo is not None and q.tipo not in TIPOS_SOLICITUD:
            raise ErrorDominio(f"El tipo de solicitud «{q.tipo}» no existe.")
        vm = SolicitudesPorEstadoViewModel()
        for tipo, repo in self.repos:
            if q.tipo is not None and q.tipo != tipo:
                continue
            for s in sorted(_repo_de(repo, q.eventoId), key=lambda s: s.id):
                if q.estado is None or s.estado.value == q.estado:
                    vm.solicitudes.append(SolicitudPorEstadoViewModel(tipo, s.id, s.evento_id, _servicio_afectado(tipo, s),
                                                                      s.estado.value, s.pendiente, _datos_proveedor(tipo, s)))
        return vm


class ConsultarPagosPendientesHandler:
    """Obligaciones Pendientes o Vencidas de uno o de todos los eventos, cada concepto por separado (CA-058, CA-026)."""
    def __init__(self, estados_cuenta: IEstadoCuentaRepository):
        self.ec = estados_cuenta

    def handle(self, q: ConsultarPagosPendientesQuery) -> PagosPendientesViewModel:
        estados = self.ec.listar_por_evento_id(q.eventoId) if q.eventoId else self.ec.listar_todos()
        filas = []
        for x in estados:
            for o in x.obligaciones.values():
                if o.estado in (EstadoObligacionPago.PENDIENTE, EstadoObligacionPago.VENCIDA):
                    pagado = x.importe_pagado(o.obligacion_id)
                    filas.append(PagoPendienteViewModel(
                        x.evento_id, x.id, x.contrato_id, o.obligacion_id, o.concepto.value, str(o.importe.cantidad),
                        str(pagado), str(max(o.importe.cantidad - pagado, Decimal(0))),
                        o.plazo.vence.isoformat() if o.plazo else None, o.estado.value, o.origen_id))
        filas.sort(key=lambda f: (f.fechaLimite is None, f.fechaLimite or "", f.eventoId, f.obligacionId))
        return PagosPendientesViewModel(filas)


class ConsultarServiciosPendientesConfirmacionHandler:
    """US-012, CA-028: servicios con proveedor sin confirmar y solicitudes aún no confirmadas (GL-036)."""
    def __init__(self, eventos: IEventoRepository, cambios: ISolicitudCambioRepository,
                 adicionales: ISolicitudServicioAdicionalRepository, sustituciones: ISustitucionProveedorRepository,
                 proveedores=None):
        self.eventos, self.proveedores = eventos, proveedores
        self._solicitudes = ConsultarSolicitudesPorEstadoHandler(cambios, adicionales, sustituciones)

    def handle(self, q: ConsultarServiciosPendientesConfirmacionQuery) -> ServiciosPendientesConfirmacionViewModel:
        if q.eventoId:
            ev = self.eventos.obtener_por_id(q.eventoId)
            eventos = [ev] if ev is not None else []
        else:
            eventos = self.eventos.listar_todos()
        vm = ServiciosPendientesConfirmacionViewModel()
        nombres = _nombres_de_proveedores(self.proveedores)
        for ev in sorted(eventos, key=lambda e: e.id):
            for s in sorted(ev.servicios.values(), key=lambda s: s.servicio_contratado_id):
                if s.estado != EstadoServicioContratado.CONFIRMADO:
                    vm.servicios.append(ServicioPendienteViewModel(
                        ev.id, ev.estado.value, s.servicio_contratado_id, s.servicio, s.proveedor_id, s.estado.value,
                        nombres.get(s.proveedor_id)))
        todas = self._solicitudes.handle(ConsultarSolicitudesPorEstadoQuery(eventoId=q.eventoId)).solicitudes
        vm.solicitudes = [s for s in todas if s.pendiente]
        return vm


# ------------------------------------------------------------------ Devoluciones pendientes (H-09, SE-012, CA-098)
@dataclass(frozen=True)
class ConsultarDevolucionesPendientesQuery:
    ahora: datetime                        # el reloj lo entrega quien consulta; la consulta no lo lee
    eventoId: Optional[str] = None         # None = todos los eventos


@dataclass
class DevolucionPendienteViewModel:
    eventoId: str
    estadoCuentaId: str
    devolucionId: str
    solicitudId: Optional[str]             # None en la devolución del anticipo (decisión A): nace de un pago
    concepto: str
    importe: str
    fechaCierre: str
    fechaLimite: str                       # cinco días hábiles: SE-012 desde el cierre; decisión A, desde la fecha de referencia
    vencida: bool                          # sigue pendiente después de su fecha límite
    tipo: str = "SE-012"                   # «SE-012» o «Anticipo de contratación cerrada» (dos devoluciones distintas, A-5)
    pagoId: Optional[str] = None


@dataclass
class DevolucionesPendientesViewModel:
    devoluciones: List[DevolucionPendienteViewModel] = field(default_factory=list)


class ConsultarDevolucionesPendientesHandler:
    """Solo lectura. Devoluciones Pendientes con su fecha límite y si ya vencieron, ordenadas por fecha límite."""
    def __init__(self, estados_cuenta: IEstadoCuentaRepository):
        self.ec = estados_cuenta

    def handle(self, q: ConsultarDevolucionesPendientesQuery) -> DevolucionesPendientesViewModel:
        estados = self.ec.listar_por_evento_id(q.eventoId) if q.eventoId else self.ec.listar_todos()
        filas = [DevolucionPendienteViewModel(x.evento_id, x.id, d.devolucion_id, d.solicitud_id, d.concepto.value,
                                              str(d.importe.cantidad), d.fecha_cierre.isoformat(), d.fecha_limite.isoformat(),
                                              d.vencida(q.ahora), d.tipo.value, d.pago_id)
                 for x in estados for d in x.devoluciones if d.estado.value == "Pendiente"]
        filas.sort(key=lambda f: (f.fechaLimite, f.eventoId, f.devolucionId))
        return DevolucionesPendientesViewModel(filas)
