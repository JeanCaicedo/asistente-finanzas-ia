"""Acceso a datos de categorías + sembrado de categorías del sistema."""
from __future__ import annotations

import sqlite3

from ..clock import utcnow_iso

# Categorías del sistema (is_system=1). No borrables ni renombrables.
SYSTEM_CATEGORIES: list[tuple[str, str]] = [
    ("Comida", "expense"),
    ("Transporte", "expense"),
    ("Vivienda", "expense"),
    ("Servicios", "expense"),
    ("Ocio", "expense"),
    ("Salud", "expense"),
    ("Compras", "expense"),
    ("Salario", "income"),
    ("Otros ingresos", "income"),
]


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "kind": row["kind"],
        "is_system": bool(row["is_system"]),
        "color": row["color"],
    }


def seed_system_categories(conn: sqlite3.Connection) -> None:
    """Inserta las categorías del sistema si aún no existen (idempotente)."""
    now = utcnow_iso()
    for name, kind in SYSTEM_CATEGORIES:
        exists = conn.execute(
            "SELECT 1 FROM category WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO category (name, kind, is_system, color, created_at) "
                "VALUES (?, ?, 1, NULL, ?)",
                (name, kind, now),
            )


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM category ORDER BY is_system DESC, name COLLATE NOCASE"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get(conn: sqlite3.Connection, category_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM category WHERE id = ?", (category_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def get_by_name(conn: sqlite3.Connection, name: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM category WHERE name = ? COLLATE NOCASE", (name,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def create(conn: sqlite3.Connection, name: str, kind: str, color: str | None) -> dict:
    """Crea una categoría del usuario (is_system=0). Lanza IntegrityError si duplica."""
    cur = conn.execute(
        "INSERT INTO category (name, kind, is_system, color, created_at) "
        "VALUES (?, ?, 0, ?, ?)",
        (name.strip(), kind, color, utcnow_iso()),
    )
    created = get(conn, cur.lastrowid)
    assert created is not None
    return created


def delete(conn: sqlite3.Connection, category_id: int) -> str:
    """Borra una categoría propia.

    Devuelve: 'deleted', 'not_found' o 'is_system'. Las transacciones que la
    referencian pasan a NULL (ON DELETE SET NULL) y sus presupuestos se borran
    (ON DELETE CASCADE).
    """
    row = conn.execute(
        "SELECT is_system FROM category WHERE id = ?", (category_id,)
    ).fetchone()
    if row is None:
        return "not_found"
    if row["is_system"]:
        return "is_system"
    # Marca explícita: transacciones afectadas vuelven a 'uncategorized'.
    conn.execute(
        "UPDATE \"transaction\" SET category_status = 'uncategorized', "
        "ai_confidence = NULL WHERE category_id = ?",
        (category_id,),
    )
    conn.execute("DELETE FROM category WHERE id = ?", (category_id,))
    return "deleted"
