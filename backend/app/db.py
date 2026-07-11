"""Conexión SQLite y creación del esquema.

Usa el módulo estándar `sqlite3` (sin ORM, Principio III). El esquema completo se
crea al arrancar si no existe. Montos siempre como enteros (`*_minor`).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS category (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    kind        TEXT    NOT NULL CHECK (kind IN ('expense','income','both')),
    is_system   INTEGER NOT NULL DEFAULT 0 CHECK (is_system IN (0,1)),
    color       TEXT,
    created_at  TEXT    NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_category_name_ci ON category (name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS "transaction" (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    type            TEXT    NOT NULL CHECK (type IN ('income','expense')),
    amount_minor    INTEGER NOT NULL CHECK (amount_minor > 0),
    currency        TEXT    NOT NULL,
    date            TEXT    NOT NULL,
    description     TEXT,
    category_id     INTEGER REFERENCES category(id) ON DELETE SET NULL,
    category_status TEXT    NOT NULL DEFAULT 'uncategorized'
                    CHECK (category_status IN ('ai_suggested','user_confirmed','uncategorized')),
    ai_confidence   REAL,
    source          TEXT    NOT NULL DEFAULT 'manual' CHECK (source IN ('manual','imported')),
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tx_date ON "transaction" (date);
CREATE INDEX IF NOT EXISTS ix_tx_category ON "transaction" (category_id);
CREATE INDEX IF NOT EXISTS ix_tx_type ON "transaction" (type);

CREATE TABLE IF NOT EXISTS budget (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id  INTEGER NOT NULL REFERENCES category(id) ON DELETE CASCADE,
    year_month   TEXT    NOT NULL,
    limit_minor  INTEGER NOT NULL CHECK (limit_minor > 0),
    currency     TEXT    NOT NULL,
    created_at   TEXT    NOT NULL,
    UNIQUE (category_id, year_month)
);

CREATE TABLE IF NOT EXISTS savings_goal (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    target_minor INTEGER NOT NULL CHECK (target_minor > 0),
    currency     TEXT    NOT NULL,
    target_date  TEXT,
    created_at   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS goal_contribution (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id      INTEGER NOT NULL REFERENCES savings_goal(id) ON DELETE CASCADE,
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
    date         TEXT    NOT NULL,
    note         TEXT,
    created_at   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_contrib_goal ON goal_contribution (goal_id);
"""


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Devuelve una conexión con FKs activas y filas accesibles por nombre."""
    _ensure_parent(config.DB_PATH)
    conn = sqlite3.connect(
        str(config.DB_PATH), check_same_thread=False, isolation_level=None
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection | None = None) -> None:
    """Crea el esquema si no existe."""
    own = conn is None
    conn = conn or get_connection()
    try:
        conn.executescript(_SCHEMA)
    finally:
        if own:
            conn.close()


def get_db() -> Iterator[sqlite3.Connection]:
    """Dependencia FastAPI: una conexión por request."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def is_empty(conn: sqlite3.Connection) -> bool:
    """True si no hay transacciones (BD recién creada / reseteada)."""
    row = conn.execute('SELECT COUNT(*) AS c FROM "transaction"').fetchone()
    return (row["c"] if row else 0) == 0
