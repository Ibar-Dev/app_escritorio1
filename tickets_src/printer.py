"""Impresión ESC/POS de tickets TPV en impresora térmica POS-80 USB.

Si el dispositivo no está conectado, se relanza como ConnectionError para
que la UI muestre un aviso sin crashear.
"""
from __future__ import annotations

import logging
import time

from tickets_src.ticket_model import Ticket

logger = logging.getLogger(__name__)

_PRINTER_NAME = "POS-80C (copy 3)"  # nombre exacto en el gestor de impresión de Windows
_ANCHO = 32
_MAX_INTENTOS = 3
_BACKOFF_BASE = 1  # segundos; secuencia de delays: 1s, 2s


def imprimir_ticket(ticket: Ticket) -> None:
    """Imprime el ticket por USB con reintentos antes de rendirse.

    Raises:
        ConnectionError: si la impresora no está disponible tras todos los intentos.
    """
    ultimo_exc: Exception | None = None
    for intento in range(1, _MAX_INTENTOS + 1):
        try:
            _imprimir(ticket)
            return
        except Exception as exc:
            ultimo_exc = exc
            if intento < _MAX_INTENTOS:
                delay = _BACKOFF_BASE * (2 ** (intento - 1))
                logger.info(
                    "Impresora: reintento %d/%d en %ds — %s",
                    intento, _MAX_INTENTOS, delay, exc,
                )
                time.sleep(delay)
    logger.warning("Impresora no disponible tras %d intentos: %s", _MAX_INTENTOS, ultimo_exc)
    raise ConnectionError(f"Impresora no disponible: {ultimo_exc}") from ultimo_exc


def _imprimir(ticket: Ticket) -> None:
    from escpos.printer import Win32Raw

    p = Win32Raw(_PRINTER_NAME)
    p.text("ZOO PICASSO\n".center(_ANCHO))
    p.text(("─" * _ANCHO) + "\n")
    p.text(f"Ticket #{ticket.numero:04d}\n".center(_ANCHO))
    p.text(("─" * _ANCHO) + "\n")
    for linea in ticket.lineas:
        nombre = linea.nombre[: _ANCHO - 10]
        p.text(f"{nombre:<{_ANCHO - 10}} {linea.total:>8.2f}\n")
    p.text(("─" * _ANCHO) + "\n")
    p.text(f"{'TOTAL':>{_ANCHO - 10}} {ticket.total:>8.2f} EUR\n")
    p.text("\nGracias por su visita\n".center(_ANCHO))
    p.cut()
    p.close()
    logger.info("Ticket T-%04d impreso.", ticket.numero)
