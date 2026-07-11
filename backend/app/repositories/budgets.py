"""Acceso a datos de presupuestos. Único por (category_id, year_month)."""
from __future__ import annotations

import sqlite3

from ..clock import utcnow_iso


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "category_id": row["category_id"],
        "year_month": row["year_month"],
        "limit_minor": row["limit_minor"],
        "currency": row["currency"],
    }


def create(
    conn: sqlite3.Connection,
    *,
    category_id: int,
    year_month: str,
    limit_minor: int,
    currency: str,
) -> dict:
    """Crea un presupuesto. Lanza IntegrityError si (category_id, year_month) ya existe."""
    cur = conn.execute(
        "INSERT INTO budget (category_id, year_month, limit_minor, currency, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (category_id, year_month, limit_minor, currency, utcnow_iso()),
    )
    return get(conn, cur.lastrowid)  # type: ignore[return-value]


def get(conn: sqlite3.Connection, budget_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM budget WHERE id = ?", (budget_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_for_month(conn: sqlite3.Connection, year_month: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM budget WHERE year_month = ? ORDER BY id", (year_month,)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def delete(conn: sqlite3.Connection, budget_id: int) -> bool:
    if get(conn, budget_id) is None:
        return False
    conn.execute("DELETE FROM budget WHERE id = ?", (budget_id,))
    return True
