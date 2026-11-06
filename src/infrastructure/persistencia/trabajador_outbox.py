"""Trabajador de despacho del Outbox (proceso aparte, ejecutable).

    python -m infrastructure.persistencia.trabajador_outbox            # bucle continuo (Docker Compose: servicio `worker`)
    python -m infrastructure.persistencia.trabajador_outbox --una-vez  # despacha lo pendiente y termina

Lee DATABASE_URL del entorno o de `.env`, comprueba la conexión y que las migraciones estén aplicadas, y despacha los eventos
pendientes cada `--intervalo` segundos. Se puede ejecutar más de un trabajador a la vez: el reclamo con `SKIP LOCKED` evita que dos
procesen el mismo evento. Un fallo en un ciclo se registra y el bucle continúa; SIGINT/SIGTERM lo detienen de forma ordenada.

Orden de arranque en una plataforma (p. ej. Render): este proceso NO migra y no puede asumir que la migración ya terminó. Con `--espera-esquema SEGUNDOS`
(por omisión 0: un solo intento, como antes) reintenta cada pocos segundos, con límite de tiempo, mientras la base de datos no responda o no tenga aplicada
la revisión de Alembic que el código necesita; registra cada espera y, si vence el plazo, termina con error. Las migraciones las aplica solo el
`preDeployCommand` de la API (`python -m alembic upgrade head`)."""
from __future__ import annotations
import argparse
import logging
import signal
import sys
import threading
import time
from datetime import datetime
from typing import Callable, Optional
from application.reloj import reloj_negocio
from .composicion_persistente import construir_persistente
from .errores import ErrorDeConexion, EsquemaDesactualizado

registro = logging.getLogger("eventosnova.trabajador")
INTERVALO_ESPERA_S = 5.0            # segundos entre intentos mientras la base no está lista


def ejecutar(contenedor, intervalo: float = 2.0, una_vez: bool = False, detener: Optional[threading.Event] = None,
             reloj: Callable[[], datetime] = reloj_negocio) -> int:
    """En cada ciclo aplica la llegada de T a los eventos que corresponda (C-01, CA-109, CA-110) y despacha el Outbox, hasta que `detener`
    se active (o una sola vez). Devuelve cuántos eventos del Outbox procesó en total. `reloj` es el reloj de negocio de la API (America/Mexico_City, sin zona, TP-06)."""
    detener = detener or threading.Event()
    total = 0
    while not detener.is_set():
        try:
            llegada = contenedor.servicios.cierre.procesar_eventos_vencidos(reloj())
            if llegada.datos.get("iniciados") or llegada.datos.get("cerrados") or llegada.datos.get("errores"):
                registro.info("Llegada de T: %s", llegada.datos)
            procesados = contenedor.despachador.despachar()
            total += procesados
            if procesados:
                registro.info("Eventos procesados: %s", procesados)
        except Exception:                                   # se registra y se reintenta en el siguiente ciclo
            registro.exception("Falló un ciclo de despacho del Outbox")
            if una_vez:
                raise
        if una_vez:
            break
        detener.wait(intervalo)
    return total


def construir_esperando_esquema(espera_max: float, intervalo: float, detener: threading.Event, construir: Optional[Callable[[], object]] = None,
                                reloj: Callable[[], float] = time.monotonic):
    """Construye el contenedor esperando, con límite de tiempo, a que la base responda y alcance la revisión de Alembic que el código necesita.

    Solo reintenta mientras el motivo sea transitorio (`ErrorDeConexion`, `EsquemaDesactualizado`); NUNCA migra. Cualquier otro error (p. ej. falta
    `DATABASE_URL`) se propaga de inmediato. Si vence `espera_max` (0 = un solo intento) registra el motivo y vuelve a lanzar el último error.
    Devuelve None si se pidió detener (SIGTERM/SIGINT) mientras esperaba."""
    construir = construir or construir_persistente            # se resuelve al llamar (así se puede sustituir en las pruebas)
    inicio, intento = reloj(), 0
    while True:
        intento += 1
        try:
            contenedor = construir()
        except (ErrorDeConexion, EsquemaDesactualizado) as e:
            restante = espera_max - (reloj() - inicio)
            if restante <= 0:
                if espera_max > 0:
                    registro.error("La base de datos no estuvo lista en %.0f s (%d intentos): %s", espera_max, intento, e)
                raise
            if intento == 1 or intento % 6 == 0:                  # el primer aviso y luego uno cada ~30 s: sin inundar el log
                registro.warning("Esperando a que la base de datos esté lista (%s): %s Se reintenta cada %.0f s; quedan %.0f s. Este proceso no "
                                 "ejecuta migraciones.", type(e).__name__, e, intervalo, restante)
            if detener.wait(min(intervalo, restante)):
                registro.info("Detenido mientras esperaba a la base de datos.")
                return None
            continue
        if intento > 1:
            registro.info("La base de datos está lista tras %.0f s (%d intentos).", reloj() - inicio, intento)
        return contenedor


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Trabajador de despacho del Outbox de Eventos Nova")
    parser.add_argument("--intervalo", type=float, default=2.0, help="segundos entre ciclos (por omisión 2)")
    parser.add_argument("--una-vez", action="store_true", help="despachar lo pendiente y terminar")
    parser.add_argument("--espera-esquema", type=float, default=0.0, metavar="SEGUNDOS",
                        help="espera máxima a que la base responda y tenga las migraciones al día, sin migrar (por omisión 0: un solo intento)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    detener = threading.Event()
    anteriores = {senal: signal.signal(senal, lambda *_: detener.set()) for senal in (signal.SIGINT, signal.SIGTERM)}
    try:
        contenedor = construir_esperando_esquema(args.espera_esquema, INTERVALO_ESPERA_S, detener)    # falla de forma clara si no hay base o falta migrar
        if contenedor is None:                                # SIGTERM/SIGINT durante la espera
            return 0
        try:
            total = ejecutar(contenedor, args.intervalo, args.una_vez, detener)
            registro.info("Trabajador detenido; eventos procesados: %s", total)
        finally:
            contenedor.cerrar()
    finally:
        for senal, manejador in anteriores.items():         # no deja alterados los manejadores de señales del proceso
            signal.signal(senal, manejador)
    return 0


if __name__ == "__main__":
    sys.exit(main())
