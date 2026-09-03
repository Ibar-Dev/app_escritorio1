# main.py — App de escritorio de Zoo Picasso
# Tickets (TPV), facturas en Excel, control de ventas y envio de facturas por email.
# Ejecutar: uv run main.py  (desde esta carpeta)

import flet as ft

from bootstrap import ensure_data_dirs, ensure_project_paths

ensure_project_paths()
ensure_data_dirs()

import src.settings  # noqa: E402  # logging centralizado y rutas

from ui.email_view import EmailView  # noqa: E402
from ui.facturas_view import FacturasView  # noqa: E402
from ui.tickets_view import TicketsView  # noqa: E402
from ui.ventas_view import VentasView  # noqa: E402

_OPERADORA = "Giselle"

_TABS = [
    ("Tickets", ft.Icons.RECEIPT_LONG),
    ("Facturas", ft.Icons.DESCRIPTION),
    ("Ventas", ft.Icons.BAR_CHART),
    ("Configuración", ft.Icons.SETTINGS),
]


def main(page: ft.Page):
    page.title = "Zoo Picasso - App de escritorio"
    page.window.width = 1180
    page.window.height = 800
    page.padding = 16

    # Las vistas se crean una sola vez y conservan su estado al cambiar de pestana.
    vista_tickets = TicketsView(page, _OPERADORA)
    vista_facturas = FacturasView(page, _OPERADORA)
    vista_ventas = VentasView(page)
    vista_email = EmailView(page)

    contenedor = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    # Construimos las interfaces visuales una sola vez para evitar duplicar controles en el árbol.
    vistas_ui = {
        0: vista_tickets.construir(),
        1: vista_facturas.construir(),
        2: vista_ventas.construir(),
        3: vista_email.construir(),
    }

    def _mostrar(indice: int) -> None:
        contenedor.controls = [vistas_ui[indice]]

        if indice == 2:
            vista_ventas.actualizar_resumen()
            vista_ventas.buscar()

        page.update()

    def cambiar_pestana(e: ft.ControlEvent) -> None:
        _mostrar(e.control.selected_index)

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=160,
        destinations=[
            ft.NavigationRailDestination(
                icon=icon,
                selected_icon=icon,
                label=nombre,
            )
            for nombre, icon in _TABS
        ],
        on_change=cambiar_pestana,
        expand=True,
    )

    page.add(ft.Row(controls=[rail, ft.VerticalDivider(width=1), contenedor], expand=True))
    _mostrar(0)
    page.update()


if __name__ == "__main__":
    ft.run(main)