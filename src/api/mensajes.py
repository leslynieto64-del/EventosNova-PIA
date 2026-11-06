"""Mensaje de resultado en español para cada respuesta de la API (lo muestra la página /docs de Swagger tras pulsar Execute).

NO cambia ningún cuerpo JSON ni código HTTP: solo añade dos cabeceras a las respuestas JSON de la API:
    X-Mensaje       frase breve en español que explica qué ocurrió, en UTF-8 con codificación porcentual (las cabeceras HTTP son ASCII;
                    `decodeURIComponent` o `urllib.parse.unquote` la devuelven legible; Swagger lo hace al mostrar el aviso);
    X-Mensaje-Tipo  exito | info | advertencia | error.
Con el éxito de una consulta, el mensaje cuenta los elementos hallados; con el de una operación, usa el mensaje del servicio de aplicación
(o una frase más completa cuando el resultado es inequívoco); con un fallo, explica la causa. La interfaz web no las usa y las ignora."""
from __future__ import annotations
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

registro = logging.getLogger("eventosnova.api")

EXITO, INFO, ADVERTENCIA, ERROR = "exito", "info", "advertencia", "error"
CABECERA_MENSAJE, CABECERA_TIPO = "X-Mensaje", "X-Mensaje-Tipo"
MAXIMO_CUERPO_ANALIZADO = 1_000_000                       # más grande: se usa el mensaje genérico, sin leer el cuerpo
MAXIMO_MENSAJE = 400
_SIN_MENSAJE = ("/app", "/docs", "/redoc", "/openapi.json")   # interfaz web y documentación: no son respuestas de la API

# Frase completa para operaciones cuyo resultado es inequívoco. Solo se usa si el mensaje del servicio empieza por uno de los prefijos
# indicados; si no (p. ej. «El evento ya estaba cancelado»), se muestra el mensaje real del servicio y nunca una frase que no corresponda.
_FRASES: Dict[Tuple[str, str], List[Tuple[str, str]]] = {
    ("POST", "/eventos"): [("Evento registrado", "El evento se registró correctamente.")],
    ("POST", "/eventos/{evento_id}/propuestas"): [("Propuesta creada", "La propuesta se creó correctamente.")],
    ("POST", "/propuestas/{propuesta_id}/aceptacion"): [("Propuesta aceptada", "La propuesta fue aceptada correctamente.")],
    ("POST", "/propuestas/{propuesta_id}/contrato"): [("Contrato preparado", "El contrato se preparó correctamente.")],
    ("POST", "/contratos/{contrato_id}/firma"): [("Contrato firmado", "El contrato se firmó correctamente.")],
    ("POST", "/contratos/{contrato_id}/comunicacion-politica-no-reembolso"):
        [("Comunicación de la política", "La comunicación de la política de no reembolso quedó registrada.")],
    ("POST", "/contratos/{contrato_id}/confirmacion"): [("Contratación confirmada", "La contratación quedó confirmada.")],
    ("POST", "/estados-cuenta/{estado_cuenta_id}/pagos"):
        [("Pago Verificado", "El pago quedó registrado y verificado correctamente."), ("Pago Registrado", "El pago quedó registrado correctamente.")],
    ("POST", "/estados-cuenta/{estado_cuenta_id}/pagos/{pago_id}/verificacion"):
        [("Pago Verificado", "El pago quedó verificado correctamente.")],
    ("POST", "/eventos/{evento_id}/cancelacion"):
        [("Cancelación registrada", "El evento fue cancelado correctamente."), ("Evento cancelado", "El evento fue cancelado correctamente.")],
    ("POST", "/eventos/{evento_id}/revision-administrativa"): [("Revisión registrada", "La revisión administrativa quedó registrada.")],
    ("POST", "/eventos/{evento_id}/servicios/{servicio_contratado_id}/proveedor"):
        [("Proveedor asignado", "El proveedor fue asignado; queda pendiente de su confirmación.")],
    ("POST", "/eventos/{evento_id}/servicios/{servicio_contratado_id}/respuesta-proveedor"):
        [("Disponibilidad confirmada", "El proveedor confirmó su disponibilidad y la respuesta quedó registrada."),
         ("Indisponibilidad registrada", "El proveedor indicó que no está disponible y la respuesta quedó registrada.")],
    ("POST", "/proveedores"): [("Proveedor registrado", "El proveedor se registró correctamente.")],
}

_TIPOS_VALIDACION = {
    "missing": "es obligatorio", "string_type": "debe ser texto", "int_parsing": "debe ser un número entero", "int_type": "debe ser un número entero",
    "float_parsing": "debe ser un número", "float_type": "debe ser un número", "decimal_parsing": "debe ser un número", "decimal_type": "debe ser un número",
    "bool_parsing": "debe ser verdadero o falso", "bool_type": "debe ser verdadero o falso", "extra_forbidden": "no es un campo permitido",
    "string_too_short": "es demasiado corto", "string_too_long": "es demasiado largo", "list_type": "debe ser una lista", "dict_type": "debe ser un objeto",
    "datetime_parsing": "no tiene un formato de fecha y hora válido", "datetime_type": "no tiene un formato de fecha y hora válido",
    "datetime_from_date_parsing": "no tiene un formato de fecha y hora válido", "date_parsing": "no tiene un formato de fecha válido",
    "timezone_naive": "debe ir sin zona horaria", "json_invalid": "el cuerpo no es un JSON válido", "greater_than": "está fuera del rango permitido",
    "greater_than_equal": "está fuera del rango permitido", "less_than": "está fuera del rango permitido", "less_than_equal": "está fuera del rango permitido",
    "enum": "no es una de las opciones permitidas", "literal_error": "no es una de las opciones permitidas",
}


def _ruta_plantilla(scope: dict) -> str:
    ruta = scope.get("route")
    return getattr(ruta, "path_format", None) or getattr(ruta, "path", None) or scope.get("path", "")


# Consultas que devuelven UN elemento (no una lista): contar sus campos de lista («1 resultado (servicios)») confundiría.
_CONSULTAS_DE_UN_ELEMENTO = {
    "/proveedores/{proveedor_id}": "Se muestran los datos del proveedor.",
    "/eventos/{evento_id}/administracion": "Se muestra la información administrativa del evento.",
}
_SUSTANTIVOS = {"estados cuenta": "estados de cuenta"}          # el nombre sale de la clave del JSON; aquí se corrige cuando queda forzado


def _nombre(clave: str) -> str:
    nombre = re.sub(r"(?<!^)(?=[A-Z])", " ", clave).replace("_", " ").lower()
    return _SUSTANTIVOS.get(nombre, nombre)


def _contar(cuerpo: Any, plantilla: str) -> Optional[Tuple[str, int]]:
    """(nombre, cantidad) si la respuesta es una lista, o un objeto con una única lista (en la raíz o dentro de «datos»)."""
    if isinstance(cuerpo, list):
        partes = [p for p in plantilla.split("/") if p and not p.startswith("{")]
        return (_nombre(partes[-1]) if partes else "elementos"), len(cuerpo)
    if isinstance(cuerpo, dict):
        candidato = cuerpo.get("datos") if isinstance(cuerpo.get("datos"), dict) else cuerpo
        listas = [(k, v) for k, v in candidato.items() if isinstance(v, list)]
        if len(listas) == 1:
            return _nombre(listas[0][0]), len(listas[0][1])
    return None


def _validacion(detalle: list) -> str:
    problemas = []
    for e in detalle[:5]:
        if not isinstance(e, dict):
            continue
        loc = [str(x) for x in (e.get("loc") or []) if x not in ("body", "query", "path", "header", "cookie")]
        campo = ".".join(loc) or "la solicitud"
        if e.get("type") == "value_error":
            motivo = re.sub(r"^Value error, ", "", str(e.get("msg", "")))                # el texto lo escribió el proyecto (ya está en español)
        else:
            motivo = _TIPOS_VALIDACION.get(str(e.get("type")), f"no es válido ({e.get('msg', 'valor incorrecto')})")
        problemas.append(f"«{campo}» {motivo}")
    extra = f" (y {len(detalle) - 5} más)" if len(detalle) > 5 else ""
    return "Hay datos no válidos en la solicitud: " + "; ".join(problemas) + extra + "."


def describir(metodo: str, plantilla: str, estado: int, cuerpo: Any) -> Tuple[str, str]:
    """(tipo, mensaje) de una respuesta. `cuerpo` es el JSON ya leído (o None si no hay)."""
    detalle = cuerpo.get("detalle") if isinstance(cuerpo, dict) and isinstance(cuerpo.get("detalle"), str) else ""
    if 200 <= estado < 300:
        if metodo in ("GET", "HEAD"):
            if plantilla in _CONSULTAS_DE_UN_ELEMENTO:
                return INFO, "Consulta realizada correctamente. " + _CONSULTAS_DE_UN_ELEMENTO[plantilla]
            cuenta = _contar(cuerpo, plantilla)
            if cuenta is None:
                return INFO, "Consulta realizada correctamente."
            nombre, n = cuenta
            if n == 0:
                return INFO, f"Consulta realizada correctamente. No se encontraron {nombre}."
            return INFO, "Consulta realizada correctamente. " + (f"Se encontraron {n} {nombre}." if n > 1 else f"Se encontró 1 resultado ({nombre}).")
        servicio = cuerpo.get("mensaje") if isinstance(cuerpo, dict) and isinstance(cuerpo.get("mensaje"), str) else ""
        for prefijo, frase in _FRASES.get((metodo, plantilla), []):
            if servicio.startswith(prefijo):
                return EXITO, frase
        return EXITO, "Operación realizada correctamente." + (f" {servicio}" if servicio else "")
    if estado == 401:
        if plantilla == "/auth/inicio-sesion":
            return ERROR, "No se pudo iniciar sesión. Comprueba tus credenciales."
        return ERROR, "No has iniciado sesión o tu sesión expiró. Inicia sesión para continuar."
    if estado == 403:
        if "token de seguridad" in detalle:                                       # CSRF: no es un problema de permisos del rol
            return ERROR, "No se pudo validar la petición: falta el token de seguridad (CSRF) o venció. Vuelve a iniciar sesión y recarga la página; en Swagger, inicia sesión en /app/ y recarga /docs."
        if "no proviene de este sitio" in detalle:
            return ERROR, "La petición se rechazó porque no proviene de este sitio. Usa la aplicación o Swagger desde la dirección del propio servicio."
        extra = f" {detalle}" if detalle and "permiso" not in detalle.lower() else ""
        return ERROR, "No tienes permisos para realizar esta operación." + extra
    if estado == 404:
        return ERROR, "No se encontró el recurso solicitado." + (f" {detalle}" if detalle else "")
    if estado == 409:
        return ADVERTENCIA, "La operación no pudo completarse porque existe un conflicto con el estado actual." + (f" {detalle}" if detalle else "")
    if estado == 413:
        return ERROR, "La solicitud es demasiado grande."
    if estado == 422:
        if isinstance(cuerpo, dict) and isinstance(cuerpo.get("detail"), list):
            return ADVERTENCIA, _validacion(cuerpo["detail"])
        pendientes = cuerpo.get("pendientes") if isinstance(cuerpo, dict) and isinstance(cuerpo.get("pendientes"), list) else []
        extra = " Pendiente: " + "; ".join(str(p) for p in pendientes) + "." if pendientes else ""
        return ADVERTENCIA, "No se pudo completar la operación" + (f": {detalle}" if detalle else " porque no cumple una regla de negocio.") + extra
    if estado == 429:
        return ADVERTENCIA, detalle or "Demasiados intentos. Espera un momento antes de volver a intentarlo."
    if estado == 503:
        return ADVERTENCIA, "El servicio o la base de datos no está disponible. Intenta de nuevo más tarde."
    if estado >= 500:
        return ERROR, "Ocurrió un error interno. Intenta más tarde o contacta al administrador."
    return ERROR, f"La solicitud no pudo procesarse (código {estado})." + (f" {detalle}" if detalle else "")


def _para_cabecera(texto: str) -> str:
    """Sin saltos ni caracteres de control (la cabecera no puede partirse) y en ASCII: UTF-8 con codificación porcentual."""
    limpio = re.sub(r"[\x00-\x1f\x7f]+", " ", texto).strip()[:MAXIMO_MENSAJE]
    return quote(limpio, safe=" .,;:()-_'/")


def _cabeceras(metodo: str, plantilla: str, estado: int, cuerpo: Any) -> List[Tuple[bytes, bytes]]:
    tipo, mensaje = describir(metodo, plantilla, estado, cuerpo)
    return [(CABECERA_MENSAJE.lower().encode(), _para_cabecera(mensaje).encode("ascii")), (CABECERA_TIPO.lower().encode(), tipo.encode())]


class MensajesDeResultado:
    """Middleware ASGI: añade X-Mensaje y X-Mensaje-Tipo a las respuestas JSON de la API sin tocar su cuerpo ni su código."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"].startswith(_SIN_MENSAJE):
            return await self.app(scope, receive, send)
        inicio: Optional[dict] = None
        trozos: List[bytes] = []
        pasar = False                                          # respuesta que no es JSON: se deja pasar sin tocar

        async def enviar(mensaje):
            nonlocal inicio, pasar
            if mensaje["type"] == "http.response.start":
                tipos = [v for k, v in mensaje.get("headers", []) if k.lower() == b"content-type"]
                if not tipos or not tipos[0].lower().startswith(b"application/json"):
                    pasar = True
                    return await send(mensaje)
                inicio = mensaje
                return
            if pasar or inicio is None:
                return await send(mensaje)
            trozos.append(mensaje.get("body", b""))
            if mensaje.get("more_body"):
                return
            cuerpo_bytes = b"".join(trozos)
            cuerpo: Any = None
            if len(cuerpo_bytes) <= MAXIMO_CUERPO_ANALIZADO:
                try:
                    cuerpo = json.loads(cuerpo_bytes)
                except ValueError:
                    cuerpo = None
            try:
                extra = _cabeceras(scope.get("method", "GET"), _ruta_plantilla(scope), inicio["status"], cuerpo)
            except Exception:                                  # el mensaje es una ayuda: nunca debe romper la respuesta
                registro.exception("No se pudo componer el mensaje de resultado")
                extra = []
            await send({**inicio, "headers": list(inicio.get("headers", [])) + extra})
            await send({"type": "http.response.body", "body": cuerpo_bytes})

        await self.app(scope, receive, enviar)


def registrar_mensajes(aplicacion: FastAPI) -> None:
    aplicacion.add_middleware(MensajesDeResultado)

    @aplicacion.exception_handler(Exception)
    async def _error_interno(request: Request, exc: Exception):
        """Misma respuesta de siempre (500, «Internal Server Error») más el mensaje. Starlette registra el traceback y vuelve a lanzar
        la excepción después de enviarla: no se pierde nada de la depuración y el cliente no recibe trazas."""
        tipo, mensaje = describir(request.method, "", 500, None)
        return PlainTextResponse("Internal Server Error", status_code=500,
                                 headers={CABECERA_MENSAJE: _para_cabecera(mensaje), CABECERA_TIPO: tipo})
