"""Contador persistente genérico — lee, incrementa y escribe un archivo JSON."""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_locks: dict[Path, threading.Lock] = {}
_locks_meta = threading.Lock()


def _get_lock(ruta: Path) -> threading.Lock:
    with _locks_meta:
        if ruta not in _locks:
            _locks[ruta] = threading.Lock()
        return _locks[ruta]


def peek_siguiente(ruta: Path) -> int:
    """Returns the next number without incrementing the counter."""
    return _leer(ruta)


def siguiente_numero(ruta: Path) -> int:
    """Retorna el próximo número disponible e incrementa el contador en disco."""
    with _get_lock(ruta):
        n = _leer(ruta)
        _escribir(ruta, n + 1)
        return n


def decrementar(ruta: Path) -> None:
    """Decrements the counter by 1; call only in error rollback paths."""
    with _get_lock(ruta):
        n = _leer(ruta)
        _escribir(ruta, max(1, n - 1))


def _leer(ruta: Path) -> int:
    if ruta.exists():
        try:
            return int(json.loads(ruta.read_text("utf-8")).get("siguiente", 1))
        except (OSError, ValueError, AttributeError):
            logger.warning("Contador %s corrupto, reiniciando desde 1.", ruta.name)
    return 1


def _escribir(ruta: Path, valor: int) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"siguiente": valor}, indent=2), "utf-8")
