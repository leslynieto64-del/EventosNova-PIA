"""Esquemas de entrada de las operaciones de la API (contratación, pagos, eventos, solicitudes y consultas).

Igual que `esquemas.py`: validan la FORMA y el TIPO del dato (campos presentes, sin campos desconocidos, números que son números,
booleanos que son booleanos, fechas sin zona). Las reglas de negocio (importe no negativo, datos completos, estados permitidos...)
las aplica el dominio al construir sus objetos de valor o el servicio de aplicación. Los importes son `Decimal` finito (nunca
`float`) y no se fija ningún máximo ni escala: no existe una regla aprobada que lo haga."""
from __future__ import annotations
from decimal import Decimal
from typing import Annotated, Dict, List, Literal, Optional
from pydantic import Field, NaiveDatetime, StrictBool
from domain.valores import (CondicionesServicio, ConceptoPago, Decision, Importe, ResultadoViabilidad)
from .esquemas import DatosEventoEntrada, _Esquema

Dinero = Annotated[Decimal, Field(allow_inf_nan=False)]


def importe(valor: Optional[Decimal]) -> Optional[Importe]:
    return None if valor is None else Importe(valor)


# ---------------------------------------------------------------- propuestas y contratación
class AceptarPropuestaEntrada(_Esquema):
    version_id: str = Field(examples=["PR-1a2b3c4d-v1"])


class CierreNoAceptacionEntrada(_Esquema):
    motivo: str = Field(examples=["El Cliente no respondió"])


class PrepararContratoEntrada(_Esquema):
    politica_incluida: StrictBool = Field(examples=[True])


class FechaEntrada(_Esquema):
    """Fecha y hora (sin zona) del hecho que se registra."""
    fecha: NaiveDatetime = Field(examples=["2026-10-05T10:00:00"])


class SeguimientoAnticipoEntrada(_Esquema):
    fecha: NaiveDatetime = Field(examples=["2026-10-09T10:00:00"])
    resultado_contacto: str = Field(examples=["Se contactó al Cliente"])
    sin_pago_tras_seguimiento: StrictBool = Field(examples=[False])


# ---------------------------------------------------------------- pagos y cuenta
class PagoEntrada(_Esquema):
    obligacion_id: str = Field(examples=["OB-1a2b3c4d"])
    importe: Dinero = Field(examples=["3000.00"])
    fecha: NaiveDatetime = Field(description="Cuándo el Cliente efectuó el pago (según el comprobante).", examples=["2026-10-05T10:00:00"])
    comprobante: str = Field(examples=["C-0001"])
    registrado_en: Optional[NaiveDatetime] = Field(default=None, description="Cuándo Administración lo registra; por omisión, la fecha del pago.")
    verificar_ahora: StrictBool = Field(default=True, description="Si es falso, el pago queda Registrado y se verifica después.")


class VerificacionPagoEntrada(_Esquema):
    verificado_en: NaiveDatetime = Field(examples=["2026-10-06T09:00:00"])


class ProtocoloCobroEntrada(_Esquema):
    importe_moratorio: Dinero = Field(examples=["200.00"])
    comunicado_en: NaiveDatetime
    seguimiento: str = Field(examples=["Recordatorio amistoso"])


class RegularizacionEntrada(_Esquema):
    revisado_en: NaiveDatetime


class DevolucionEntrada(_Esquema):
    comprobante: Optional[str] = Field(default=None, min_length=1, description=(
        "Comprobante de la devolución que Administración efectuó fuera del sistema (CA-098). Si se omite, se usa el ejecutor de "
        "devoluciones simulado."), examples=["TRANSF-0001"])


class SolicitudPagoServicioAdicionalEntrada(_Esquema):
    concepto: ConceptoPago = Field(examples=["ServicioAdicional"])
    importe: Dinero = Field(examples=["800.00"])
    comunicado_en: NaiveDatetime


class SolicitudPagoCambioEntrada(_Esquema):
    comunicado_en: NaiveDatetime


class ImporteAdicionalSustitucionEntrada(_Esquema):
    importe: Dinero = Field(examples=["250.75"])


# ---------------------------------------------------------------- eventos
class CancelacionEntrada(_Esquema):
    motivo: str = Field(examples=["El Cliente canceló"])


class CancelacionFaltaRegularizacionEntrada(_Esquema):
    """S-3. Con la autenticación activa el servidor ignora `coordinador` y `fecha`: registra la cuenta de la sesión y su propio reloj, para que
    nadie pueda atribuir la cancelación a otra persona ni fechar el registro a su conveniencia. Solo con la autenticación desactivada (pruebas
    y desarrollo local) se usan los valores enviados."""
    motivo: str = Field(examples=["Saldo vencido sin regularizar"])
    coordinador: Optional[str] = Field(default=None, examples=["Coordinador"])
    fecha: Optional[NaiveDatetime] = None


class RevisionAdministrativaEntrada(_Esquema):
    resultado: str = Field(examples=["Sin reembolso (política de no reembolso)"])
    fecha: NaiveDatetime


class AsignarProveedorEntrada(_Esquema):
    proveedor_id: str = Field(examples=["PV-1"])


class RespuestaProveedorEntrada(_Esquema):
    """El proveedor responde desde su cuenta (sin `medio`). Coordinación registra lo que el proveedor le comunicó e INDICA el medio (S-5).
    El origen de la respuesta y la cuenta que la registra los decide el servidor a partir de la sesión, nunca este cuerpo."""
    proveedor_id: str = Field(examples=["PV-1"])
    disponible: StrictBool
    medio: Optional[Literal["Llamada telefónica", "Mensaje (WhatsApp o SMS)", "Correo electrónico", "Otro"]] = Field(
        default=None, description="Solo Coordinación: medio por el que el proveedor comunicó su respuesta.")


# ---------------------------------------------------------------- solicitudes
class DecisionEntrada(_Esquema):
    """Decisión del Cliente o de Administración (`Decision`)."""
    actor: str = Field(examples=["Cliente"])
    aprobada: StrictBool
    fecha: NaiveDatetime
    motivo: str = ""

    def a_dominio(self) -> Decision:
        return Decision(self.actor, self.aprobada, self.fecha, self.motivo)


class AnexoEntrada(_Esquema):
    descripcion: str = Field(examples=["Cambio de hora"])


class SolicitudCambioEntrada(_Esquema):
    evento_id: str
    contrato_id: str
    descripcion: str = Field(examples=["Cambiar la hora"])
    tarifa_vigente: Dinero = Field(description="Tarifa vigente del cargo por cambio tardío (BN-003).", examples=["500.00"])
    datos_propuestos: Optional[DatosEventoEntrada] = None
    condiciones_propuestas: Optional[Dict[str, str]] = Field(
        default=None, description="servicioContratadoId → descripción de las nuevas condiciones.")


class ViabilidadEntrada(_Esquema):
    viable: StrictBool
    motivo: str = ""
    costo_adicional_proveedor: Optional[Dinero] = None
    condiciones_proveedor: Optional[str] = Field(default=None, max_length=1000, description="D-P3: condiciones especiales que comunicó el proveedor. Opcional: vacío si no hay condiciones adicionales.")

    def resultado(self) -> ResultadoViabilidad:
        return ResultadoViabilidad(self.viable, self.motivo)


class SolicitudServicioAdicionalEntrada(_Esquema):
    evento_id: str
    contrato_id: str
    servicio: str = Field(examples=["Foto"])


class DisponibilidadEntrada(_Esquema):
    """D-P3: lo que el proveedor comunicó a Coordinación. Con `disponible` verdadero, `proveedor_id` (del catálogo: registrado, activo y que
    ofrece el servicio), `costo` (mayor que cero) y `condiciones` son obligatorios; con `disponible` falso no se envía nada más."""
    disponible: StrictBool
    proveedor_id: Optional[str] = Field(default=None, max_length=100, examples=["PV-1a2b3c4d"])
    costo: Optional[Dinero] = Field(default=None, examples=["800.00"])
    condiciones: Optional[str] = Field(default=None, max_length=1000, examples=["DJ 4 horas con equipo de sonido"])


class DecisionEsperaEntrada(_Esquema):
    acepta_esperar: StrictBool


class SustitucionEntrada(_Esquema):
    evento_id: str
    servicio_contratado_id: str
    contrato_id: str


class AlternativaEntrada(_Esquema):
    proveedor_id: str = Field(min_length=1, max_length=100, description="D-P3: proveedor alternativo del catálogo (registrado, activo, que ofrece el servicio y distinto del original).", examples=["PV-1a2b3c4d"])
    condiciones_alternativa: str = Field(max_length=1000, examples=["Condiciones del reemplazo"])
    costo_adicional: Optional[Dinero] = None

    def condiciones(self) -> CondicionesServicio:
        return CondicionesServicio(self.condiciones_alternativa)
