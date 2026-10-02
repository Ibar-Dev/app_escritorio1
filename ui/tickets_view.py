import logging
from datetime import date
from decimal import Decimal
from typing import Callable

import flet as ft

from escritorio.categorias import CATEGORIAS
from src.money import parse
from src.ventas_store import resumen_ventas_dia
from escritorio.registro import registrar_ventas_ticket
from escritorio.categorias import METODOS_PAGO
from tickets_src.counter import peek_siguiente, rollback, siguiente_numero
from tickets_src.excel_writer import guardar_ticket
from tickets_src.printer import imprimir_ticket
from tickets_src.ticket_model import LineaTicket, Ticket

logger = logging.getLogger(__name__)


class FilaServicio:
    """Una linea de servicio del ticket, con su categoria para el control de ventas."""

    def __init__(self, on_change: Callable[[], None]):
        self.nombre = ft.TextField(
            label="Servicio",
            width=240,
            on_change=lambda _: on_change(),
        )
        self.cantidad = ft.TextField(
            label="Cant.",
            value="1",
            width=70,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda _: self._recalcular(on_change),
        )
        self.precio = ft.TextField(
            label="P. Unit. (EUR)",
            value="0.00",
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda _: self._recalcular(on_change),
        )
        self.total = ft.TextField(
            label="Total",
            value="0.00",
            width=100,
            read_only=True,
            bgcolor=ft.Colors.GREY_200,
        )
        self.categoria = ft.Dropdown(
            label="Categoría",
            width=150,
            options=[ft.dropdown.Option(key=v, text=v) for v in CATEGORIAS],
        )

    def _recalcular(self, on_change: Callable[[], None]):
        try:
            cantidad = int(self.cantidad.value)
            precio = float(self.precio.value.replace(",", "."))
            self.total.value = f"{round(cantidad * precio, 2):.2f}"
        except ValueError:
            self.total.value = "0.00"
        on_change()

    def como_row(self) -> ft.Row:
        return ft.Row(
            controls=[self.nombre, self.cantidad, self.precio, self.total, self.categoria],
            alignment=ft.MainAxisAlignment.START,
            spacing=8,
        )

    def a_linea_ticket(self) -> LineaTicket:
        nombre = self.nombre.value.strip()
        if not nombre:
            raise ValueError("El nombre del servicio no puede estar vacio.")
        cantidad = int(self.cantidad.value)
        precio = float(self.precio.value.replace(",", "."))
        return LineaTicket(nombre=nombre, cantidad=cantidad, precio_unitario=precio)


class TicketsView:
    """Pestana de tickets (TPV): genera, guarda en Excel, imprime y registra la venta."""

    def __init__(self, page: ft.Page, usuario: str = ""):
        self.page = page
        self.usuario = usuario
        self.filas: list[FilaServicio] = []
        self.numero_ticket = peek_siguiente()

        self.contenedor_filas = ft.Column(spacing=6)
        self.lbl_numero = ft.Text(
            value=f"Ticket #{self.numero_ticket:04d}",
            size=13,
            color=ft.Colors.GREY_700,
        )
        self.lbl_total = ft.Text(
            value="0.00 EUR",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_700,
        )
        self.lbl_estado = ft.Text(value="", size=13)
        self.lbl_acumulado_dia = ft.Text(
            value="0.00 EUR",
            size=15,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_700,
        )
        self.total_dia: Decimal = Decimal("0.00")
        self.tickets_dia = 0
        self.lbl_tickets_dia = ft.Text(value="0", size=15, weight=ft.FontWeight.BOLD)
        self.dd_metodo_pago = ft.Dropdown(
            label="Metodo de pago",
            width=180,
            value="efectivo",
            options=[ft.dropdown.Option(key=v, text=v.capitalize()) for v in METODOS_PAGO],
        )
        self.atajos_rapidos: list[tuple[str, str]] = [
            ("Comida", "animal"),
            ("Chuches", "animal"),
            ("Accesorios", "animal"),
            ("Peluquería", "peluqueria"),
            ("Veterinaria", "animal"),
        ]
        self.switch_imprimir = ft.Switch(label="Imprimir ticket en papel", value=False)
        self._refrescar_resumen_dia()

    # ── Construccion ──────────────────────────────────────────────────────────
    def construir(self) -> ft.Control:
        self._refrescar_resumen_dia()
        if not self.filas:
            self.agregar_fila()
        cabecera = ft.Column(
            controls=[
                ft.Text("TICKETS", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
                self.lbl_numero,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
        )
        botones_filas = ft.Row(
            controls=[
                ft.Button("+ Añadir línea", icon=ft.Icons.ADD, on_click=self.agregar_fila),
                ft.OutlinedButton("- Quitar línea", icon=ft.Icons.REMOVE, on_click=self.quitar_fila),
            ],
            alignment=ft.MainAxisAlignment.START,
        )
        fila_atajos = ft.Row(
            controls=[
                ft.Text("Atajos:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                *[
                    ft.OutlinedButton(
                        concepto,
                        on_click=lambda _, c=concepto, cat=categoria: self._agregar_atajo(c, cat),
                    )
                    for concepto, categoria in self.atajos_rapidos
                ],
            ],
            spacing=6,
            wrap=True,
        )
        fila_total = ft.Row(
            controls=[
                ft.Text("TOTAL:", size=18, weight=ft.FontWeight.BOLD),
                self.lbl_total,
            ],
            alignment=ft.MainAxisAlignment.END,
        )
        resumen_dia = ft.Row(
            controls=[
                ft.Text("TICKETS DEL DÍA:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                self.lbl_tickets_dia,
                ft.Text("ACUMULADO DEL DÍA:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                self.lbl_acumulado_dia,
            ],
            alignment=ft.MainAxisAlignment.END,
            spacing=8,
        )
        self.boton_guardar = ft.Button(
            "GUARDAR VENTA",
            icon=ft.Icons.SAVE,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            height=52,
            width=320,
            on_click=self.guardar,
        )
        return ft.Column(
            controls=[
                cabecera,
                ft.Divider(),
                self.contenedor_filas,
                fila_atajos,
                botones_filas,
                ft.Divider(),
                fila_total,
                ft.Row(
                    controls=[self.dd_metodo_pago, self.switch_imprimir],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(),
                resumen_dia,
                ft.Divider(),
                ft.Row([self.boton_guardar], alignment=ft.MainAxisAlignment.CENTER),
                self.lbl_estado,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # ── Acciones ──────────────────────────────────────────────────────────────
    def actualizar_total(self):
        try:
            total = sum(float(f.total.value) for f in self.filas)
            self.lbl_total.value = f"{total:.2f} EUR"
        except ValueError:
            self.lbl_total.value = "0.00 EUR"
        self.page.update()

    def agregar_fila(self, _=None):
        fila = FilaServicio(on_change=self.actualizar_total)
        self.filas.append(fila)
        self.contenedor_filas.controls.append(fila.como_row())
        self.page.update()

    def quitar_fila(self, _=None):
        if len(self.filas) <= 1:
            self._estado("El ticket debe tener al menos una línea.", ft.Colors.ORANGE_700)
            return
        self.filas.pop()
        self.contenedor_filas.controls.pop()
        self.actualizar_total()

    def resetear(self):
        self.filas.clear()
        self.contenedor_filas.controls.clear()
        self.numero_ticket = peek_siguiente()
        self.lbl_numero.value = f"Ticket #{self.numero_ticket:04d}"
        self.lbl_estado.value = ""
        self.dd_metodo_pago.value = "efectivo"
        self.switch_imprimir.value = False
        self.boton_guardar.disabled = False
        self.agregar_fila()
        self.actualizar_total()

    def _estado(self, mensaje: str, color: str):
        self.lbl_estado.value = mensaje
        self.lbl_estado.color = color
        self.page.update()

    def _refrescar_resumen_dia(self):
        resumen = resumen_ventas_dia(date.today().isoformat())
        self.total_dia = parse(resumen["total"])
        self.tickets_dia = int(resumen["cantidad_ventas"])
        self.lbl_tickets_dia.value = str(self.tickets_dia)
        self.lbl_acumulado_dia.value = f"{self.total_dia:.2f} EUR"

    def _agregar_atajo(self, nombre_servicio: str, categoria: str):
        self.agregar_fila()
        fila = self.filas[-1]
        fila.nombre.value = nombre_servicio
        if categoria in CATEGORIAS:
            fila.categoria.value = categoria
        fila._recalcular(self.actualizar_total)
        self.page.update()

    def guardar(self, _=None):
        try:
            lineas = [f.a_linea_ticket() for f in self.filas]
        except ValueError as e:
            self._estado(str(e), ft.Colors.RED_600)
            return

        self.boton_guardar.disabled = True
        self.page.update()
        numero = siguiente_numero()
        self.numero_ticket = numero
        self.lbl_numero.value = f"Ticket #{numero:04d}"
        ticket = Ticket(
            numero=numero,
            lineas=lineas,
            metodo_pago=(self.dd_metodo_pago.value or "").strip().lower(),
        )

        try:
            guardar_ticket(ticket)
        except Exception as e:
            rollback()
            self.boton_guardar.disabled = False
            self._estado(f"Error al guardar en Excel: {e}", ft.Colors.RED_600)
            logger.error("Error al guardar ticket #%s: %s", ticket.numero, e)
            return

        aviso_bd: str | None = None
        try:
            registrar_ventas_ticket(
                ticket.numero,
                [
                    (fila.categoria.value, linea.total)
                    for fila, linea in zip(self.filas, lineas)
                ],
                self.usuario,
                ticket.metodo_pago,
            )
        except Exception as e:
            logger.error("No se pudo registrar la venta del ticket #%s: %s", ticket.numero, e)
            aviso_bd = f"⚠ Ticket guardado, pero venta no registrada en BD: {e}"

        aviso_print: str | None = None
        if self.switch_imprimir.value:
            try:
                imprimir_ticket(ticket)
            except ConnectionError as e:
                aviso_print = f"⚠ Ticket guardado, pero error de impresora: {e}"
            except Exception as e:
                aviso_print = f"⚠ Ticket guardado, pero error al imprimir: {e}"

        self._refrescar_resumen_dia()
        self.resetear()
        if aviso_bd and aviso_print:
            self._estado(f"{aviso_bd} | {aviso_print}", ft.Colors.ORANGE_700)
        elif aviso_bd:
            self._estado(aviso_bd, ft.Colors.ORANGE_700)
        elif aviso_print:
            self._estado(aviso_print, ft.Colors.ORANGE_700)
        elif self.switch_imprimir.value:
            self._estado(f"✓ Ticket #{ticket.numero:04d} guardado e impreso correctamente.", ft.Colors.GREEN_700)
        else:
            self._estado(f"✓ Ticket #{ticket.numero:04d} guardado correctamente.", ft.Colors.GREEN_700)