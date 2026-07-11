"""Importación CSV/Excel con pandas: mapeo de columnas, validación fila a fila y
detección de duplicados (FR-023..FR-026). Nunca hay carga parcial silenciosa: el
preview reporta filas inválidas y duplicados; el commit inserta solo lo confirmado.
"""
from __future__ import annotations

import io
import sqlite3
from datetime import date as _date
from typing import Optional

from .. import config
from ..money import MoneyError, parse_to_minor
from ..repositories import transactions as tx_repo

_DATE_HINTS = ["fecha", "date", "dia", "día"]
_DESC_HINTS = ["descripcion", "descripción", "description", "detalle", "concepto", "comercio"]
_AMOUNT_HINTS = ["monto", "amount", "valor", "importe", "cantidad", "total"]


class ImportFormatError(Exception):
    """Archivo no soportado o corrupto."""


def _read_dataframe(filename: str, content: bytes):
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise ImportFormatError("Dependencia de importación no disponible.") from exc

    name = (filename or "").lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(io.BytesIO(content))
        if name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(io.BytesIO(content))
    except Exception as exc:
        raise ImportFormatError("El archivo está corrupto o no se pudo leer.") from exc
    raise ImportFormatError("Formato no soportado (usa CSV o Excel).")


def _match_column(columns: list[str], hints: list[str]) -> Optional[str]:
    lowered = {c: str(c).strip().lower() for c in columns}
    for col, low in lowered.items():
        if low in hints:
            return col
    for col, low in lowered.items():
        if any(h in low for h in hints):
            return col
    return None


def _normalize_date(value) -> Optional[str]:
    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "none"}:
        return None
    # ISO directo
    try:
        return _date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        pass
    # dd/mm/yyyy o dd-mm-yyyy
    for sep in ("/", "-"):
        parts = text.split(sep)
        if len(parts) == 3:
            try:
                d, m, y = (int(p) for p in parts)
                if y < 100:
                    y += 2000
                return _date(y, m, d).isoformat()
            except ValueError:
                continue
    return None


def preview(conn: sqlite3.Connection, filename: str, content: bytes) -> dict:
    """Analiza el archivo y produce el preview (sin insertar nada)."""
    df = _read_dataframe(filename, content)
    columns = [str(c) for c in df.columns]

    mapping = {
        "date": _match_column(columns, _DATE_HINTS),
        "description": _match_column(columns, _DESC_HINTS),
        "amount": _match_column(columns, _AMOUNT_HINTS),
    }

    valid_rows: list[dict] = []
    invalid_rows: list[dict] = []
    possible_duplicates: list[dict] = []

    if not mapping["date"] or not mapping["amount"]:
        # Sin columnas mínimas no se puede construir ninguna fila válida.
        return {
            "columns": columns,
            "proposed_mapping": mapping,
            "valid_rows": [],
            "invalid_rows": [
                {"row_index": -1, "reason": "No se detectaron columnas de fecha y monto."}
            ],
            "possible_duplicates": [],
        }

    for idx, raw in df.iterrows():
        row_index = int(idx)
        date_iso = _normalize_date(raw[mapping["date"]])
        if date_iso is None:
            invalid_rows.append({"row_index": row_index, "reason": "Fecha inválida o vacía."})
            continue
        try:
            amount_minor = parse_to_minor(raw[mapping["amount"]], config.DEFAULT_CURRENCY)
        except MoneyError as exc:
            invalid_rows.append({"row_index": row_index, "reason": str(exc)})
            continue

        description = None
        if mapping["description"]:
            d = str(raw[mapping["description"]]).strip()
            description = d if d and d.lower() not in {"nan", "none"} else None

        row = {
            "type": "expense",
            "amount_minor": amount_minor,
            "currency": config.DEFAULT_CURRENCY,
            "date": date_iso,
            "description": description,
            "category_id": None,
        }
        dup_id = tx_repo.find_exact_duplicate(
            conn, date=date_iso, amount_minor=amount_minor, description=description
        )
        if dup_id is not None:
            possible_duplicates.append(
                {"row_index": row_index, "existing_transaction_id": dup_id}
            )
        valid_rows.append(row)

    return {
        "columns": columns,
        "proposed_mapping": mapping,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "possible_duplicates": possible_duplicates,
    }
