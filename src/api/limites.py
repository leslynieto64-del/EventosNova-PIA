"""Límite del tamaño del cuerpo de las peticiones: una persona autenticada (o un programa) no puede enviar cuerpos enormes que agoten la memoria
o llenen la base de datos. Se aplica en la capa ASGI, antes de interpretar el JSON, tanto con `Content-Length` como con cuerpo por trozos.

`EVENTOSNOVA_TAMANO_MAXIMO_CUERPO` (bytes) lo cambia; por omisión 256 KiB, muy por encima de cualquier formulario de la interfaz."""
from __future__ import annotations
import json
import os

MAXIMO_POR_OMISION = 256 * 1024


def maximo_desde_entorno() -> int:
    try:
        valor = int(os.environ.get("EVENTOSNOVA_TAMANO_MAXIMO_CUERPO", MAXIMO_POR_OMISION))
    except ValueError:
        return MAXIMO_POR_OMISION
    return valor if valor > 0 else MAXIMO_POR_OMISION


class LimiteDeCuerpo:
    def __init__(self, app, maximo: int):
        self.app, self.maximo = app, maximo

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declarado = next((v for k, v in scope["headers"] if k == b"content-length"), None)
        if declarado is not None:
            try:
                if int(declarado) > self.maximo:
                    await self._rechazar(send)
                    return
            except ValueError:
                pass
        recibido, excedido = 0, False

        async def recibir():
            nonlocal recibido, excedido
            mensaje = await receive()
            if mensaje["type"] == "http.request":
                recibido += len(mensaje.get("body", b""))
                if recibido > self.maximo:                    # se corta la lectura; la respuesta de la aplicación se sustituye por 413
                    excedido = True
                    return {"type": "http.request", "body": b"", "more_body": False}
            return mensaje

        async def enviar(mensaje):
            if excedido:
                if mensaje["type"] == "http.response.start":
                    await self._rechazar(send)
                return
            await send(mensaje)

        await self.app(scope, recibir, enviar)

    async def _rechazar(self, send):
        cuerpo = json.dumps({"tipo": "cuerpo_demasiado_grande", "detalle": "El cuerpo de la petición supera el tamaño permitido.",
                             "pendientes": []}).encode("utf-8")
        await send({"type": "http.response.start", "status": 413,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(cuerpo)).encode())]})
        await send({"type": "http.response.body", "body": cuerpo})
