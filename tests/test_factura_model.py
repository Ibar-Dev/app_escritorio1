"""Tests para src.factura_model — sin I/O."""
from __future__ import annotations

from datetime import date

from decimal import Decimal

import pytest

from src.factura_model import Factura, LineaFactura, PagoInfo


def _linea(concepto="Servicio", cantidad=2, precio=15.0, categoria="perro"):
    return LineaFactura(concepto=concepto, cantidad=cantidad, precio_unitario=precio, categoria=categoria)


class TestLineaFactura:
    def test_total_entero(self):
        assert _linea(cantidad=3, precio=10.0).total == 30.0

    def test_total_decimales(self):
        assert _linea(cantidad=2, precio=7.50).total == 15.0

    def test_redondeo_centimos(self):
        # 3 × 0.1 en float puede dar 0.30000000000000004 sin round
        linea = LineaFactura("x", 3, 0.1)
        assert linea.total == Decimal("0.30")


class TestFactura:
    def test_total_con_iva_suma_lineas(self):
        f = Factura(
            numero=1,
            fecha=date(2026, 1, 15),
            lineas=[_linea(cantidad=2, precio=10.0), _linea(cantidad=1, precio=5.0)],
        )
        assert f.total_con_iva == 25.0

    def test_total_factura_vacia(self):
        f = Factura(numero=1, fecha=date(2026, 1, 1))
        assert f.total_con_iva == 0.0

    def test_numero_formateado(self):
        f = Factura(numero=7, fecha=date(2026, 3, 10))
        assert f.numero_formateado == "2026-007"

    def test_numero_formateado_tres_digitos(self):
        f = Factura(numero=123, fecha=date(2025, 12, 1))
        assert f.numero_formateado == "2025-123"


class TestPagoInfo:
    def test_cambio_calculado(self):
        pago = PagoInfo(
            monto_total=50.0,
            monto_efectivo=50.0,
            monto_tarjeta=0.0,
            metodo_pago="efectivo",
            efectivo_entregado=60.0,
            cambio=10.0,
        )
        assert pago.cambio == 10.0

    def test_pago_mixto(self):
        pago = PagoInfo(30.0, 20.0, 10.0, "mixto", 25.0, 5.0)
        assert pago.monto_efectivo + pago.monto_tarjeta == pago.monto_total
