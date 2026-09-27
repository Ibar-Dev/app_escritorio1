"""Modelos de dominio para tickets TPV (dataclasses puras, sin I/O)."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from src.money import parse


@dataclass
class LineaTicket:
    nombre: str
    cantidad: int
    precio_unitario: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.precio_unitario, Decimal):
            self.precio_unitario = parse(self.precio_unitario)

    @property
    def total(self) -> Decimal:
        return parse(self.cantidad * self.precio_unitario)


@dataclass
class Ticket:
    numero: int
    lineas: list[LineaTicket] = field(default_factory=list)
    metodo_pago: str = "efectivo"
    subtotal: float = 0.0

    def __post_init__(self) -> None:
        # Si no se informa subtotal, se inicializa desde las lineas actuales.
        if self.subtotal == 0.0 and self.lineas:
            self.subtotal = float(self.total)
        self.metodo_pago = (self.metodo_pago or "efectivo").strip().lower()

    @property
    def total(self) -> Decimal:
        return parse(sum(l.total for l in self.lineas))
