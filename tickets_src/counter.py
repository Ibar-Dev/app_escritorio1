"""Contador persistente de tickets en data/contador.json."""
from __future__ import annotations

import src.settings as _s
from src.counter import decrementar as _dec
from src.counter import peek_siguiente as _peek
from src.counter import siguiente_numero as _siguiente

_ARCHIVO = _s.RUTA_DATOS / "contador.json"


def peek_siguiente() -> int:
    """Returns the next ticket number without incrementing the counter."""
    return _peek(_ARCHIVO)


def siguiente_numero() -> int:
    """Retorna el próximo número de ticket e incrementa el contador."""
    return _siguiente(_ARCHIVO)


def rollback() -> None:
    """Rolls back the last consumed ticket number; call only on write failure."""
    _dec(_ARCHIVO)
