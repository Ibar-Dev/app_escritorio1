"""Impresión ESC/POS de recibos de factura en impresora térmica POS-80 USB.

Si el dispositivo no está conectado, se relanza como ConnectionError para
que la UI muestre un aviso sin crashear.
"""
from __future__ import annotations

import logging
import textwrap

from .factura_model import Factura

logger = logging.getLogger(__name__)

_PRINTER_NAME = "POS-80C (copy 3)"  # nombre exacto en el gestor de impresión de Windows
_ANCHO_DEFAULT = 42


def generar_ticket_escpos(factura: Factura, ancho: int = _ANCHO_DEFAULT) -> list[str]:
    """Devuelve líneas de texto formateadas para imprimir como recibo."""
    sep = "─" * ancho
    lineas: list[str] = [
        "ZOO PICASSO".center(ancho),
        sep,
        f"Factura: {factura.numero_formateado}".center(ancho),
        f"Fecha: {factura.fecha.strftime('%d/%m/%Y')}".center(ancho),
    ]
    if factura.cliente_nombre:
        lineas.append(f"Cliente: {factura.cliente_nombre}"[:ancho])
    lineas.append(sep)
    for linea in factura.lineas:
        concepto = linea.concepto[:ancho - 12]
        lineas.append(f"{concepto:<{ancho - 12}} {linea.total:>10.2f}")
    lineas += [
        sep,
        f"{'TOTAL':>{ancho - 12}} {factura.total_con_iva:>10.2f} EUR",
        sep,
        "Gracias por su visita".center(ancho),
        "",
    ]
    return lineas


def imprimir_ticket_usb_windows(lineas: list[str]) -> str:
    """Envía las líneas a la impresora USB y retorna su identificador.

    Raises:
        ConnectionError: si la impresora no está disponible o falla la conexión.
    """
    try:
        from escpos.printer import Win32Raw
        p = Win32Raw(_PRINTER_NAME)
        for linea in lineas:
            p.text(linea + "\n")
        p.cut()
        p.close()
        logger.info("Ticket impreso en '%s'", _PRINTER_NAME)
        return f"Win32Raw({_PRINTER_NAME})"
    except Exception as exc:
        logger.warning("Impresora no disponible: %s", exc)
        raise ConnectionError(f"Impresora no disponible: {exc}") from exc
