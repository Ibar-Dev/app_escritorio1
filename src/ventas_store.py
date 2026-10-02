"""Operaciones SQLite para el control de ventas (ventas.db)."""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Any

import src.settings as _s
from src.factura_model import Factura, PagoInfo
from src.money import cents, from_cents

logger = logging.getLogger(__name__)

RUTA_DB_VENTAS = _s.RUTA_DATOS / "ventas.db"

_DDL = """
CREATE TABLE IF NOT EXISTS ventas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_factura  TEXT    NOT NULL,
    fecha_venta     TEXT    NOT NULL,
    anio_mes        TEXT    NOT NULL,
    categoria       TEXT    NOT NULL DEFAULT '',
    monto           INTEGER NOT NULL DEFAULT 0,
    cliente_nombre  TEXT    DEFAULT '',
    usuario         TEXT    DEFAULT '',
    created_at      TEXT    NOT NULL,
    metodo_pago     TEXT    DEFAULT '',
    estado          TEXT    NOT NULL DEFAULT 'activa'
);
CREATE TABLE IF NOT EXISTS ajustes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    anio_mes    TEXT    NOT NULL,
    concepto    TEXT    NOT NULL,
    monto       INTEGER NOT NULL DEFAULT 0,
    usuario     TEXT    DEFAULT '',
    created_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ventas_anio_mes ON ventas(anio_mes);
CREATE INDEX IF NOT EXISTS idx_ventas_fecha    ON ventas(fecha_venta);
"""


@contextmanager
def _connect():
    RUTA_DB_VENTAS.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(RUTA_DB_VENTAS)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def inicializar_db_ventas() -> None:
    """Crea las tablas si no existen (idempotente)."""
    with _connect() as conn:
        conn.executescript(_DDL)


def registrar_ventas_factura(
    factura: Factura,
    usuario: str,
    pago: PagoInfo,
) -> None:
    """Inserta una fila por línea de la factura en ventas."""
    inicializar_db_ventas()
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    fecha = factura.fecha.isoformat()
    anio_mes = factura.fecha.strftime("%Y-%m")
    metodo_pago = (pago.metodo_pago or "efectivo").strip().lower()
    registros = [
        (
            factura.numero_formateado,
            fecha,
            anio_mes,
            (linea.categoria or "sin_categoria").strip() or "sin_categoria",
            cents(linea.total),
            (factura.cliente_nombre or "").strip(),
            (usuario or "").strip(),
            created_at,
            metodo_pago,
        )
        for linea in factura.lineas
    ]
    if not registros:
        return
    with _connect() as conn:
        conn.executemany(
            """INSERT INTO ventas
               (numero_factura, fecha_venta, anio_mes, categoria, monto,
                cliente_nombre, usuario, created_at, metodo_pago)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            registros,
        )
    logger.info("Factura %s registrada (%d líneas)", factura.numero_formateado, len(registros))


def historial_ventas(
    desde: str,
    hasta: str,
    categoria: str | None = None,
    metodo_pago: str | None = None,
) -> list[dict[str, Any]]:
    """Retorna ventas agrupadas por número de factura/ticket."""
    inicializar_db_ventas()
    sql = """
        SELECT
            numero_factura,
            fecha_venta,
            MAX(cliente_nombre)             AS cliente_nombre,
            GROUP_CONCAT(DISTINCT categoria) AS categorias,
            SUM(monto)                      AS monto_lineas,
            MAX(metodo_pago)                AS metodo_pago,
            MAX(estado)                     AS estado
        FROM ventas
        WHERE fecha_venta BETWEEN ? AND ?
          AND estado = 'activa'
          AND (? IS NULL OR categoria = ?)
          AND (? IS NULL OR metodo_pago = ?)
        GROUP BY numero_factura, fecha_venta
        ORDER BY fecha_venta DESC, numero_factura DESC
    """
    with _connect() as conn:
        cur = conn.execute(sql, (desde, hasta, categoria, categoria, metodo_pago, metodo_pago))
        return _filas_a_decimal([dict(row) for row in cur.fetchall()])


def resumen_ventas_rango(
    desde: str,
    hasta: str,
    categoria: str | None = None,
    metodo_pago: str | None = None,
) -> dict[str, Any]:
    """Resumen de ventas activas para un rango y filtros opcionales."""
    inicializar_db_ventas()
    with _connect() as conn:
        row = conn.execute(
            """SELECT
                   COALESCE(SUM(monto), 0) AS total,
                   COUNT(DISTINCT numero_factura) AS cantidad_ventas,
                   COALESCE(SUM(CASE WHEN metodo_pago IN ('efectivo','mixto') THEN monto ELSE 0 END), 0) AS total_efectivo,
                   COALESCE(SUM(CASE WHEN metodo_pago IN ('tarjeta','mixto')  THEN monto ELSE 0 END), 0) AS total_tarjeta
               FROM ventas
               WHERE fecha_venta BETWEEN ? AND ?
                 AND estado = 'activa'
                 AND (? IS NULL OR categoria = ?)
                 AND (? IS NULL OR metodo_pago = ?)""",
            (desde, hasta, categoria, categoria, metodo_pago, metodo_pago),
        ).fetchone()

        cat_rows = conn.execute(
            """SELECT categoria, SUM(monto) AS total
               FROM ventas
               WHERE fecha_venta BETWEEN ? AND ?
                 AND estado = 'activa'
                 AND (? IS NULL OR categoria = ?)
                 AND (? IS NULL OR metodo_pago = ?)
               GROUP BY categoria""",
            (desde, hasta, categoria, categoria, metodo_pago, metodo_pago),
        ).fetchall()

    total = from_cents(row["total"])
    return {
        "total": total,
        "cantidad_ventas": int(row["cantidad_ventas"]),
        "total_efectivo": from_cents(row["total_efectivo"]),
        "total_tarjeta": from_cents(row["total_tarjeta"]),
        "por_categoria": {r["categoria"]: from_cents(r["total"]) for r in cat_rows},
    }


def _filas_a_decimal(filas: list[dict]) -> list[dict]:
    """Convierte el campo monto_lineas de céntimos a Decimal en resultados de historial."""
    for f in filas:
        if "monto_lineas" in f:
            f["monto_lineas"] = from_cents(f["monto_lineas"])
    return filas


def resumen_ventas_activas(anio_mes: str) -> dict[str, Any]:
    """Resumen del mes: totales, desglose por categoría y ajustes."""
    inicializar_db_ventas()
    with _connect() as conn:
        row = conn.execute(
            """SELECT
                   COALESCE(SUM(monto), 0)                                            AS total_bruto,
                   COUNT(DISTINCT numero_factura)                                        AS cantidad_ventas,
                   COALESCE(SUM(CASE WHEN metodo_pago IN ('efectivo','mixto') THEN monto ELSE 0 END), 0) AS total_efectivo,
                   COALESCE(SUM(CASE WHEN metodo_pago IN ('tarjeta','mixto')  THEN monto ELSE 0 END), 0) AS total_tarjeta
               FROM ventas WHERE anio_mes = ? AND estado = 'activa'""",
            (anio_mes,),
        ).fetchone()

        cat_rows = conn.execute(
            "SELECT categoria, SUM(monto) AS total FROM ventas "
            "WHERE anio_mes = ? AND estado = 'activa' GROUP BY categoria",
            (anio_mes,),
        ).fetchall()

        ajuste_row = conn.execute(
            "SELECT COALESCE(SUM(monto), 0) AS ajuste_total FROM ajustes WHERE anio_mes = ?",
            (anio_mes,),
        ).fetchone()

    total_bruto = from_cents(row["total_bruto"])
    ajuste_total = from_cents(ajuste_row["ajuste_total"])
    return {
        "total": total_bruto + ajuste_total,
        "total_bruto": total_bruto,
        "ajuste_total": ajuste_total,
        "cantidad_ventas": int(row["cantidad_ventas"]),
        "total_efectivo": from_cents(row["total_efectivo"]),
        "total_tarjeta": from_cents(row["total_tarjeta"]),
        "por_categoria": {r["categoria"]: from_cents(r["total"]) for r in cat_rows},
    }


def resumen_ventas_dia(fecha: str) -> dict[str, Any]:
    """Totales de ventas activas para un día dado (YYYY-MM-DD)."""
    inicializar_db_ventas()
    with _connect() as conn:
        row = conn.execute(
            """SELECT
                   COALESCE(SUM(monto), 0)       AS total,
                   COUNT(DISTINCT numero_factura)   AS cantidad_ventas
               FROM ventas WHERE fecha_venta = ? AND estado = 'activa'""",
            (fecha,),
        ).fetchone()
    return {"total": from_cents(row["total"]), "cantidad_ventas": int(row["cantidad_ventas"])}


def ventas_activas_detalle(anio_mes: str) -> list[dict[str, Any]]:
    """Filas individuales del mes para la hoja Detalle del reporte Excel."""
    inicializar_db_ventas()
    with _connect() as conn:
        cur = conn.execute(
            """SELECT numero_factura, fecha_venta, categoria, monto,
                      cliente_nombre, usuario, metodo_pago
               FROM ventas WHERE anio_mes = ? AND estado = 'activa'
               ORDER BY fecha_venta, numero_factura""",
            (anio_mes,),
        )
        return [{**dict(row), "monto": from_cents(row["monto"])} for row in cur.fetchall()]


def listar_ajustes_activos(anio_mes: str) -> list[dict[str, Any]]:
    """Ajustes manuales del mes para incluirlos en el reporte."""
    inicializar_db_ventas()
    with _connect() as conn:
        cur = conn.execute(
            "SELECT concepto, monto, usuario, created_at FROM ajustes "
            "WHERE anio_mes = ? ORDER BY created_at",
            (anio_mes,),
        )
        return [{**dict(row), "monto": from_cents(row["monto"])} for row in cur.fetchall()]
