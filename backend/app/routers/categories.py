"""Endpoints de categorías."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..errors import error_body
from ..repositories import categories as repo
from ..schemas import Category, CategoryCreate

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[Category])
def list_categories(conn: sqlite3.Connection = Depends(get_db)):
    return repo.list_all(conn)


@router.post("/categories", response_model=Category, status_code=201)
def create_category(body: CategoryCreate, conn: sqlite3.Connection = Depends(get_db)):
    try:
        return repo.create(conn, body.name, body.kind, body.color)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=error_body("conflict", "Ya existe una categoría con ese nombre."),
        )


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, conn: sqlite3.Connection = Depends(get_db)):
    result = repo.delete(conn, category_id)
    if result == "not_found":
        raise HTTPException(
            status_code=404, detail=error_body("not_found", "Categoría no encontrada.")
        )
    if result == "is_system":
        raise HTTPException(
            status_code=403,
            detail=error_body("forbidden", "No se puede borrar una categoría del sistema."),
        )
    return None
