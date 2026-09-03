"""Tests para los contadores persistentes (factura y ticket)."""
from __future__ import annotations

import pytest


class TestFacturaCounter:
    def test_primer_numero_es_uno(self):
        from src.factura_counter import siguiente_numero_factura
        assert siguiente_numero_factura() == 1

    def test_incrementa_entre_llamadas(self):
        from src.factura_counter import siguiente_numero_factura
        a = siguiente_numero_factura()
        b = siguiente_numero_factura()
        assert b == a + 1

    def test_peek_no_incrementa(self):
        from src.factura_counter import peek_siguiente_numero_factura, siguiente_numero_factura
        n = peek_siguiente_numero_factura()
        assert peek_siguiente_numero_factura() == n
        assert siguiente_numero_factura() == n

    def test_rollback_restaura_numero(self):
        from src.factura_counter import rollback_numero_factura, siguiente_numero_factura
        n = siguiente_numero_factura()
        rollback_numero_factura()
        assert siguiente_numero_factura() == n

    def test_persiste_en_disco(self, tmp_data_dir):
        import importlib
        import src.factura_counter as fc
        fc.siguiente_numero_factura()  # escribe 2 en disco
        # Simular reinicio: forzar re-lectura
        importlib.reload(fc)
        # El monkeypatch ya apunta al tmp_path correcto — pero _ARCHIVO se fija en conftest
        n = fc.siguiente_numero_factura()
        assert n == 2


class TestTicketCounter:
    def test_primer_numero_es_uno(self):
        from tickets_src.counter import siguiente_numero
        assert siguiente_numero() == 1

    def test_incrementa_entre_llamadas(self):
        from tickets_src.counter import siguiente_numero
        a = siguiente_numero()
        b = siguiente_numero()
        assert b == a + 1

    def test_peek_no_incrementa(self):
        from tickets_src.counter import peek_siguiente, siguiente_numero
        n = peek_siguiente()
        assert peek_siguiente() == n
        assert siguiente_numero() == n

    def test_rollback_restaura_numero(self):
        from tickets_src.counter import rollback, siguiente_numero
        n = siguiente_numero()
        rollback()
        assert siguiente_numero() == n
