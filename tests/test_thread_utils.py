"""Tests para utilidades de hilos UI seguras."""
from __future__ import annotations

import threading
import time

import flet as ft

from ui.thread_utils import drenar_tareas_ui_pendientes, ejecutar_en_hilo_seguro


def test_error_en_hilo_muestra_snackbar_via_call_from_thread():
    class PageFake:
        def __init__(self):
            self.abiertos = []
            self.actualizaciones = 0

        def open(self, control):
            self.abiertos.append(control)

        def update(self):
            self.actualizaciones += 1

        def call_from_thread(self, fn):
            fn()

    page = PageFake()
    done = threading.Event()

    def _falla():
        try:
            raise RuntimeError("fallo intencional")
        finally:
            done.set()

    ejecutar_en_hilo_seguro(page, _falla)
    assert done.wait(timeout=1.0)

    for _ in range(20):
        if page.abiertos:
            break
        time.sleep(0.01)

    assert len(page.abiertos) == 1
    snackbar = page.abiertos[0]
    assert isinstance(snackbar, ft.SnackBar)
    assert "Error en la operación" in snackbar.content.value
    assert snackbar.content.color == ft.Colors.WHITE
    color_error = getattr(ft.Colors, "ERROR", None) or getattr(ft.Colors, "RED_700", None) or ft.Colors.RED
    assert snackbar.bgcolor == color_error
    assert page.actualizaciones >= 1


def test_error_en_hilo_se_encola_si_no_hay_call_from_thread():
    class PageFake:
        def __init__(self):
            self.abiertos = []
            self.actualizaciones = 0

        def open(self, control):
            self.abiertos.append(control)

        def update(self):
            self.actualizaciones += 1

    page = PageFake()
    done = threading.Event()

    def _falla():
        try:
            raise ValueError("boom")
        finally:
            done.set()

    ejecutar_en_hilo_seguro(page, _falla)
    assert done.wait(timeout=1.0)

    assert len(page.abiertos) == 0
    procesadas = 0
    for _ in range(20):
        procesadas += drenar_tareas_ui_pendientes()
        if page.abiertos:
            break
        time.sleep(0.01)
    assert procesadas >= 1
    assert len(page.abiertos) == 1
    assert page.actualizaciones >= 1
