"""Tests de reportes: suma==total, periodo vacío, trazabilidad de ids."""
from __future__ import annotations

from app.repositories import categories as cat_repo
from app.repositories import transactions as tx_repo
from app.services import reports


def _exp(conn, cat_id, amount, date, desc=None):
    return tx_repo.create(
        conn, type="expense", amount_minor=amount, currency="COP", date=date,
        description=desc, category_id=cat_id, category_status="user_confirmed",
        ai_confidence=None,
    )


def test_sum_equals_total(seeded_conn):
    comida = cat_repo.get_by_name(seeded_conn, "Comida")["id"]
    transporte = cat_repo.get_by_name(seeded_conn, "Transporte")["id"]
    _exp(seeded_conn, comida, 3000, "2026-07-01")
    _exp(seeded_conn, comida, 2000, "2026-07-02")
    _exp(seeded_conn, transporte, 1500, "2026-07-03")
    report = reports.by_category(seeded_conn, "2026-07")
    assert report["total_minor"] == 6500
    assert sum(i["amount_minor"] for i in report["items"]) == report["total_minor"]


def test_empty_period(seeded_conn):
    report = reports.by_category(seeded_conn, "2000-01")
    assert report["total_minor"] == 0
    assert report["items"] == []


def test_uncategorized_grouped(seeded_conn):
    _exp(seeded_conn, None, 4000, "2026-07-01")
    report = reports.by_category(seeded_conn, "2026-07")
    labels = [i["category_name"] for i in report["items"]]
    assert "Sin categorizar" in labels
    assert report["total_minor"] == 4000


def test_traceability_ids(seeded_conn):
    comida = cat_repo.get_by_name(seeded_conn, "Comida")["id"]
    t1 = _exp(seeded_conn, comida, 3000, "2026-07-01")
    t2 = _exp(seeded_conn, comida, 2000, "2026-07-02")
    report = reports.by_category(seeded_conn, "2026-07")
    item = next(i for i in report["items"] if i["category_id"] == comida)
    assert set(item["transaction_ids"]) == {t1["id"], t2["id"]}


def test_monthly_series_length(seeded_conn):
    series = reports.monthly_series(seeded_conn, 3, "2026-07")
    assert [p["year_month"] for p in series] == ["2026-05", "2026-06", "2026-07"]
