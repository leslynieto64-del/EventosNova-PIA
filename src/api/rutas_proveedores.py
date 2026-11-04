"""Catálogo de proveedores: registrar, consultar un proveedor y buscar. La asignación de un proveedor a un servicio contratado y su
respuesta están en `rutas_eventos` (BN-004, BN-009). Un proveedor inexistente es 404 (`no_encontrado`), como en las demás consultas."""
from __future__ import annotations
from datetime import datetime
from typing import Callable, List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from pydantic import Field, StringConstraints
from .dependencias import obtener_contenedor, obtener_reloj
from .esquemas import RechazoRespuesta, _Esquema
from .rutas_comunes import OperacionRespuesta, responder

router = APIRouter(tags=["Proveedores (catálogo)"])
_RECHAZO = {422: {"model": RechazoRespuesta, "description": "Rechazo de negocio o entrada no válida"}}
_NO_ENCONTRADO = {404: {"model": RechazoRespuesta, "description": "Proveedor no encontrado"}, **_RECHAZO}


class ProveedorEntrada(_Esquema):
    """Alta de un proveedor. Solo el nombre es obligatorio: el BRD no especifica más atributos."""
    nombre: str = Field(examples=["Banquetes del Valle"], max_length=200)
    servicios: List[Annotated[str, StringConstraints(max_length=100)]] = Field(default_factory=list, max_length=30, examples=[["Banquete", "Música"]],
                                 description="Servicios que ofrece; se usan para proponerlo al asignar un servicio contratado.")
    contacto: str = Field(default="", max_length=300, examples=["55 1234 5678"], description="Texto libre (teléfono, correo...).")


@router.post("/proveedores", status_code=201, response_model=OperacionRespuesta, responses=_RECHAZO,
             summary="Registrar un proveedor en el catálogo")
def registrar_proveedor(entrada: ProveedorEntrada, contenedor=Depends(obtener_contenedor),
                        reloj: Callable[[], datetime] = Depends(obtener_reloj)):
    return responder(contenedor, contenedor.servicios.catalogo.registrar_proveedor(
        entrada.nombre, entrada.servicios, entrada.contacto, reloj()), despachar=False)


@router.get("/proveedores", response_model=OperacionRespuesta, responses=_RECHAZO,
            summary="Consultar y buscar proveedores del catálogo")
def listar_proveedores(q: str = Query(default="", description="Texto a buscar en identificador, nombre, contacto o servicios"),
                       servicio: Optional[str] = Query(default=None, description="Solo los que ofrecen este servicio"),
                       contenedor=Depends(obtener_contenedor)):
    return responder(contenedor, contenedor.servicios.catalogo.listar_proveedores(q, servicio or ""), despachar=False)


@router.get("/proveedores/{proveedor_id}", response_model=OperacionRespuesta, responses=_NO_ENCONTRADO,
            summary="Datos de un proveedor del catálogo")
def consultar_proveedor(proveedor_id: str, contenedor=Depends(obtener_contenedor)):
    resultado = contenedor.servicios.catalogo.consultar_proveedor(proveedor_id)
    if not resultado.exito:
        return JSONResponse(status_code=404, content=RechazoRespuesta(tipo="no_encontrado", detalle=resultado.mensaje).model_dump())
    return responder(contenedor, resultado, despachar=False)


def _existente_o_404(contenedor, proveedor_id: str):
    existe = contenedor.servicios.catalogo.consultar_proveedor(proveedor_id)
    if existe.exito:
        return None
    return JSONResponse(status_code=404, content=RechazoRespuesta(tipo="no_encontrado", detalle=existe.mensaje).model_dump())


@router.post("/proveedores/{proveedor_id}/edicion", response_model=OperacionRespuesta, responses=_NO_ENCONTRADO,
             summary="Corregir nombre, servicios y contacto de un proveedor")
def editar_proveedor(proveedor_id: str, entrada: ProveedorEntrada, contenedor=Depends(obtener_contenedor)):
    ausente = _existente_o_404(contenedor, proveedor_id)
    if ausente is not None:
        return ausente
    return responder(contenedor, contenedor.servicios.catalogo.editar_proveedor(proveedor_id, entrada.nombre, entrada.servicios, entrada.contacto),
                     despachar=False)


@router.post("/proveedores/{proveedor_id}/desactivacion", response_model=OperacionRespuesta, responses=_NO_ENCONTRADO,
             summary="Desactivar un proveedor (no se borra: deja de proponerse para asignaciones nuevas)")
def desactivar_proveedor(proveedor_id: str, contenedor=Depends(obtener_contenedor)):
    ausente = _existente_o_404(contenedor, proveedor_id)
    if ausente is not None:
        return ausente
    return responder(contenedor, contenedor.servicios.catalogo.cambiar_actividad_proveedor(proveedor_id, False), despachar=False)


@router.post("/proveedores/{proveedor_id}/activacion", response_model=OperacionRespuesta, responses=_NO_ENCONTRADO,
             summary="Volver a activar un proveedor desactivado")
def activar_proveedor(proveedor_id: str, contenedor=Depends(obtener_contenedor)):
    ausente = _existente_o_404(contenedor, proveedor_id)
    if ausente is not None:
        return ausente
    return responder(contenedor, contenedor.servicios.catalogo.cambiar_actividad_proveedor(proveedor_id, True), despachar=False)
