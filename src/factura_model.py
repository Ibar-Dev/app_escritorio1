"""Modelos de dominio para facturas (dataclasses puras, sin I/O)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from src.money import parse


@dataclass
class LineaFactura:
    concepto: str
    cantidad: int
    precio_unitario: Decimal  # precio final, IVA ya incluido
    categoria: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.precio_unitario, Decimal):
            self.precio_unitario = parse(self.precio_unitario)

    @property
    def total(self) -> Decimal:
        return parse(self.cantidad * self.precio_unitario)


@dataclass
class PagoInfo:
    monto_total: Decimal
    monto_efectivo: Decimal
    monto_tarjeta: Decimal
    metodo_pago: str  # "efectivo" | "tarjeta" | "mixto"
    efectivo_entregado: Decimal
    cambio: Decimal

    def __post_init__(self) -> None:
        for f in ("monto_total", "monto_efectivo", "monto_tarjeta", "efectivo_entregado", "cambio"):
            v = getattr(self, f)
            if not isinstance(v, Decimal):
                object.__setattr__(self, f, parse(v))


@dataclass
class Factura:
    numero: int
    fecha: date
    cliente_nombre: str = ""
    cliente_nif: str = ""
    lineas: list[LineaFactura] = field(default_factory=list)

    @property
    def total_con_iva(self) -> Decimal:
        return parse(sum(l.total for l in self.lineas))

    @property
    def numero_formateado(self) -> str:
        return f"{self.fecha.year}-{self.numero:03d}"
