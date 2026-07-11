"""Reportes del dashboard con trazabilidad (Principio IV).

Garantiza que la suma de los items por categoría == total de gastos del periodo
(FR-013 / SC-002), porque ambos se derivan del MISMO conjunto de transacciones.
"""
from __future__ import annotations

import sqlite3

from .. import config
from . import finance

_UNCATEGORIZED_LABEL = "Sin categorizar"


def by_category(conn: sqlite3.Connection, year_month: str) -> dict:
    """Gasto por categoría de un mes, con `transaction_ids` por item.

    La suma de `amount_minor` de los items es idéntica a `total_minor`.
    """
    rows = conn.execute(
        "SELECT t.id AS tx_id, t.amount_minor AS amount, t.category_id AS cat_id, "
        "       c.name AS cat_name "
        'FROM "transaction" t '
        "LEFT JOIN category c ON c.id = t.category_id "
        "WHERE t.type = 'expense' AND t.date LIKE ? "
        "ORDER BY t.category_id IS NULL, c.name COLLATE NOCASE, t.id",
        (f"{year_month}-%",),
    ).fetchall()

    buckets: dict = {}
    total = 0
    for row in rows:
        cat_id = row["cat_id"]
        # category_id NULL o categoría inexistente → "Sin categorizar".
        name = row["cat_name"] if row["cat_name"] else _UNCATEGORIZED_LABEL
        key = cat_id if row["cat_name"] else None
        bucket = buckets.setdefault(
            key,
            {
                "category_id": key,
                "category_name": name,
                "amount_minor": 0,
                "transaction_ids": [],
            },
        )
        bucket["amount_minor"] += int(row["amount"])
        bucket["transaction_ids"].append(int(row["tx_id"]))
        total += int(row["amount"])

    items = sorted(
        buckets.values(), key=lambda b: (-b["amount_minor"], b["category_name"])
    )
    return {
        "year_month": year_month,
        "currency": config.DEFAULT_CURRENCY,
        "total_minor": total,
        "items": items,
    }


def _add_months(year_month: str, delta: int) -> str:
    year, month = int(year_month[:4]), int(year_month[5:7])
    index = (year * 12 + (month - 1)) + delta
    y, m = divmod(index, 12)
    return f"{y:04d}-{m + 1:02d}"


def monthly_series(conn: sqlite3.Connection, months: int, anchor_year_month: str) -> list[dict]:
    """Serie de los últimos `months` meses (terminando en anchor), con ingresos,
    gastos, neto y la variación de neto respecto al mes previo (tendencia)."""
    result: list[dict] = []
    for i in range(months - 1, -1, -1):
        ym = _add_months(anchor_year_month, -i)
        totals = finance.monthly_totals(conn, ym)
        result.append(
            {
                "year_month": ym,
                "income_minor": totals["income_minor"],
                "expense_minor": totals["expense_minor"],
                "net_minor": totals["net_minor"],
                "currency": config.DEFAULT_CURRENCY,
            }
        )
    return result
