from __future__ import annotations

import shutil
import sys
from pathlib import Path


def ensure_project_paths() -> list[str]:
    """Ensures app_escritorio/ is on sys.path (dev and packaged)."""
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller bundle: _MEIPASS already on sys.path
        candidates = [Path(sys._MEIPASS)]
    else:
        candidates = [Path(__file__).resolve().parent]

    added: list[str] = []
    for candidate in candidates:
        s = str(candidate)
        if s not in sys.path:
            sys.path.insert(0, s)
            added.append(s)
    return added


def ensure_data_dirs() -> None:
    """Creates user data directories and seeds smtp_config.json on first run."""
    import src.settings as _s  # imported after sys.path is set

    for ruta in (_s.RUTA_DATOS, _s.RUTA_FACTURAS, _s.RUTA_REPORTES, _s.RUTA_CONFIG):
        ruta.mkdir(parents=True, exist_ok=True)

    smtp_destino = _s.RUTA_CONFIG / "smtp_config.json"
    if not smtp_destino.exists():
        smtp_template = _s.BUNDLE_DIR / "config" / "smtp_config.json"
        if smtp_template.exists():
            shutil.copy2(smtp_template, smtp_destino)
        else:
            smtp_destino.write_text("{}", encoding="utf-8")
