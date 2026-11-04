"""Adaptadores simulados de colaboradores externos (solo para revisar la arquitectura)."""
from __future__ import annotations
import json
import os
from decimal import Decimal
from typing import List
from application.puertos import (IConsultaDisponibilidadProveedor, INotificadorParticipantes, IVerificadorPagos,
                                 IEjecutorDevoluciones)
from domain.valores import CondicionesServicio, DisponibilidadProveedor, Importe


class ConsultaDisponibilidadSimulada(IConsultaDisponibilidadProveedor):
    def __init__(self, respuestas: List[DisponibilidadProveedor] = None):
        self.respuestas = respuestas or []

    def consultar(self, servicio, fecha_evento, proveedores_actuales):
        return list(self.respuestas)


class NotificadorEnMemoria(INotificadorParticipantes):
    def __init__(self):
        self.enviados = []

    def notificar(self, destinatarios, asunto, detalle):
        self.enviados.append((tuple(destinatarios), asunto, detalle))


class VerificadorPagosSimulado(IVerificadorPagos):
    def verificar(self, comprobante, importe):
        return bool(comprobante)


class EjecutorDevolucionesSimulado(IEjecutorDevoluciones):
    def __init__(self):
        self.ejecutadas = {}

    def ejecutar(self, devolucion_id, importe, referencia_idempotente):
        return self.ejecutadas.setdefault(referencia_idempotente, f"COMP-{devolucion_id}")


class ConsultaDisponibilidadDesdeArchivo(IConsultaDisponibilidadProveedor):
    """SIMULACIÓN CONFIGURABLE de la disponibilidad de proveedores: lee un JSON {servicio: [{proveedor_id, disponible, costo?,
    condiciones?}]}. Eventos Nova no tiene una fuente real de disponibilidad especificada (el BRD solo pide que el Coordinador pueda
    consultarla); sin ella, la API no podría asignar ningún proveedor. La fecha del evento y los proveedores actuales no se usan:
    el archivo es una demostración, no un calendario. SOLO PARA PRUEBAS AUTOMATIZADAS (D-P3): se inyecta en código, nunca por entorno."""
    def __init__(self, ruta: str):
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        self._por_servicio = {}
        for servicio, filas in datos.items():
            if servicio.startswith("_"):
                continue                                    # comentarios del archivo
            self._por_servicio[servicio] = [
                DisponibilidadProveedor(f["proveedor_id"], bool(f["disponible"]),
                                        Importe(Decimal(str(f["costo"]))) if f.get("costo") is not None else None,
                                        CondicionesServicio(f["condiciones"]) if f.get("condiciones") else None)
                for f in filas]

    def consultar(self, servicio, fecha_evento, proveedores_actuales):
        return list(self._por_servicio.get(servicio, []))


class ConsultaDisponibilidadDesdeCatalogo(IConsultaDisponibilidadProveedor):
    """Candidatos para la ASIGNACIÓN INICIAL de un proveedor, tomados del catálogo registrado.
    DECISIÓN APROBADA (D-P2): es candidato el proveedor registrado, activo y que ofrece el servicio. El sistema NO comprueba la disponibilidad
    real en la fecha del evento (no hay calendario ni integración): `fecha_evento` se recibe pero se ignora a propósito, y la disponibilidad
    se confirma después con la respuesta del proveedor a la asignación. No aporta costo ni condiciones (no se inventan tarifas), por eso
    solo se usa en la asignación inicial y no en cambios, servicios adicionales ni sustituciones, que sí necesitan costo."""
    def __init__(self, proveedores):
        self._proveedores = proveedores

    def consultar(self, servicio, fecha_evento, proveedores_actuales):
        return [DisponibilidadProveedor(p.proveedor_id, True) for p in self._proveedores.listar_todos() if p.activo and p.ofrece(servicio)]


class ConsultaDisponibilidadCombinada(IConsultaDisponibilidadProveedor):
    """Une varias fuentes de disponibilidad; si un proveedor figura en más de una, prevalece la primera."""
    def __init__(self, *fuentes):
        self._fuentes = fuentes

    def consultar(self, servicio, fecha_evento, proveedores_actuales):
        vistos, resultado = set(), []
        for fuente in self._fuentes:
            for d in fuente.consultar(servicio, fecha_evento, proveedores_actuales):
                if d.proveedor_id not in vistos:
                    vistos.add(d.proveedor_id); resultado.append(d)
        return resultado


def disponibilidad_desde_entorno():
    """D-P3 (aprobada 01/11/2026): la fuente simulada o de archivo existe SOLO para las pruebas automatizadas y se inyecta en código
    (`construir(ConsultaDisponibilidadDesdeArchivo(ruta))`). Ya NO se activa por entorno: si `EVENTOSNOVA_DISPONIBILIDAD_ARCHIVO` está
    definida, la aplicación se niega a arrancar para que nadie la deje activa por accidente. Sin la variable devuelve None (sin fuente):
    los candidatos salen del catálogo real y los costos y condiciones se capturan a mano."""
    if os.environ.get("EVENTOSNOVA_DISPONIBILIDAD_ARCHIVO", "").strip():
        raise RuntimeError("EVENTOSNOVA_DISPONIBILIDAD_ARCHIVO ya no es compatible: la fuente simulada de disponibilidad es solo para pruebas "
                           "automatizadas y no puede activarse por entorno. Elimine la variable (decisión D-P3).")
    return None
