"""Endpoints de reportes del dashboard."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Query

from ..clock import today_iso
from ..db import get_db
from ..schemas import CategoryReport, MonthlyPoint
from ..services import reports

router = APIRouter(tags=["reports"])


@router.get("/reports/by-category", response_model=CategoryReport)
def report_by_category(
    year_month: str = Query(...), conn: sqlite3.Connection = Depends(get_db)
):
    return reports.by_category(conn, year_month)


@router.get("/reports/monthly", response_model=list[MonthlyPoint])
def report_monthly(
    months: int = Query(default=6, ge=1, le=36),
    conn: sqlite3.Connection = Depends(get_db),
):
    return reports.monthly_series(conn, months, today_iso()[:7])
