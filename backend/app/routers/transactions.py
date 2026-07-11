"""Endpoints de transacciones (con sugerencia de categoría de la IA en la creación)."""
from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db import get_db
from ..errors import error_body
from ..money import MoneyError
from ..repositories import categories as cat_repo
from ..repositories import transactions as repo
from ..schemas import Transaction, TransactionCreate, TransactionUpdate
from ..services import categorize, finance

router = APIRouter(tags=["transactions"])


@router.get("/transactions", response_model=list[Transaction])
def list_transactions(
    year_month: Optional[str] = Query(default=None),
    category_id: Optional[int] = Query(default=None),
    type: Optional[str] = Query(default=None),
    conn: sqlite3.Connection = Depends(get_db),
):
    return repo.list_(conn, year_month=year_month, category_id=category_id, type=type)


@router.post("/transactions", response_model=Transaction, status_code=201)
def create_transaction(body: TransactionCreate, conn: sqlite3.Connection = Depends(get_db)):
    try:
        finance.validate_transaction(
            type=body.type, amount_minor=body.amount_minor, date=body.date
        )
    except (MoneyError, ValueError) as exc:
        raise HTTPException(
            status_code=422, detail=error_body("validation_error", str(exc))
        )

    category_id = body.category_id
    category_status = "uncategorized"
    ai_confidence = None

    if category_id is not None:
        # El usuario eligió categoría → prevalece (user_confirmed).
        if cat_repo.get(conn, category_id) is None:
            raise HTTPException(
                status_code=422,
                detail=error_body("validation_error", "La categoría no existe."),
            )
        category_status = "user_confirmed"
    else:
        # Sin categoría: la IA/fallback sugiere (US2). Metadato, nunca cálculo.
        suggestion = categorize.suggest(body.description)
        category_status = suggestion["status"]
        ai_confidence = suggestion["confidence"]
        if suggestion["category_name"]:
            cat = cat_repo.get_by_name(conn, suggestion["category_name"])
            category_id = cat["id"] if cat else None
            if category_id is None:
                category_status = "uncategorized"

    return repo.create(
        conn,
        type=body.type,
        amount_minor=body.amount_minor,
        currency=body.currency,
        date=body.date,
        description=body.description,
        category_id=category_id,
        category_status=category_status,
        ai_confidence=ai_confidence,
        source="manual",
    )


@router.patch("/transactions/{tx_id}", response_model=Transaction)
def update_transaction(
    tx_id: int, body: TransactionUpdate, conn: sqlite3.Connection = Depends(get_db)
):
    existing = repo.get(conn, tx_id)
    if existing is None:
        raise HTTPException(
            status_code=404, detail=error_body("not_found", "Transacción no encontrada.")
        )

    fields = body.model_dump(exclude_unset=True)

    # Validaciones de dominio sobre los campos presentes.
    new_type = fields.get("type", existing["type"])
    new_amount = fields.get("amount_minor", existing["amount_minor"])
    new_date = fields.get("date", existing["date"])
    try:
        finance.validate_transaction(
            type=new_type, amount_minor=new_amount, date=new_date
        )
    except (MoneyError, ValueError) as exc:
        raise HTTPException(
            status_code=422, detail=error_body("validation_error", str(exc))
        )

    # Corregir categoría → user_confirmed prevalece sobre la IA (FR-006).
    if "category_id" in fields:
        cid = fields["category_id"]
        if cid is not None:
            if cat_repo.get(conn, cid) is None:
                raise HTTPException(
                    status_code=422,
                    detail=error_body("validation_error", "La categoría no existe."),
                )
            fields["category_status"] = "user_confirmed"
        else:
            fields["category_status"] = "uncategorized"
        fields["ai_confidence"] = None

    return repo.update(conn, tx_id, fields)


@router.delete("/transactions/{tx_id}", status_code=204)
def delete_transaction(tx_id: int, conn: sqlite3.Connection = Depends(get_db)):
    if not repo.delete(conn, tx_id):
        raise HTTPException(
            status_code=404, detail=error_body("not_found", "Transacción no encontrada.")
        )
    return None
