"""Tests del importador: mapeo, filas inválidas, duplicados, archivo corrupto."""
from __future__ import annotations

import pytest

from app.repositories import transactions as tx_repo
from app.services import importer

_CSV = (
    "fecha,descripcion,monto\n"
    "2026-07-01,Mercado supermercado,50000\n"
    "2026-07-02,Uber al trabajo,15000\n"
    "no-fecha,Fila mala,abc\n"          # inválida: fecha y monto
    "2026-07-03,Sin monto,\n"           # inválida: monto vacío
)


def test_mapping_and_valid_rows(conn):
    preview = importer.preview(conn, "movimientos.csv", _CSV.encode("utf-8"))
    assert preview["proposed_mapping"]["date"] == "fecha"
    assert preview["proposed_mapping"]["amount"] == "monto"
    assert preview["proposed_mapping"]["description"] == "descripcion"
    assert len(preview["valid_rows"]) == 2
    assert preview["valid_rows"][0]["amount_minor"] == 5000000  # 50000 * 100


def test_invalid_rows_reported(conn):
    preview = importer.preview(conn, "movimientos.csv", _CSV.encode("utf-8"))
    assert len(preview["invalid_rows"]) == 2
    idxs = {r["row_index"] for r in preview["invalid_rows"]}
    assert idxs == {2, 3}


def test_duplicate_detection(conn):
    # Inserta una transacción que coincide exactamente con la primera fila del CSV.
    tx_repo.create(
        conn, type="expense", amount_minor=5000000, currency="COP",
        date="2026-07-01", description="Mercado supermercado",
        category_id=None, category_status="uncategorized", ai_confidence=None,
    )
    preview = importer.preview(conn, "movimientos.csv", _CSV.encode("utf-8"))
    assert len(preview["possible_duplicates"]) == 1
    assert preview["possible_duplicates"][0]["row_index"] == 0


def test_corrupt_file_rejected(conn):
    with pytest.raises(importer.ImportFormatError):
        importer.preview(conn, "archivo.xlsx", b"esto no es un excel valido")


def test_unsupported_extension(conn):
    with pytest.raises(importer.ImportFormatError):
        importer.preview(conn, "archivo.txt", b"cualquier cosa")


def test_dd_mm_yyyy_dates(conn):
    csv = "fecha,descripcion,monto\n01/07/2026,Cine,20000\n"
    preview = importer.preview(conn, "f.csv", csv.encode("utf-8"))
    assert preview["valid_rows"][0]["date"] == "2026-07-01"
