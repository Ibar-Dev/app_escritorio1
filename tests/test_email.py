"""Tests para escritorio.email_envio — mock smtplib.SMTP."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from escritorio.config_app import ConfigSMTP
from escritorio.email_envio import enviar_email_prueba, enviar_factura_por_email


@pytest.fixture()
def cfg():
    return ConfigSMTP(
        servidor="smtp.gmail.com",
        puerto=587,
        usar_tls=True,
        usuario="test@gmail.com",
        contrasena="app-password",
        remitente="test@gmail.com",
        firma="Zoo Picasso",
    )


@pytest.fixture()
def adjunto_xlsx(tmp_path: Path) -> Path:
    ruta = tmp_path / "factura_2026-001.xlsx"
    ruta.write_bytes(b"PK\x03\x04")  # cabecera mínima ZIP/xlsx
    return ruta


class TestEnviarFacturaPorEmail:
    def test_llama_sendmail(self, cfg, adjunto_xlsx, mock_smtp):
        mock_cls, servidor = mock_smtp
        enviar_factura_por_email(cfg, "cliente@example.com", adjunto_xlsx, "2026-001", "Test Cliente")
        assert servidor.sendmail.called or servidor.send_message.called

    def test_error_sin_destinatario(self, cfg, adjunto_xlsx):
        with pytest.raises(ValueError, match="email"):
            enviar_factura_por_email(cfg, "  ", adjunto_xlsx, "2026-001")

    def test_error_adjunto_inexistente(self, cfg, tmp_path):
        with pytest.raises(FileNotFoundError):
            enviar_factura_por_email(cfg, "a@b.com", tmp_path / "noexiste.xlsx", "001")

    def test_usa_tls(self, cfg, adjunto_xlsx, mock_smtp):
        mock_cls, servidor = mock_smtp
        enviar_factura_por_email(cfg, "c@e.com", adjunto_xlsx, "001")
        servidor.starttls.assert_called()


class TestEnviarEmailPrueba:
    def test_envia_sin_error(self, cfg, mock_smtp):
        mock_cls, servidor = mock_smtp
        enviar_email_prueba(cfg, cfg.usuario)
        assert servidor.login.called


def test_cargar_config_smtp_casts_int_y_bool(monkeypatch, tmp_path):
    import escritorio.config_app as config_app

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "smtp_config.json"
    config_file.write_text(
        '{"servidor": "smtp.gmail.com", "puerto": "465", "usar_tls": "false", "usuario": "user@example.com", "remitente": "from@example.com"}',
        encoding="utf-8",
    )

    monkeypatch.setattr(config_app, "RUTA_SMTP_CONFIG", config_file)
    monkeypatch.setattr(config_app.keyring, "get_password", lambda *args, **kwargs: "secret")

    cfg = config_app.cargar_config_smtp()

    assert cfg.puerto == 465
    assert cfg.usar_tls is False
    assert cfg.usuario == "user@example.com"
    assert cfg.contrasena == "secret"
