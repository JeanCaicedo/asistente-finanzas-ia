"""Endpoints de presupuestos con progreso calculado."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db import get_db
from ..errors import error_body
from ..repositories import budgets as repo
from ..repositories import categories as cat_repo
from ..schemas import BudgetCreate, BudgetProgress
from ..services import finance

router = APIRouter(tags=["budgets"])


def _to_progress(conn: sqlite3.Connection, budget: dict) -> dict:
    cat = cat_repo.get(conn, budget["category_id"])
    spent = finance.spent_for_category(conn, budget["category_id"], budget["year_month"])
    status = finance.budget_status(spent, budget["limit_minor"])
    return {
        "id": budget["id"],
        "category_id": budget["category_id"],
        "category_name": cat["name"] if cat else "Sin categorizar",
        "year_month": budget["year_month"],
        "limit_minor": budget["limit_minor"],
        "spent_minor": status["spent_minor"],
        "percent": status["percent"],
        "over_by_minor": status["over_by_minor"],
        "status": status["status"],
        "currency": budget["currency"],
    }


@router.get("/budgets", response_model=list[BudgetProgress])
def list_budgets(
    year_month: str = Query(...), conn: sqlite3.Connection = Depends(get_db)
):
    return [_to_progress(conn, b) for b in repo.list_for_month(conn, year_month)]


@router.post("/budgets", response_model=BudgetProgress, status_code=201)
def create_budget(body: BudgetCreate, conn: sqlite3.Connection = Depends(get_db)):
    if cat_repo.get(conn, body.category_id) is None:
        raise HTTPException(
            status_code=422, detail=error_body("validation_error", "La categoría no existe.")
        )
    try:
        budget = repo.create(
            conn,
            category_id=body.category_id,
            year_month=body.year_month,
            limit_minor=body.limit_minor,
            currency=body.currency,
        )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=error_body("conflict", "Ya existe un presupuesto para esa categoría y mes."),
        )
    return _to_progress(conn, budget)


@router.delete("/budgets/{budget_id}", status_code=204)
def delete_budget(budget_id: int, conn: sqlite3.Connection = Depends(get_db)):
    if not repo.delete(conn, budget_id):
        raise HTTPException(
            status_code=404, detail=error_body("not_found", "Presupuesto no encontrado.")
        )
    return None
