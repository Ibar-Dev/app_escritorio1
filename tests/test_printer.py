"""Tests para tickets_src.printer — formato y filtrado de lineas."""
from __future__ import annotations

from tickets_src.printer import _imprimir
from tickets_src.ticket_model import LineaTicket, Ticket


def _texto_emitido(fake_printer) -> str:
    partes: list[str] = []
    for call in fake_printer.text.call_args_list:
        if call.args:
            partes.append(call.args[0])
    return "".join(partes)


def test_imprime_subtotal_metodo_y_total(mock_escpos):
    ticket = Ticket(
        numero=7,
        lineas=[LineaTicket("Comida", 1, 12.0)],
        metodo_pago="efectivo",
    )

    _imprimir(ticket)

    texto = _texto_emitido(mock_escpos)
    assert "SUBTOTAL" in texto
    assert "METODO PAGO" in texto
    assert "EFECTIVO" in texto
    assert "TOTAL" in texto


def test_filtra_lineas_vacias_o_espacios(mock_escpos):
    ticket = Ticket(
        numero=8,
        lineas=[
            LineaTicket("Comida", 1, 5.0),
            LineaTicket("", 1, 3.0),
            LineaTicket("   ", 1, 4.0),
            LineaTicket("Accesorios", 1, 6.0),
        ],
    )

    _imprimir(ticket)

    texto = _texto_emitido(mock_escpos)
    assert "Comida" in texto
    assert "Accesorios" in texto
    assert "\n                      3.00\n" not in texto
    assert "\n                      4.00\n" not in texto


def test_metodo_pago_vacio_usa_default_efectivo(mock_escpos):
    ticket = Ticket(
        numero=9,
        lineas=[LineaTicket("Chuches", 1, 3.0)],
        metodo_pago="",
    )

    _imprimir(ticket)

    texto = _texto_emitido(mock_escpos)
    assert "METODO PAGO" in texto
    assert "EFECTIVO" in texto


def test_filtra_lineas_con_valor_cero(mock_escpos):
    ticket = Ticket(
        numero=10,
        lineas=[
            LineaTicket("Comida", 1, 7.0),
            LineaTicket("Promo", 1, 0.0),
        ],
        metodo_pago="tarjeta",
    )

    _imprimir(ticket)

    texto = _texto_emitido(mock_escpos)
    assert "Comida" in texto
    assert "Promo" not in texto
    assert "TARJETA" in texto
