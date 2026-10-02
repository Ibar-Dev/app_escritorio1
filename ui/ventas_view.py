import logging
import calendar
import threading
import time
from datetime import date, timedelta

import flet as ft

from escritorio.categorias import CATEGORIAS, METODOS_PAGO
from ui.thread_utils import ejecutar_en_hilo_seguro
from escritorio.reportes import generar_reporte_historial, generar_reporte_mensual
from src.ventas_store import (
    historial_ventas,
    resumen_ventas_dia,
    resumen_ventas_rango,
)

logger = logging.getLogger(__name__)

_COLUMNAS = [
    ft.DataColumn(label=ft.Text("Nº", weight=ft.FontWeight.BOLD)),
    ft.DataColumn(label=ft.Text("Fecha", weight=ft.FontWeight.BOLD)),
    ft.DataColumn(label=ft.Text("Cliente", weight=ft.FontWeight.BOLD)),
    ft.DataColumn(label=ft.Text("Categorías", weight=ft.FontWeight.BOLD)),
    ft.DataColumn(label=ft.Text("Total (€)", weight=ft.FontWeight.BOLD), numeric=True),
    ft.DataColumn(label=ft.Text("Pago", weight=ft.FontWeight.BOLD)),
    ft.DataColumn(label=ft.Text("Estado", weight=ft.FontWeight.BOLD)),
]


class VentasView:
    """Pestana de control de ventas: resumen, historial y exportacion a Excel."""

    _REFRESH_HOY_SEGUNDOS = 30

    def __init__(self, page: ft.Page):
        self.page = page
        self.ultima_busqueda: list[dict] = []
        self._refresh_hoy_activo = threading.Event()
        self._refresh_hoy_hilo: threading.Thread | None = None

        hoy = date.today()
        self.txt_desde = ft.TextField(label="Desde (AAAA-MM-DD)", value=(hoy - timedelta(days=30)).isoformat(), width=150)
        self.txt_hasta = ft.TextField(label="Hasta (AAAA-MM-DD)", value=hoy.isoformat(), width=150)
        self.dd_categoria = ft.Dropdown(
            label="Categoría",
            width=160,
            options=[ft.dropdown.Option(key="", text="Todas")] + [ft.dropdown.Option(key=v, text=v) for v in CATEGORIAS],
        )
        self.dd_pago = ft.Dropdown(
            label="Método de pago",
            width=150,
            options=[ft.dropdown.Option(key="", text="Todos")] + [ft.dropdown.Option(key=v, text=v.capitalize()) for v in METODOS_PAGO],
        )

        self.lbl_resumen_hoy = ft.Text(value="—", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
        self.lbl_hoy_meta = ft.Text(value="Actualiza cada 30s", size=11, color=ft.Colors.GREY_700)
        self.lbl_total_mes = ft.Text(value="—", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800)
        self.lbl_ventas_mes = ft.Text(value="—", size=13)
        self.lbl_efectivo = ft.Text(value="—", size=13)
        self.lbl_tarjeta = ft.Text(value="—", size=13)
        self.lbl_periodo = ft.Text(value="Periodo: —", size=11, color=ft.Colors.GREY_700)
        self.lbl_total_mes_cal = ft.Text(value="—", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_800)
        self.lbl_ventas_mes_cal = ft.Text(value="—", size=13)
        self.lbl_efectivo_mes_cal = ft.Text(value="—", size=13)
        self.lbl_tarjeta_mes_cal = ft.Text(value="—", size=13)
        self.lbl_periodo_mes_cal = ft.Text(value="Periodo: —", size=11, color=ft.Colors.GREY_700)
        self.tabla = ft.DataTable(columns=_COLUMNAS, rows=[], border=ft.Border.all(1, ft.Colors.GREY_300), border_radius=8)
        self.contenedor_tabla = ft.Column(controls=[self.tabla], scroll=ft.ScrollMode.AUTO)
        self.lbl_estado = ft.Text(value="", size=13)

    def construir(self) -> ft.Control:
        self.actualizar_resumen_hoy()
        self.buscar()
        filtros = ft.Row(
            controls=[
                self.txt_desde,
                self.txt_hasta,
                self.dd_categoria,
                self.dd_pago,
                ft.Button("Buscar", icon=ft.Icons.SEARCH, on_click=self.buscar),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=8,
        )
        tarjetas = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("VENTAS DE HOY", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                            self.lbl_resumen_hoy,
                            self.lbl_hoy_meta,
                        ],
                        spacing=2,
                    ),
                    padding=12,
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50,
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("TOTAL DEL RANGO", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                            self.lbl_total_mes,
                            self.lbl_ventas_mes,
                            self.lbl_periodo,
                            ft.Row(
                                controls=[
                                    ft.Text("Efectivo:", size=12),
                                    self.lbl_efectivo,
                                    ft.Text("Tarjeta:", size=12),
                                    self.lbl_tarjeta,
                                ],
                                spacing=6,
                            ),
                        ],
                        spacing=2,
                    ),
                    padding=12,
                    border_radius=8,
                    bgcolor=ft.Colors.GREEN_50,
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("MES CALENDARIO ACTUAL", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                            self.lbl_total_mes_cal,
                            self.lbl_ventas_mes_cal,
                            self.lbl_periodo_mes_cal,
                            ft.Row(
                                controls=[
                                    ft.Text("Efectivo:", size=12),
                                    self.lbl_efectivo_mes_cal,
                                    ft.Text("Tarjeta:", size=12),
                                    self.lbl_tarjeta_mes_cal,
                                ],
                                spacing=6,
                            ),
                        ],
                        spacing=2,
                    ),
                    padding=12,
                    border_radius=8,
                    bgcolor=ft.Colors.ORANGE_50,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=12,
            wrap=True,
        )
        exportar = ft.Row(
            controls=[
                ft.Button("Exportar reporte del mes (Excel)", icon=ft.Icons.DESCRIPTION, on_click=self.exportar_mes),
                ft.OutlinedButton("Exportar historial filtrado (Excel)", icon=ft.Icons.TABLE_VIEW, on_click=self.exportar_historial),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=8,
        )
        return ft.Column(
            controls=[
                ft.Text("CONTROL DE VENTAS", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                ft.Divider(),
                tarjetas,
                ft.Divider(),
                filtros,
                ft.Divider(),
                self.contenedor_tabla,
                ft.Divider(),
                exportar,
                self.lbl_estado,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _fecha_valida(self, texto: str) -> str:
        try:
            date.fromisoformat(texto.strip())
        except ValueError as e:
            raise ValueError("Las fechas deben tener formato AAAA-MM-DD.") from e
        return texto.strip()

    def _filtros_actuales(self) -> tuple[str, str, str | None, str | None]:
        desde = self._fecha_valida(self.txt_desde.value)
        hasta = self._fecha_valida(self.txt_hasta.value)
        if desde > hasta:
            raise ValueError("La fecha 'desde' no puede ser mayor que 'hasta'.")
        return desde, hasta, self.dd_categoria.value or None, self.dd_pago.value or None

    def on_view_activated(self) -> None:
        self.actualizar_resumen_hoy()
        self.buscar()
        self._iniciar_refresh_hoy()

    def on_view_deactivated(self) -> None:
        self._detener_refresh_hoy()

    def _iniciar_refresh_hoy(self) -> None:
        if self._refresh_hoy_hilo and self._refresh_hoy_hilo.is_alive():
            return
        self._refresh_hoy_activo.set()

        def _loop() -> None:
            while self._refresh_hoy_activo.is_set():
                time.sleep(self._REFRESH_HOY_SEGUNDOS)
                if not self._refresh_hoy_activo.is_set():
                    break
                self.actualizar_resumen_hoy()

        self._refresh_hoy_hilo = threading.Thread(target=_loop, daemon=True)
        self._refresh_hoy_hilo.start()

    def _detener_refresh_hoy(self) -> None:
        self._refresh_hoy_activo.clear()

    def actualizar_resumen_hoy(self) -> None:
        def _cargar() -> None:
            try:
                hoy = resumen_ventas_dia(date.today().isoformat())
                self.lbl_resumen_hoy.value = f"{hoy['total']:.2f} € ({hoy['cantidad_ventas']} ventas)"
            except Exception as e:
                logger.error("Error al calcular ventas del dia: %s", e)
            self.page.update()

        ejecutar_en_hilo_seguro(self.page, _cargar)

    def _actualizar_resumen_rango(self, desde: str, hasta: str, categoria: str | None, metodo_pago: str | None) -> None:
        resumen = resumen_ventas_rango(desde, hasta, categoria, metodo_pago)
        self.lbl_total_mes.value = f"{resumen['total']:.2f} €"
        self.lbl_ventas_mes.value = f"{resumen['cantidad_ventas']} ventas registradas"
        self.lbl_efectivo.value = f"{resumen['total_efectivo']:.2f} €"
        self.lbl_tarjeta.value = f"{resumen['total_tarjeta']:.2f} €"
        self.lbl_periodo.value = f"Periodo: {desde} a {hasta}"

    def _periodo_mes_actual(self) -> tuple[str, str]:
        hoy = date.today()
        inicio = hoy.replace(day=1)
        ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
        fin = hoy.replace(day=ultimo_dia)
        return inicio.isoformat(), fin.isoformat()

    def _actualizar_resumen_mes_calendario(self, categoria: str | None, metodo_pago: str | None) -> None:
        desde_mes, hasta_mes = self._periodo_mes_actual()
        resumen = resumen_ventas_rango(desde_mes, hasta_mes, categoria, metodo_pago)
        self.lbl_total_mes_cal.value = f"{resumen['total']:.2f} €"
        self.lbl_ventas_mes_cal.value = f"{resumen['cantidad_ventas']} ventas registradas"
        self.lbl_efectivo_mes_cal.value = f"{resumen['total_efectivo']:.2f} €"
        self.lbl_tarjeta_mes_cal.value = f"{resumen['total_tarjeta']:.2f} €"
        self.lbl_periodo_mes_cal.value = f"Periodo: {desde_mes} a {hasta_mes}"

    def actualizar_resumen(self):
        self.actualizar_resumen_hoy()
        try:
            desde, hasta, categoria, metodo_pago = self._filtros_actuales()
        except ValueError as e:
            self._estado(str(e), ft.Colors.RED_600)
            return

        def _cargar() -> None:
            try:
                self._actualizar_resumen_rango(desde, hasta, categoria, metodo_pago)
                self._actualizar_resumen_mes_calendario(categoria, metodo_pago)
            except Exception as e:
                logger.error("Error al calcular resumen de rango: %s", e)
            self.page.update()

        ejecutar_en_hilo_seguro(self.page, _cargar)

    def buscar(self, _=None):
        try:
            desde, hasta, categoria, metodo_pago = self._filtros_actuales()
        except ValueError as e:
            self._estado(str(e), ft.Colors.RED_600)
            return
        self._estado("Buscando…", ft.Colors.BLUE_700)

        def _consultar():
            try:
                filas = historial_ventas(
                    desde,
                    hasta,
                    categoria,
                    metodo_pago,
                )
                self._actualizar_resumen_rango(desde, hasta, categoria, metodo_pago)
                self._actualizar_resumen_mes_calendario(categoria, metodo_pago)
            except Exception as e:
                self._estado(f"Error al consultar el historial: {e}", ft.Colors.RED_600)
                return
            self.ultima_busqueda = filas
            self.tabla.rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(f["numero_factura"]))),
                        ft.DataCell(ft.Text(str(f["fecha_venta"]))),
                        ft.DataCell(ft.Text(str(f["cliente_nombre"] or "—"))),
                        ft.DataCell(ft.Text(str(f["categorias"] or "—"))),
                        ft.DataCell(ft.Text(f"{f['monto_lineas']:.2f}")),
                        ft.DataCell(ft.Text(str(f["metodo_pago"] or "—"))),
                        ft.DataCell(ft.Text(str(f["estado"] or "—"))),
                    ]
                )
                for f in filas
            ]
            self._estado(f"{len(filas)} ventas en el periodo {desde} a {hasta}.", ft.Colors.BLUE_700)
            self.page.update()

        ejecutar_en_hilo_seguro(self.page, _consultar)

    def exportar_mes(self, _=None):
        self._estado("Generando reporte mensual…", ft.Colors.BLUE_700)

        def _exportar():
            try:
                mes = date.today().strftime("%Y-%m")
                ruta = generar_reporte_mensual(mes)
                self._estado(f"✓ Reporte del mes guardado en: {ruta}", ft.Colors.GREEN_700)
            except Exception as e:
                self._estado(f"Error al generar el reporte: {e}", ft.Colors.RED_600)
                logger.error("Error al exportar reporte mensual: %s", e, exc_info=True)

        ejecutar_en_hilo_seguro(self.page, _exportar)

    def exportar_historial(self, _=None):
        if not self.ultima_busqueda:
            self._estado("Primero haz una búsqueda para exportar su resultado.", ft.Colors.ORANGE_700)
            return
        self._estado("Exportando historial…", ft.Colors.BLUE_700)

        def _exportar():
            try:
                ruta = generar_reporte_historial(self.ultima_busqueda)
                self._estado(f"✓ Historial exportado en: {ruta}", ft.Colors.GREEN_700)
            except Exception as e:
                self._estado(f"Error al exportar el historial: {e}", ft.Colors.RED_600)
                logger.error("Error al exportar historial: %s", e, exc_info=True)

        ejecutar_en_hilo_seguro(self.page, _exportar)

    def _estado(self, mensaje: str, color: str):
        self.lbl_estado.value = mensaje
        self.lbl_estado.color = color
        self.page.update()