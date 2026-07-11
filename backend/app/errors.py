"""Formato de error uniforme {error:{code,message,details}} (D10 / FR-031).

Los mensajes NUNCA incluyen montos ni descripciones sensibles.
"""
from __future__ import annotations


def error_body(code: str, message: str, details: list[str] | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or []}}
