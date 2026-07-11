"""Tests del chat: cifra == reporte, cita fuentes, degradado, needs_input.

Se fuerza la ausencia de IA para probar el pipeline determinista (degradado).
"""
from __future__ import annotations

import pytest

import app.services.chat as chat
from app.llm import gemini
from app.repositories import categories as cat_repo
from app.repositories import transactions as tx_repo
from app.services import reports


@pytest.fixture(autouse=True)
def _no_ai(monkeypatch):
    monkeypatch.setattr(gemini, "is_available", lambda: False)


def _exp(conn, cat_id, amount, date):
    return tx_repo.create(
        conn, type="expense", amount_minor=amount, currency="COP", date=date,
        description=None, category_id=cat_id, category_status="user_confirmed",
        ai_confidence=None,
    )


def test_category_spend_matches_report(seeded_conn):
    comida = cat_repo.get_by_name(seeded_conn, "Comida")["id"]
    _exp(seeded_conn, comida, 3000, "2026-07-01")
    _exp(seeded_conn, comida, 2000, "2026-07-02")
    period = "2026-07"

    report = reports.by_category(seeded_conn, period)
    report_amount = next(i["amount_minor"] for i in report["items"] if i["category_id"] == comida)

    result = chat.answer(seeded_conn, "cuánto gasté en comida en 2026-07")
    assert result["degraded"] is True  # sin IA
    cite = result["citations"][0]
    assert cite["amount_minor"] == report_amount == 5000
    assert cite["category_id"] == comida
    assert cite["period"] == period


def test_net_question_cites_period(seeded_conn):
    tx_repo.create(
        seeded_conn, type="income", amount_minor=100000, currency="COP",
        date="2026-07-01", description=None, category_id=None,
        category_status="uncategorized", ai_confidence=None,
    )
    result = chat.answer(seeded_conn, "¿cuál es mi neto en 2026-07?")
    assert result["citations"][0]["amount_minor"] == 100000


def test_affordability_needs_input(seeded_conn):
    result = chat.answer(seeded_conn, "¿puedo permitirme este gasto?")
    assert result["needs_input"] is not None
    assert result["citations"] == []


def test_affordability_with_amount(seeded_conn):
    tx_repo.create(
        seeded_conn, type="income", amount_minor=500000, currency="COP",
        date="2026-07-01", description=None, category_id=None,
        category_status="uncategorized", ai_confidence=None,
    )
    result = chat.answer(seeded_conn, "¿puedo permitirme un gasto de 1000 en 2026-07?")
    assert result["needs_input"] is None
    assert result["citations"]  # cita el neto del mes


def test_degraded_answer_contains_figures(seeded_conn):
    # Sin IA, la respuesta es el texto de cifras deterministas (no vacío).
    result = chat.answer(seeded_conn, "neto de 2026-07")
    assert result["degraded"] is True
    assert result["answer"]
