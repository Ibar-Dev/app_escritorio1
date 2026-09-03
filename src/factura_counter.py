"""Contador persistente de facturas en data/contador_facturas.json."""
from __future__ import annotations

import src.settings as _s
from src.counter import decrementar as _dec
from src.counter import peek_siguiente as _peek
from src.counter import siguiente_numero as _siguiente

_ARCHIVO = _s.RUTA_DATOS / "contador_facturas.json"


def peek_siguiente_numero_factura() -> int:
    """Returns the next invoice number without incrementing the counter."""
    return _peek(_ARCHIVO)


def siguiente_numero_factura() -> int:
    """Retorna el próximo número de factura e incrementa el contador."""
    return _siguiente(_ARCHIVO)


def rollback_numero_factura() -> None:
    """Rolls back the last consumed invoice number; call only on write failure."""
    _dec(_ARCHIVO)
