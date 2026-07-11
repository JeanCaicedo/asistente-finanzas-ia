"""Endpoints de metas de ahorro y aportes manuales."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from ..clock import today_iso
from ..db import get_db
from ..errors import error_body
from ..money import MoneyError
from ..repositories import goals as repo
from ..schemas import ContributionCreate, GoalCreate, GoalProgress
from ..services import finance

router = APIRouter(tags=["goals"])


def _to_progress(conn: sqlite3.Connection, goal: dict) -> dict:
    saved = repo.saved_minor(conn, goal["id"])
    status = finance.goal_status(
        saved, goal["target_minor"], goal["target_date"], today_iso()
    )
    return {
        "id": goal["id"],
        "name": goal["name"],
        "target_minor": goal["target_minor"],
        "saved_minor": status["saved_minor"],
        "percent": status["percent"],
        "status": status["status"],
        "target_date": goal["target_date"],
        "currency": goal["currency"],
    }


@router.get("/goals", response_model=list[GoalProgress])
def list_goals(conn: sqlite3.Connection = Depends(get_db)):
    return [_to_progress(conn, g) for g in repo.list_all(conn)]


@router.post("/goals", response_model=GoalProgress, status_code=201)
def create_goal(body: GoalCreate, conn: sqlite3.Connection = Depends(get_db)):
    goal = repo.create(
        conn,
        name=body.name,
        target_minor=body.target_minor,
        currency=body.currency,
        target_date=body.target_date,
    )
    return _to_progress(conn, goal)


@router.post("/goals/{goal_id}/contributions", response_model=GoalProgress, status_code=201)
def add_contribution(
    goal_id: int, body: ContributionCreate, conn: sqlite3.Connection = Depends(get_db)
):
    goal = repo.get(conn, goal_id)
    if goal is None:
        raise HTTPException(
            status_code=404, detail=error_body("not_found", "Meta no encontrada.")
        )
    try:
        finance._parse_date(body.date)  # valida la fecha del aporte
    except (MoneyError, ValueError) as exc:
        raise HTTPException(
            status_code=422, detail=error_body("validation_error", str(exc))
        )
    repo.add_contribution(
        conn,
        goal_id=goal_id,
        amount_minor=body.amount_minor,
        date=body.date,
        note=body.note,
    )
    return _to_progress(conn, goal)
