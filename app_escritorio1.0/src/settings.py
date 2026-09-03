"""Rutas de runtime y logging centralizado.

Este módulo se importa primero (antes de cualquier otro de la app) para
garantizar que BASE_DIR y las rutas derivadas estén resueltas tanto en
desarrollo como dentro del bundle PyInstaller (_MEIPASS).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from platformdirs import user_data_dir


def _base() -> Path:
    # En el bundle PyInstaller todos los archivos están bajo _MEIPASS
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    # En desarrollo: directorio de este archivo es src/, su padre es app_escritorio/
    return Path(__file__).resolve().parent.parent


def _user_data() -> Path:
    # Siempre escribible: %LOCALAPPDATA%\ZooPicasso\ZooPicasso en Windows
    return Path(user_data_dir("ZooPicasso", "ZooPicasso"))


BUNDLE_DIR: Path = _base()   # solo lectura: assets del bundle
RUTA_DATOS: Path = _user_data() / "data"
RUTA_FACTURAS: Path = _user_data() / "facturas"
RUTA_REPORTES: Path = _user_data() / "reportes"
RUTA_CONFIG: Path = _user_data() / "config"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
