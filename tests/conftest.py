"""Fixtures compartidas para todos los tests."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import src.settings as settings


@pytest.fixture(autouse=True)
def tmp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirige todas las rutas de datos a un directorio temporal por test."""
    data = tmp_path / "data"
    data.mkdir()
    facturas = tmp_path / "facturas"
    facturas.mkdir()
    reportes = tmp_path / "reportes"
    reportes.mkdir()

    monkeypatch.setattr(settings, "RUTA_DATOS", data)
    monkeypatch.setattr(settings, "RUTA_FACTURAS", facturas)
    monkeypatch.setattr(settings, "RUTA_REPORTES", reportes)

    # Propaga el cambio a los módulos que importan las rutas al cargar
    import src.factura_counter as fc
    import src.factura_writer as fw
    import src.ventas_store as vs
    import tickets_src.counter as tc
    import tickets_src.excel_writer as ew
    import escritorio.registro as reg

    monkeypatch.setattr(fc, "_ARCHIVO", data / "contador_facturas.json")
    monkeypatch.setattr(vs, "RUTA_DB_VENTAS", data / "ventas.db")
    monkeypatch.setattr(reg, "RUTA_DB_VENTAS", data / "ventas.db")
    monkeypatch.setattr(fw, "RUTA_FACTURAS", facturas)
    monkeypatch.setattr(tc, "_ARCHIVO", data / "contador.json")
    monkeypatch.setattr(ew, "_ARCHIVO", data / "tickets.xlsx")

    yield tmp_path


@pytest.fixture()
def mock_escpos():
    """Evita importar python-escpos (requiere hardware USB)."""
    fake_printer = MagicMock()
    with patch.dict(
        "sys.modules",
        {
            "escpos": MagicMock(),
            "escpos.printer": MagicMock(
                Usb=MagicMock(return_value=fake_printer),
                Win32Raw=MagicMock(return_value=fake_printer),
            ),
        },
    ):
        yield fake_printer


@pytest.fixture()
def mock_smtp():
    """Sustituye smtplib.SMTP por un mock."""
    fake_server = MagicMock()
    fake_server.__enter__ = MagicMock(return_value=fake_server)
    fake_server.__exit__ = MagicMock(return_value=False)
    with patch("smtplib.SMTP", return_value=fake_server) as mock_cls:
        yield mock_cls, fake_server
