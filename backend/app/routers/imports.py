"""Endpoints de importación CSV/Excel (preview + commit)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..db import get_db
from ..errors import error_body
from ..repositories import transactions as tx_repo
from ..schemas import ImportCommit, ImportPreview, ImportResult
from ..services import categorize, importer
from ..repositories import categories as cat_repo

router = APIRouter(tags=["imports"])


@router.post("/import/preview", response_model=ImportPreview)
async def import_preview(
    file: UploadFile = File(...), conn: sqlite3.Connection = Depends(get_db)
):
    content = await file.read()
    try:
        return importer.preview(conn, file.filename or "", content)
    except importer.ImportFormatError as exc:
        raise HTTPException(
            status_code=415, detail=error_body("unsupported", str(exc))
        )


@router.post("/import/commit", response_model=ImportResult)
def import_commit(body: ImportCommit, conn: sqlite3.Connection = Depends(get_db)):
    created = 0
    skipped: list[dict] = []
    for idx, row in enumerate(body.rows):
        dup_id = tx_repo.find_exact_duplicate(
            conn,
            date=row.date,
            amount_minor=row.amount_minor,
            description=row.description,
        )
        if dup_id is not None and body.skip_duplicates:
            skipped.append({"row_index": idx, "reason": "Duplicado (fecha+monto+descripción)."})
            continue

        # Categorización de la fila (IA/fallback), como en la creación manual.
        suggestion = categorize.suggest(row.description)
        category_id = None
        category_status = suggestion["status"]
        ai_confidence = suggestion["confidence"]
        if suggestion["category_name"]:
            cat = cat_repo.get_by_name(conn, suggestion["category_name"])
            category_id = cat["id"] if cat else None
            if category_id is None:
                category_status = "uncategorized"

        tx_repo.create(
            conn,
            type=row.type,
            amount_minor=row.amount_minor,
            currency=row.currency,
            date=row.date,
            description=row.description,
            category_id=category_id,
            category_status=category_status,
            ai_confidence=ai_confidence,
            source="imported",
        )
        created += 1

    return {"created_count": created, "skipped_count": len(skipped), "skipped": skipped}
