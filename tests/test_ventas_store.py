"""Tests para src.ventas_store — SQLite con BD temporal."""
from __future__ import annotations

from datetime import date, datetime

import pytest

from src.factura_model import Factura, LineaFactura, PagoInfo
from src.ventas_store import (
    historial_ventas,
    inicializar_db_ventas,
    listar_ajustes_activos,
    registrar_ventas_factura,
    resumen_ventas_activas,
    resumen_ventas_dia,
    ventas_activas_detalle,
)
from escritorio.registro import registrar_ventas_ticket


def _factura(numero=1, fecha=date(2026, 6, 15), lineas=None, cliente="Cliente Test"):
    if lineas is None:
        lineas = [LineaFactura("Servicio A", 2, 10.0, "perro")]
    return Factura(numero=numero, fecha=fecha, cliente_nombre=cliente, lineas=lineas)


def _pago(total=20.0, metodo="efectivo"):
    return PagoInfo(total, total, 0.0, metodo, total, 0.0)


class TestInicializar:
    def test_crea_tablas(self):
        inicializar_db_ventas()
        import sqlite3
        import src.ventas_store as vs
        conn = sqlite3.connect(vs.RUTA_DB_VENTAS)
        tablas = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        assert {"ventas", "ajustes"} <= tablas

    def test_idempotente(self):
        inicializar_db_ventas()
        inicializar_db_ventas()  # no debe lanzar error


class TestRegistrarFactura:
    def test_inserta_lineas(self):
        f = _factura(lineas=[LineaFactura("A", 1, 5.0, "gato"), LineaFactura("B", 2, 3.0, "ave")])
        registrar_ventas_factura(f, "Giselle", _pago(11.0))
        filas = historial_ventas("2026-06-01", "2026-06-30")
        assert len(filas) == 1
        assert filas[0]["monto_lineas"] == 11

    def test_guarda_metodo_pago(self):
        registrar_ventas_factura(_factura(), "Giselle", _pago(20.0, "tarjeta"))
        filas = historial_ventas("2026-06-01", "2026-06-30")
        assert filas[0]["metodo_pago"] == "tarjeta"

    def test_categorias_concatenadas(self):
        f = _factura(lineas=[LineaFactura("A", 1, 5.0, "perro"), LineaFactura("B", 1, 5.0, "gato")])
        registrar_ventas_factura(f, "u", _pago(10.0))
        filas = historial_ventas("2026-06-01", "2026-06-30")
        cats = filas[0]["categorias"]
        assert "perro" in cats and "gato" in cats


class TestHistorialVentas:
    def test_filtra_por_fecha(self):
        registrar_ventas_factura(_factura(fecha=date(2026, 5, 10)), "u", _pago(20.0))
        registrar_ventas_factura(_factura(numero=2, fecha=date(2026, 6, 15)), "u", _pago(20.0))
        filas = historial_ventas("2026-06-01", "2026-06-30")
        assert len(filas) == 1

    def test_filtra_por_categoria(self):
        f1 = _factura(numero=1, lineas=[LineaFactura("x", 1, 10.0, "perro")])
        f2 = _factura(numero=2, lineas=[LineaFactura("y", 1, 10.0, "gato")])
        registrar_ventas_factura(f1, "u", _pago(10.0))
        registrar_ventas_factura(f2, "u", _pago(10.0))
        filas = historial_ventas("2026-06-01", "2026-06-30", categoria="perro")
        assert len(filas) == 1

    def test_filtra_por_metodo_pago(self):
        registrar_ventas_factura(_factura(numero=1), "u", _pago(20.0, "efectivo"))
        registrar_ventas_factura(_factura(numero=2), "u", _pago(20.0, "tarjeta"))
        filas = historial_ventas("2026-06-01", "2026-06-30", metodo_pago="tarjeta")
        assert len(filas) == 1


class TestResumen:
    def test_totales_mensuales(self):
        registrar_ventas_factura(_factura(numero=1, lineas=[LineaFactura("A", 1, 30.0, "perro")]), "u", _pago(30.0, "efectivo"))
        registrar_ventas_factura(_factura(numero=2, lineas=[LineaFactura("B", 1, 20.0, "gato")]), "u", _pago(20.0, "tarjeta"))
        r = resumen_ventas_activas("2026-06")
        assert r["total_bruto"] == 50.0
        assert r["cantidad_ventas"] == 2
        assert r["total_efectivo"] == 30.0
        assert r["total_tarjeta"] == 20.0

    def test_por_categoria(self):
        registrar_ventas_factura(_factura(lineas=[LineaFactura("A", 2, 5.0, "perro")]), "u", _pago(10.0))
        r = resumen_ventas_activas("2026-06")
        assert r["por_categoria"]["perro"] == 10.0

    def test_resumen_dia(self):
        registrar_ventas_factura(_factura(fecha=date(2026, 6, 15)), "u", _pago(20.0))
        r = resumen_ventas_dia("2026-06-15")
        assert r["total"] == 20.0
        assert r["cantidad_ventas"] == 1

    def test_dia_sin_ventas(self):
        r = resumen_ventas_dia("2026-06-01")
        assert r["total"] == 0.0
        assert r["cantidad_ventas"] == 0

    def test_resumen_dia_incluye_factura_y_ticket(self):
        hoy = date.today()
        registrar_ventas_factura(
            _factura(numero=1, fecha=hoy, lineas=[LineaFactura("A", 1, 12.0, "perro")]),
            "u",
            _pago(12.0, "efectivo"),
        )
        registrar_ventas_ticket(2, [("perro", 8.0)], "u", "tarjeta")
        r = resumen_ventas_dia(hoy.isoformat())
        assert r["total"] == 20.0
        assert r["cantidad_ventas"] == 2


class TestDetalle:
    def test_detalle_mensual(self):
        registrar_ventas_factura(_factura(lineas=[LineaFactura("A", 1, 5.0, "perro"), LineaFactura("B", 1, 3.0, "gato")]), "u", _pago(8.0))
        filas = ventas_activas_detalle("2026-06")
        assert len(filas) == 2

    def test_ajustes_vacios(self):
        ajustes = listar_ajustes_activos("2026-06")
        assert ajustes == []
