"""Utilidades de fecha/hora. Timestamps en UTC ISO-8601."""
from __future__ import annotations

from datetime import datetime, timezone


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def year_month(date_iso: str) -> str:
    """Extrae 'YYYY-MM' de una fecha 'YYYY-MM-DD'."""
    return date_iso[:7]
