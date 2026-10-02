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
    monto_efectivo: Decimal = field(default_factory=lambda: Decimal("0.00"))
    monto_tarjeta: Decimal = field(default_factory=lambda: Decimal("0.00"))

    def __post_init__(self) -> None:
        metodos_validos = {"efectivo", "tarjeta", "mixto"}
        self.metodo_pago = (self.metodo_pago or "efectivo").strip().lower()
        if self.metodo_pago not in metodos_validos:
            raise ValueError(
                f"Metodo de pago '{self.metodo_pago}' no valido. "
                "Debe ser: efectivo, tarjeta o mixto."
            )

        if not isinstance(self.monto_efectivo, Decimal):
            self.monto_efectivo = parse(self.monto_efectivo)
        if not isinstance(self.monto_tarjeta, Decimal):
            self.monto_tarjeta = parse(self.monto_tarjeta)

        # Si no se informa subtotal, se inicializa desde las lineas actuales.
        if self.subtotal == 0.0 and self.lineas:
            self.subtotal = float(self.total)

        total_ticket = self.total
        if self.metodo_pago == "efectivo":
            self.monto_efectivo = total_ticket
            self.monto_tarjeta = Decimal("0.00")
        elif self.metodo_pago == "tarjeta":
            self.monto_efectivo = Decimal("0.00")
            self.monto_tarjeta = total_ticket
        else:
            if self.monto_efectivo <= 0:
                raise ValueError("Pago mixto: el monto en efectivo debe ser mayor a 0.")
            if self.monto_tarjeta <= 0:
                raise ValueError("Pago mixto: el monto en tarjeta debe ser mayor a 0.")
            suma_montos = parse(self.monto_efectivo + self.monto_tarjeta)
            if suma_montos != total_ticket:
                raise ValueError(
                    "Pago mixto: la suma de efectivo y tarjeta debe ser igual al total del ticket."
                )

    @property
    def total(self) -> Decimal:
        return parse(sum(l.total for l in self.lineas))
