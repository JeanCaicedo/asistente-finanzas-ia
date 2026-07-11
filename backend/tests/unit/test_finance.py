"""Tests de cálculos financieros: totales, presupuestos y progreso de metas."""
from __future__ import annotations

from app.repositories import transactions as tx_repo
from app.services import finance


def _add_expense(conn, cat_id, amount, date, cur="COP"):
    return tx_repo.create(
        conn, type="expense", amount_minor=amount, currency=cur, date=date,
        description=None, category_id=cat_id, category_status="user_confirmed",
        ai_confidence=None,
    )


def _add_income(conn, amount, date, cur="COP"):
    return tx_repo.create(
        conn, type="income", amount_minor=amount, currency=cur, date=date,
        description=None, category_id=None, category_status="uncategorized",
        ai_confidence=None,
    )


# --- Totales mensuales ---
def test_monthly_totals_normal(seeded_conn):
    _add_income(seeded_conn, 100000, "2026-07-01")
    _add_expense(seeded_conn, None, 30000, "2026-07-05")
    totals = finance.monthly_totals(seeded_conn, "2026-07")
    assert totals == {"income_minor": 100000, "expense_minor": 30000, "net_minor": 70000}


def test_monthly_totals_empty(seeded_conn):
    totals = finance.monthly_totals(seeded_conn, "2020-01")
    assert totals == {"income_minor": 0, "expense_minor": 0, "net_minor": 0}


def test_monthly_totals_month_boundary(seeded_conn):
    # Fin/inicio de mes: cada transacción cuenta en el mes de su fecha.
    _add_expense(seeded_conn, None, 1000, "2026-07-31")
    _add_expense(seeded_conn, None, 2000, "2026-08-01")
    assert finance.monthly_totals(seeded_conn, "2026-07")["expense_minor"] == 1000
    assert finance.monthly_totals(seeded_conn, "2026-08")["expense_minor"] == 2000


def test_net_pure():
    assert finance.net(100, 40) == 60
    assert finance.net(40, 100) == -60


# --- Presupuestos ---
def test_budget_status_ok():
    r = finance.budget_status(spent_minor=1000, limit_minor=10000)
    assert r["status"] == "ok"
    assert r["over_by_minor"] == 0


def test_budget_status_near_at_80():
    r = finance.budget_status(spent_minor=8000, limit_minor=10000)
    assert r["status"] == "near"  # exactamente 80%


def test_budget_status_near_below_100():
    r = finance.budget_status(spent_minor=9500, limit_minor=10000)
    assert r["status"] == "near"


def test_budget_status_exceeded():
    r = finance.budget_status(spent_minor=12000, limit_minor=10000)
    assert r["status"] == "exceeded"
    assert r["over_by_minor"] == 2000


def test_budget_status_no_spend_is_zero_percent():
    r = finance.budget_status(spent_minor=0, limit_minor=10000)
    assert r["status"] == "ok"
    assert r["percent"] == 0.0


# --- Metas ---
def test_goal_in_progress():
    r = finance.goal_status(saved_minor=5000, target_minor=10000, target_date=None, today="2026-07-10")
    assert r["status"] == "in_progress"


def test_goal_reached():
    r = finance.goal_status(saved_minor=10000, target_minor=10000, target_date="2026-12-31", today="2026-07-10")
    assert r["status"] == "reached"


def test_goal_overdue():
    r = finance.goal_status(saved_minor=5000, target_minor=10000, target_date="2026-06-30", today="2026-07-10")
    assert r["status"] == "overdue"


def test_goal_reached_beats_overdue():
    # Alcanzada aunque la fecha haya pasado → reached, no overdue.
    r = finance.goal_status(saved_minor=10000, target_minor=10000, target_date="2026-06-30", today="2026-07-10")
    assert r["status"] == "reached"


# --- Gasto por categoría (agregación) ---
def test_spent_for_category(seeded_conn):
    from app.repositories import categories as cat_repo
    comida = cat_repo.get_by_name(seeded_conn, "Comida")["id"]
    _add_expense(seeded_conn, comida, 3000, "2026-07-02")
    _add_expense(seeded_conn, comida, 2000, "2026-07-09")
    _add_expense(seeded_conn, comida, 9999, "2026-08-01")  # otro mes
    assert finance.spent_for_category(seeded_conn, comida, "2026-07") == 5000
