"""Acceso a datos de transacciones."""
from __future__ import annotations

import sqlite3
from typing import Optional

from ..clock import utcnow_iso


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "type": row["type"],
        "amount_minor": row["amount_minor"],
        "currency": row["currency"],
        "date": row["date"],
        "description": row["description"],
        "category_id": row["category_id"],
        "category_status": row["category_status"],
        "ai_confidence": row["ai_confidence"],
        "source": row["source"],
    }


def create(
    conn: sqlite3.Connection,
    *,
    type: str,
    amount_minor: int,
    currency: str,
    date: str,
    description: Optional[str],
    category_id: Optional[int],
    category_status: str,
    ai_confidence: Optional[float],
    source: str = "manual",
) -> dict:
    now = utcnow_iso()
    cur = conn.execute(
        'INSERT INTO "transaction" '
        "(type, amount_minor, currency, date, description, category_id, "
        " category_status, ai_confidence, source, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            type,
            amount_minor,
            currency,
            date,
            description,
            category_id,
            category_status,
            ai_confidence,
            source,
            now,
            now,
        ),
    )
    created = get(conn, cur.lastrowid)
    assert created is not None
    return created


def get(conn: sqlite3.Connection, tx_id: int) -> dict | None:
    row = conn.execute(
        'SELECT * FROM "transaction" WHERE id = ?', (tx_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def list_(
    conn: sqlite3.Connection,
    *,
    year_month: Optional[str] = None,
    category_id: Optional[int] = None,
    type: Optional[str] = None,
) -> list[dict]:
    clauses: list[str] = []
    params: list = []
    if year_month:
        clauses.append("date LIKE ?")
        params.append(f"{year_month}-%")
    if category_id is not None:
        clauses.append("category_id = ?")
        params.append(category_id)
    if type:
        clauses.append("type = ?")
        params.append(type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f'SELECT * FROM "transaction" {where} ORDER BY date DESC, id DESC', params
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update(conn: sqlite3.Connection, tx_id: int, fields: dict) -> dict | None:
    """Actualiza campos parciales. Si viene `category_id`, el llamador ajusta
    `category_status` (normalmente user_confirmed)."""
    if get(conn, tx_id) is None:
        return None
    allowed = {
        "type",
        "amount_minor",
        "date",
        "description",
        "category_id",
        "category_status",
        "ai_confidence",
    }
    sets = []
    params: list = []
    for key, value in fields.items():
        if key in allowed:
            sets.append(f"{key} = ?")
            params.append(value)
    if not sets:
        return get(conn, tx_id)
    sets.append("updated_at = ?")
    params.append(utcnow_iso())
    params.append(tx_id)
    conn.execute(
        f'UPDATE "transaction" SET {", ".join(sets)} WHERE id = ?', params
    )
    return get(conn, tx_id)


def delete(conn: sqlite3.Connection, tx_id: int) -> bool:
    if get(conn, tx_id) is None:
        return False
    conn.execute('DELETE FROM "transaction" WHERE id = ?', (tx_id,))
    return True


def find_exact_duplicate(
    conn: sqlite3.Connection, *, date: str, amount_minor: int, description: Optional[str]
) -> Optional[int]:
    """Duplicado exacto = fecha + monto + descripción (Clarificación Q4)."""
    row = conn.execute(
        'SELECT id FROM "transaction" '
        "WHERE date = ? AND amount_minor = ? AND IFNULL(description,'') = IFNULL(?, '')",
        (date, amount_minor, description),
    ).fetchone()
    return row["id"] if row else None
