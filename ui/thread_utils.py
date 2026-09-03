"""
Utilidades centralizadas para ejecutar tareas bloqueantes en hilos seguros.
Proporciona manejo automático de excepciones y notificación en la UI de Flet.
"""
import threading
import traceback
from typing import Callable

import flet as ft


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
            page.open(
                ft.SnackBar(
                    content=ft.Text(error_msg, color=ft.colors.WHITE),
                    bgcolor=ft.colors.ERROR,
                    action="Aceptar",
                )
            )

    # Lanzamos el hilo en modo daemon para que muera si se cierra la app principal.
    threading.Thread(target=wrapper, daemon=True).start()
