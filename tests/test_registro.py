"""Tests para escritorio.registro — inserción en SQLite vía ventas_store."""
from __future__ import annotations

from datetime import date

import pytest

from escritorio.registro import registrar_ventas_ticket
from src.ventas_store import historial_ventas, inicializar_db_ventas


class TestRegistrarVentasTicket:
    def test_inserta_filas(self):
        registrar_ventas_ticket(1, [("perro", 15.0), ("gato", 10.0)], "Giselle")
        filas = historial_ventas("2026-01-01", "2099-12-31")
        assert len(filas) == 1  # agrupado por ticket
        assert filas[0]["monto_lineas"] == 25

    def test_numero_ticket_formateado(self):
        registrar_ventas_ticket(42, [("perro", 5.0)], "u")
        filas = historial_ventas("2026-01-01", "2099-12-31")
        assert filas[0]["numero_factura"] == "T-0042"

    def test_filas_vacias_no_inserta(self):
        registrar_ventas_ticket(1, [], "u")
        filas = historial_ventas("2026-01-01", "2099-12-31")
        assert len(filas) == 0

    def test_categoria_none_usa_sin_categoria(self):
        registrar_ventas_ticket(1, [(None, 10.0)], "u")
        filas = historial_ventas("2026-01-01", "2099-12-31")
        assert "sin_categoria" in filas[0]["categorias"]
