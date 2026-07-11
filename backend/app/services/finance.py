"""CÁLCULOS financieros deterministas (Principio I).

Toda la aritmética de dinero ocurre aquí con enteros. Los helpers puros (net,
budget_status, goal_status) no tocan la BD y son directamente testeables. Las
funciones de agregación reciben una conexión y solo SUMAN enteros.
"""
from __future__ import annotations

import sqlite3
from datetime import date as _date
from typing import Optional

from ..money import MoneyError

# Umbral de cercanía de presupuesto (80% por defecto — data-model / FR-010).
NEAR_THRESHOLD = 0.8

_VALID_TYPES = {"income", "expense"}


# --------------------------------------------------------------------------- #
# Validación de dominio (FR-001..FR-004)
# --------------------------------------------------------------------------- #
def validate_transaction(
    *, type: str, amount_minor: int, date: str
) -> None:
    """Valida una transacción; lanza MoneyError/ValueError con mensaje claro.

    No guarda nada: el rechazo es total (sin guardado parcial, FR-003).
    """
    if type not in _VALID_TYPES:
        raise ValueError("El tipo debe ser 'income' o 'expense'.")
    if not isinstance(amount_minor, int) or isinstance(amount_minor, bool):
        raise MoneyError("El monto no es un número válido.")
    if amount_minor <= 0:
        raise MoneyError("El monto debe ser mayor que cero.")
    _parse_date(date)  # lanza si es inválida


def _parse_date(date_str: str) -> _date:
    try:
        return _date.fromisoformat(date_str)
    except (ValueError, TypeError) as exc:
        raise ValueError("La fecha no es válida (formato YYYY-MM-DD).") from exc


# --------------------------------------------------------------------------- #
# Totales (helpers puros + agregación)
# --------------------------------------------------------------------------- #
def net(income_minor: int, expense_minor: int) -> int:
    """Saldo neto = ingresos - gastos (entero exacto)."""
    return int(income_minor) - int(expense_minor)


def monthly_totals(conn: sqlite3.Connection, year_month: str) -> dict:
    """Ingresos/gastos/neto de un mes ('YYYY-MM'). Solo suma enteros."""
    row = conn.execute(
        "SELECT "
        " COALESCE(SUM(CASE WHEN type='income'  THEN amount_minor END), 0) AS income, "
        " COALESCE(SUM(CASE WHEN type='expense' THEN amount_minor END), 0) AS expense "
        'FROM "transaction" WHERE date LIKE ?',
        (f"{year_month}-%",),
    ).fetchone()
    income = int(row["income"])
    expense = int(row["expense"])
    return {
        "income_minor": income,
        "expense_minor": expense,
        "net_minor": net(income, expense),
    }


def spent_for_category(
    conn: sqlite3.Connection, category_id: int, year_month: str
) -> int:
    """Gasto (expense) de una categoría en un mes."""
    row = conn.execute(
        "SELECT COALESCE(SUM(amount_minor), 0) AS s "
        'FROM "transaction" '
        "WHERE type='expense' AND category_id = ? AND date LIKE ?",
        (category_id, f"{year_month}-%"),
    ).fetchone()
    return int(row["s"] if row else 0)


# --------------------------------------------------------------------------- #
# Presupuestos (FR-009..FR-011)
# --------------------------------------------------------------------------- #
def budget_status(
    spent_minor: int, limit_minor: int, near_threshold: float = NEAR_THRESHOLD
) -> dict:
    """Estado de un presupuesto (puro).

    - ok:       spent < near_threshold * limit
    - near:     near_threshold * limit <= spent <= limit
    - exceeded: spent > limit
    percent y over_by calculados con enteros (percent como ratio de presentación).
    """
    limit_minor = int(limit_minor)
    spent_minor = int(spent_minor)
    over_by = max(0, spent_minor - limit_minor)
    percent = (spent_minor / limit_minor) if limit_minor > 0 else 0.0

    if spent_minor > limit_minor:
        status = "exceeded"
    elif spent_minor * 100 >= int(near_threshold * 100) * limit_minor:
        # Comparación entera equivalente a spent/limit >= near_threshold.
        status = "near"
    else:
        status = "ok"
    return {"spent_minor": spent_minor, "percent": percent, "over_by_minor": over_by, "status": status}


# --------------------------------------------------------------------------- #
# Metas de ahorro (FR-012)
# --------------------------------------------------------------------------- #
def goal_status(
    saved_minor: int,
    target_minor: int,
    target_date: Optional[str],
    today: Optional[str] = None,
) -> dict:
    """Estado de una meta (puro).

    - reached:     saved >= target
    - overdue:     no alcanzada y hoy > target_date
    - in_progress: en otro caso
    """
    saved_minor = int(saved_minor)
    target_minor = int(target_minor)
    percent = (saved_minor / target_minor) if target_minor > 0 else 0.0

    if saved_minor >= target_minor:
        status = "reached"
    elif target_date and today and today > target_date:
        status = "overdue"
    else:
        status = "in_progress"
    return {"saved_minor": saved_minor, "percent": percent, "status": status}
