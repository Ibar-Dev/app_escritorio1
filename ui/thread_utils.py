"""
Utilidades centralizadas para ejecutar tareas bloqueantes en hilos seguros.
Proporciona manejo automático de excepciones y notificación en la UI de Flet.
"""
import logging
import queue
import threading
import traceback
from typing import Callable

import flet as ft

logger = logging.getLogger(__name__)

_cola_tareas_ui: queue.Queue[Callable[[], None]] = queue.Queue()


def _mostrar_snackbar_error(page: ft.Page, error_msg: str) -> None:
    color_error = getattr(ft.Colors, "ERROR", None) or getattr(ft.Colors, "RED_700", None) or ft.Colors.RED
    page.open(
        ft.SnackBar(
            content=ft.Text(error_msg, color=ft.Colors.WHITE),
            bgcolor=color_error,
        )
    )
    page.update()


def ejecutar_en_hilo_ui(page: ft.Page, tarea_ui: Callable[[], None]) -> None:
    """Ejecuta una tarea de UI en el hilo principal cuando sea posible.

    Si la API call_from_thread está disponible, se usa de inmediato.
    Si no, la tarea se encola para drenarla desde el hilo principal.
    """
    call_from_thread = getattr(page, "call_from_thread", None)
    if callable(call_from_thread):
        try:
            call_from_thread(tarea_ui)
            return
        except Exception:
            logger.exception("Fallo al despachar tarea UI con call_from_thread")
    _cola_tareas_ui.put(tarea_ui)


def drenar_tareas_ui_pendientes() -> int:
    """Procesa tareas UI encoladas y retorna cuántas se ejecutaron."""
    procesadas = 0
    while True:
        try:
            tarea = _cola_tareas_ui.get_nowait()
        except queue.Empty:
            break
        try:
            tarea()
            procesadas += 1
        except Exception:
            logger.exception("Fallo al ejecutar tarea UI encolada")
    return procesadas


def ejecutar_en_hilo_seguro(page: ft.Page, funcion_objetivo: Callable, *args, **kwargs):
    """
    DOCSTRING:
    Envuelve la ejecución de una función bloqueante (I/O, Base de Datos, Excel) en un hilo
    separado, garantizando que cualquier excepción sea capturada y mostrada en la UI de Flet.

    Parámetros:
    - page: Instancia actual de ft.Page para poder actualizar la interfaz.
    - funcion_objetivo: La función pesada que debe ejecutarse.
    - *args, **kwargs: Argumentos dinámicos que requiera la funcion_objetivo.

    Ejemplo de uso:
        ejecutar_en_hilo_seguro(self.page, self.generar_factura_pdf)
        ejecutar_en_hilo_seguro(self.page, self.guardar_en_bd, factura_id, datos_cliente)
    """

    def wrapper():
        try:
            # Ejecutamos la lógica original de tu aplicación de forma normal.
            funcion_objetivo(*args, **kwargs)

        except Exception as e:
            # Capturamos el error genérico para que el hilo no muera silenciosamente.
            # Imprimimos el error completo en consola para el log del desarrollador (trazabilidad).
            print(f"Error crítico en el hilo: {funcion_objetivo.__name__}")
            print(traceback.format_exc())

            # Notificamos a la UI insertando un mensaje en el hilo principal de Flet.
            # Usamos un SnackBar rojo para indicar fallo.
            error_msg = f"Error en la operación: {str(e)}"
            ejecutar_en_hilo_ui(page, lambda: _mostrar_snackbar_error(page, error_msg))

    # Lanzamos el hilo en modo daemon para que muera si se cierra la app principal.
    threading.Thread(target=wrapper, daemon=True).start()
