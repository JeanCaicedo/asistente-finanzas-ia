"""Endpoints de administración de la demo: reset y reseed (FR-028)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db import get_db
from ..repositories import categories as cat_repo
from ..services import seed as seed_service

router = APIRouter(tags=["admin"])


def _reset(conn: sqlite3.Connection) -> None:
    """Borra todos los datos de usuario; mantiene esquema y categorías del sistema."""
    conn.execute("DELETE FROM goal_contribution")
    conn.execute("DELETE FROM savings_goal")
    conn.execute("DELETE FROM budget")
    conn.execute('DELETE FROM "transaction"')
    conn.execute("DELETE FROM category WHERE is_system = 0")
    # Re-sembrar categorías del sistema por si faltara alguna.
    cat_repo.seed_system_categories(conn)


@router.post("/admin/reset")
def reset(conn: sqlite3.Connection = Depends(get_db)):
    _reset(conn)
    return {"status": "ok"}


@router.post("/admin/reseed")
def reseed(conn: sqlite3.Connection = Depends(get_db)):
    _reset(conn)
    seed_service.generate(conn)
    return {"status": "ok"}
