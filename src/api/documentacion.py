"""Página /docs (Swagger UI) con un aviso de resultado en español tras cada Execute.

Es la misma página que genera FastAPI (mismos recursos de swagger-ui-dist@5), más un `responseInterceptor` que lee las cabeceras
X-Mensaje y X-Mensaje-Tipo de `api.mensajes` y las muestra en un aviso fijo. El aviso nunca contradice al servidor: si la respuesta no fue
correcta (código fuera de 2xx), jamás se muestra como éxito. Solo se registra cuando la documentación está habilitada
(EVENTOSNOVA_DOCS=1); en producción sigue oculta y /docs responde 404."""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

_PAGINA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
<title>__TITULO__ - Swagger UI</title>
<style>
#aviso-resultado { position: fixed; top: 12px; left: 50%; transform: translateX(-50%); z-index: 10000; max-width: min(92vw, 720px);
  display: none; align-items: flex-start; gap: 12px; padding: 12px 16px; border-radius: 8px; border: 1px solid; font: 15px/1.4 system-ui, sans-serif;
  box-shadow: 0 6px 20px rgba(0, 0, 0, .25); overflow-wrap: anywhere; }
#aviso-resultado.visible { display: flex; }
#aviso-resultado .codigo { opacity: .75; font-size: 13px; white-space: nowrap; }
#aviso-resultado button { margin-left: auto; border: 0; background: transparent; font-size: 20px; line-height: 1; cursor: pointer; color: inherit; }
#aviso-resultado.exito { background: #d1e7dd; border-color: #0f5132; color: #0a3622; }
#aviso-resultado.info { background: #cff4fc; border-color: #055160; color: #032830; }
#aviso-resultado.advertencia { background: #fff3cd; border-color: #664d03; color: #523e02; }
#aviso-resultado.error { background: #f8d7da; border-color: #842029; color: #58151c; }
</style>
</head>
<body>
<div id="aviso-resultado" role="status" aria-live="polite"><div><strong class="etiqueta"></strong> <span class="texto"></span> <span class="codigo"></span></div><button type="button" aria-label="Cerrar aviso">&times;</button></div>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
const ETIQUETAS = { exito: 'Correcto:', info: 'Información:', advertencia: 'Atención:', error: 'Error:' };
const aviso = document.getElementById('aviso-resultado');
aviso.querySelector('button').addEventListener('click', () => aviso.classList.remove('visible'));

function mostrarAviso(tipo, mensaje, estado) {
  aviso.className = 'visible ' + tipo;
  aviso.setAttribute('role', tipo === 'error' ? 'alert' : 'status');
  aviso.querySelector('.etiqueta').textContent = ETIQUETAS[tipo];
  aviso.querySelector('.texto').textContent = mensaje;                       // textContent: el mensaje nunca se interpreta como HTML
  aviso.querySelector('.codigo').textContent = estado ? '(HTTP ' + estado + ')' : '';
}

function cabecera(res, nombre) {
  const h = res.headers;
  if (!h) return null;
  return typeof h.get === 'function' ? h.get(nombre) : (h[nombre] || h[nombre.toLowerCase()] || null);
}

function avisarResultado(res) {
  if (/\\/openapi\\.json(\\?|$)/.test(res.url || '')) return;                    // la carga de la especificación no es una operación del usuario
  const estado = res.status || 0;
  let tipo = cabecera(res, 'x-mensaje-tipo');
  let mensaje = cabecera(res, 'x-mensaje');
  if (mensaje) { try { mensaje = decodeURIComponent(mensaje); } catch (e) { /* ya venía legible */ } }      // X-Mensaje viaja en UTF-8 con codificación porcentual
  if (!ETIQUETAS[tipo]) tipo = null;
  if (!mensaje) {
    tipo = tipo || (res.ok ? 'info' : 'error');
    mensaje = estado === 0 ? 'No se recibió respuesta del servidor.' : (res.ok ? 'La solicitud terminó correctamente.' : 'La solicitud no se pudo completar.');
  }
  if (!res.ok && (tipo === 'exito' || tipo === 'info')) tipo = 'error';        // nunca se muestra un éxito si el servidor devolvió un error
  mostrarAviso(tipo || 'info', mensaje, estado);
}

window.ui = SwaggerUIBundle({
  url: '__OPENAPI__',
  dom_id: '#swagger-ui',
  layout: 'BaseLayout',
  deepLinking: true,
  showExtensions: true,
  showCommonExtensions: true,
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
  responseInterceptor: (res) => { try { avisarResultado(res); } catch (e) { /* el aviso es una ayuda: no debe romper la respuesta */ } return res; },
});
</script>
</body>
</html>
"""


def pagina_swagger(titulo: str, openapi_url: str = "/openapi.json") -> str:
    return _PAGINA.replace("__TITULO__", titulo).replace("__OPENAPI__", openapi_url)


def registrar_swagger(aplicacion: FastAPI) -> None:
    @aplicacion.get("/docs", include_in_schema=False)
    def _swagger() -> HTMLResponse:
        return HTMLResponse(pagina_swagger(aplicacion.title, aplicacion.openapi_url or "/openapi.json"))
