"""Fixtures compartidas: conexión SQLite en memoria con el esquema creado."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

# Asegura que `app` sea importable al ejecutar pytest desde backend/ o raíz.
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.db import _SCHEMA  # noqa: E402
from app.repositories import categories as cat_repo  # noqa: E402


@pytest.fixture()
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(_SCHEMA)
    yield c
    c.close()


@pytest.fixture()
def seeded_conn(conn) -> sqlite3.Connection:
    cat_repo.seed_system_categories(conn)
    return conn
