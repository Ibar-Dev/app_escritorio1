"""Operaciones monetarias exactas con decimal.Decimal."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

_Q2 = Decimal("0.01")


def parse(valor: str | float | int | Decimal) -> Decimal:
    """Convierte cualquier entrada numérica a Decimal de 2 decimales."""
    if isinstance(valor, Decimal):
        return valor.quantize(_Q2, rounding=ROUND_HALF_UP)
    return Decimal(str(valor)).quantize(_Q2, rounding=ROUND_HALF_UP)


def cents(d: Decimal) -> int:
    """Decimal → céntimos enteros para almacenamiento en SQLite."""
    return int(d.quantize(_Q2, rounding=ROUND_HALF_UP) * 100)


def from_cents(n: int | None) -> Decimal:
    """Céntimos enteros de SQLite → Decimal con 2 decimales."""
    return (Decimal(n or 0) / 100).quantize(_Q2)
