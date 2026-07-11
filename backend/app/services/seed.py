"""Generación de datos de ejemplo deterministas (~3 meses).

Usa una semilla fija y fechas ancladas al mes actual para que la demo sea
reproducible y "este mes" siempre tenga contenido (D8 / FR-027).
"""
from __future__ import annotations

import random
import sqlite3
from datetime import date

from .. import config
from ..clock import today_iso
from ..repositories import categories as cat_repo
from ..repositories import goals as goals_repo
from ..repositories import transactions as tx_repo

_SEED = 20260710
_CUR = config.DEFAULT_CURRENCY

# Descripciones de ejemplo por categoría de gasto (con keywords reconocibles).
_EXPENSE_TEMPLATES = [
    ("Comida", "Mercado supermercado", (8000000, 18000000)),
    ("Comida", "Almuerzo restaurante", (2500000, 6000000)),
    ("Transporte", "Uber al trabajo", (1200000, 3500000)),
    ("Transporte", "Gasolina", (12000000, 20000000)),
    ("Servicios", "Internet hogar", (9000000, 9000000)),
    ("Servicios", "Recibo de luz", (6000000, 12000000)),
    ("Ocio", "Cine con amigos", (3000000, 5000000)),
    ("Salud", "Farmacia", (2000000, 8000000)),
    ("Compras", "Ropa tienda", (5000000, 15000000)),
    ("Vivienda", "Arriendo apartamento", (120000000, 120000000)),
]


def _first_of_month(anchor: date, months_back: int) -> date:
    index = anchor.year * 12 + (anchor.month - 1) - months_back
    y, m = divmod(index, 12)
    return date(y, m + 1, 1)


def _cat_id(conn: sqlite3.Connection, name: str) -> int | None:
    c = cat_repo.get_by_name(conn, name)
    return c["id"] if c else None


def generate(conn: sqlite3.Connection) -> None:
    """Siembra ~3 meses de transacciones + presupuestos + una meta con aportes."""
    cat_repo.seed_system_categories(conn)
    rng = random.Random(_SEED)
    anchor = date.fromisoformat(today_iso())

    salario_id = _cat_id(conn, "Salario")
    day_cap = {0: anchor.day}  # limita el mes actual a "hoy"

    for months_back in range(2, -1, -1):  # 2 meses atrás → mes actual
        month_start = _first_of_month(anchor, months_back)
        max_day = anchor.day if months_back == 0 else 28

        # Ingreso recurrente: salario el día 1.
        tx_repo.create(
            conn,
            type="income",
            amount_minor=350000000,
            currency=_CUR,
            date=month_start.replace(day=1).isoformat(),
            description="Pago nomina salario",
            category_id=salario_id,
            category_status="user_confirmed" if salario_id else "uncategorized",
            ai_confidence=None,
            source="manual",
        )

        # Gastos variados.
        for name, desc, (lo, hi) in _EXPENSE_TEMPLATES:
            # 1-2 ocurrencias por plantilla y mes.
            for _ in range(rng.randint(1, 2)):
                day = min(rng.randint(2, 28), max_day)
                if day < 1:
                    day = 1
                amount = rng.randint(lo, hi)
                cid = _cat_id(conn, name)
                tx_repo.create(
                    conn,
                    type="expense",
                    amount_minor=amount,
                    currency=_CUR,
                    date=month_start.replace(day=day).isoformat(),
                    description=desc,
                    category_id=cid,
                    category_status="user_confirmed" if cid else "uncategorized",
                    ai_confidence=None,
                    source="manual",
                )

    # Presupuestos del mes actual para un par de categorías.
    from ..repositories import budgets as bud_repo

    ym = anchor.strftime("%Y-%m")
    for name, limit in (("Comida", 40000000), ("Transporte", 25000000)):
        cid = _cat_id(conn, name)
        if cid is not None:
            try:
                bud_repo.create(
                    conn,
                    category_id=cid,
                    year_month=ym,
                    limit_minor=limit,
                    currency=_CUR,
                )
            except sqlite3.IntegrityError:
                pass

    # Una meta de ahorro con dos aportes manuales.
    goal = goals_repo.create(
        conn,
        name="Fondo de emergencia",
        target_minor=200000000,
        currency=_CUR,
        target_date=f"{anchor.year}-12-31",
    )
    goals_repo.add_contribution(
        conn,
        goal_id=goal["id"],
        amount_minor=50000000,
        date=_first_of_month(anchor, 1).isoformat(),
        note="Aporte mensual",
    )
    goals_repo.add_contribution(
        conn,
        goal_id=goal["id"],
        amount_minor=30000000,
        date=_first_of_month(anchor, 0).isoformat(),
        note="Aporte mensual",
    )
