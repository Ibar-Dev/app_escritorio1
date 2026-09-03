import json
import logging
from dataclasses import asdict, dataclass, fields

import keyring

import src.settings as _s

logger = logging.getLogger(__name__)

RUTA_SMTP_CONFIG = _s.RUTA_CONFIG / "smtp_config.json"

_KEYRING_SERVICE = "zoo-picasso-smtp"
_KEYRING_ACCOUNT = "smtp_password"


@dataclass
class ConfigSMTP:
    servidor: str = "smtp.gmail.com"
    puerto: int = 587
    usar_tls: bool = True
    usuario: str = ""
    contrasena: str = ""
    remitente: str = ""
    asunto: str = "Tu factura {numero} de Zoo Picasso"
    cuerpo: str = (
        "Hola {cliente},\n\n"
        "Te adjuntamos la factura {numero} de Zoo Picasso.\n"
        "Gracias por tu confianza.\n\n{firma}"
    )
    firma: str = "Gisselle Marin Tabares"
    copia_para_mi: bool = False


def cargar_config_smtp() -> ConfigSMTP:
    datos: dict = {}
    if RUTA_SMTP_CONFIG.exists():
        try:
            datos = json.loads(RUTA_SMTP_CONFIG.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    valores: dict = {}
    for campo in fields(ConfigSMTP):
        nombre = campo.name
        if nombre == "contrasena":
            continue
        if nombre in datos:
            valor = datos[nombre]
            tipo = campo.type
            if tipo is int:
                try:
                    valor = int(valor)
                except (TypeError, ValueError):
                    valor = campo.default
            elif tipo is bool:
                if isinstance(valor, str):
                    valor = valor.strip().lower() in {"1", "true", "yes", "on"}
                else:
                    valor = bool(valor)
            valores[nombre] = valor
    cfg = ConfigSMTP(**valores)
    # One-time migration: move plaintext password from JSON to OS keyring
    if datos.get("contrasena"):
        try:
            keyring.set_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT, datos["contrasena"])
            datos.pop("contrasena")
            RUTA_SMTP_CONFIG.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info("Contraseña SMTP migrada al llavero del sistema.")
        except Exception:
            logger.warning("No se pudo migrar la contraseña al llavero del sistema.")
    try:
        cfg.contrasena = keyring.get_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT) or ""
    except Exception:
        logger.warning("No se pudo acceder al llavero del sistema para recuperar la contraseña SMTP.")
    return cfg


def guardar_config_smtp(cfg: ConfigSMTP) -> None:
    _s.RUTA_CONFIG.mkdir(parents=True, exist_ok=True)
    # Password goes to OS keyring, never to disk
    try:
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT, cfg.contrasena)
    except Exception:
        logger.warning("No se pudo guardar la contraseña en el llavero del sistema.")
    datos = asdict(cfg)
    datos.pop("contrasena", None)
    RUTA_SMTP_CONFIG.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def config_smtp_completa(cfg: ConfigSMTP) -> tuple[bool, str]:
    if not cfg.servidor:
        return False, "Falta el servidor SMTP."
    if not cfg.usuario:
        return False, "Falta el usuario de la cuenta de correo."
    if not cfg.contrasena:
        return False, "Falta la contraseña de la cuenta de correo."
    return True, ""