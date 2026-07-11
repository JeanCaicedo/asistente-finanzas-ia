"""Acceso a datos de metas de ahorro y aportes (contribuciones)."""
from __future__ import annotations

import sqlite3
from typing import Optional

from ..clock import utcnow_iso


def _goal_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "target_minor": row["target_minor"],
        "currency": row["currency"],
        "target_date": row["target_date"],
    }


def create(
    conn: sqlite3.Connection,
    *,
    name: str,
    target_minor: int,
    currency: str,
    target_date: Optional[str],
) -> dict:
    cur = conn.execute(
        "INSERT INTO savings_goal (name, target_minor, currency, target_date, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (name.strip(), target_minor, currency, target_date, utcnow_iso()),
    )
    return get(conn, cur.lastrowid)  # type: ignore[return-value]


def get(conn: sqlite3.Connection, goal_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM savings_goal WHERE id = ?", (goal_id,)
    ).fetchone()
    return _goal_row(row) if row else None


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM savings_goal ORDER BY id").fetchall()
    return [_goal_row(r) for r in rows]


def saved_minor(conn: sqlite3.Connection, goal_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(amount_minor), 0) AS s FROM goal_contribution WHERE goal_id = ?",
        (goal_id,),
    ).fetchone()
    return int(row["s"] if row else 0)


def add_contribution(
    conn: sqlite3.Connection,
    *,
    goal_id: int,
    amount_minor: int,
    date: str,
    note: Optional[str],
) -> int:
    cur = conn.execute(
        "INSERT INTO goal_contribution (goal_id, amount_minor, date, note, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (goal_id, amount_minor, date, note, utcnow_iso()),
    )
    return int(cur.lastrowid)
