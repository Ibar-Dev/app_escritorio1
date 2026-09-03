# zoo_picasso.spec — PyInstaller spec para Zoo Picasso (Windows)
# Uso: uv run pyinstaller zoo_picasso.spec --clean
# Requiere: pyinstaller>=6.0 (en dependency-groups.dev)
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_data_files

# Recopilar activos de flet (assets web, binarios del runtime de escritorio)
flet_datas, flet_binaries, flet_hiddenimports = collect_all("flet")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=flet_binaries,
    datas=[
        # Directorio de configuración SMTP (el archivo se genera en primera ejecución)
        ("config", "config"),
        # Catálogo de capacidades de impresoras ESC/POS (no es código, PyInstaller lo omite por defecto)
        (".venv/Lib/site-packages/escpos/capabilities.json", "escpos"),
    ] + flet_datas,
    hiddenimports=flet_hiddenimports + [
        # Backend de keyring para Windows Credential Manager
        "keyring.backends.Windows",
        "keyring.backends._win_crypto",
        # Módulos pywin32 (ver también hooks/hook-win32com.py)
        "win32api",
        "win32com",
        "win32com.client",
        "win32con",
        "win32print",
        "pywintypes",
        "pythoncom",
        # Impresora ESC/POS
        "escpos.printer",
        "libusb_package",
    ],
    # Reutiliza el hook de pywin32 ya existente en el proyecto
    hookspath=["hooks"],
    runtime_hooks=[],
    # Excluir dependencias de desarrollo que no deben llegar al bundle
    excludes=["pytest", "pytest_mock", "_pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ZooPicasso",
    debug=False,
    strip=False,
    upx=True,
    console=False,  # sin ventana de consola negra
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ZooPicasso",
)
