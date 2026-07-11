"""Logging que PROHÍBE datos financieros sensibles (Principio II / FR-030).

Solo se registran metadatos: tipo de operación, códigos de error, latencias y
conteos. Nunca `amount_minor`, descripciones ni el texto del chat. El helper
`event()` acepta únicamente valores no sensibles y filtra por lista blanca de
tipos primitivos simples; cualquier intento de pasar montos/descripciones debe
hacerse fuera de este helper (no hay ruta para ello).
"""
from __future__ import annotations

import json
import logging

_logger = logging.getLogger("finanzas")
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)

# Claves explícitamente prohibidas por si alguien las pasa por error.
_FORBIDDEN_KEYS = {
    "amount",
    "amount_minor",
    "description",
    "note",
    "question",
    "answer",
    "limit_minor",
    "target_minor",
    "saved_minor",
    "spent_minor",
}


def _safe_meta(meta: dict) -> dict:
    """Filtra claves prohibidas y valores no primitivos/no seguros."""
    safe: dict = {}
    for key, value in meta.items():
        if key in _FORBIDDEN_KEYS:
            continue
        if isinstance(value, bool) or value is None:
            safe[key] = value
        elif isinstance(value, (int, float)):
            # Se permiten conteos/latencias/códigos numéricos, no montos (filtrados arriba).
            safe[key] = value
        elif isinstance(value, str):
            # Cadenas cortas de tipo/código; se truncan por seguridad.
            safe[key] = value[:64]
    return safe


def event(operation: str, **meta) -> None:
    """Registra un evento de operación con metadatos no sensibles."""
    payload = {"op": operation, **_safe_meta(meta)}
    _logger.info(json.dumps(payload, ensure_ascii=False))


def error(operation: str, code: str, **meta) -> None:
    """Registra un error por código, sin exponer datos sensibles."""
    payload = {"op": operation, "error_code": code, **_safe_meta(meta)}
    _logger.warning(json.dumps(payload, ensure_ascii=False))
