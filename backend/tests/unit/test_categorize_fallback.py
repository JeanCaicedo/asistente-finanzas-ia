"""Tests del fallback de categorización (sin red / sin clave).

Se fuerza la ausencia de IA para probar el camino determinista.
"""
from __future__ import annotations

import app.services.categorize as categorize
from app.llm import gemini


def test_keyword_match_food():
    assert categorize.fallback_by_keywords("Pago Rappi restaurante") == "Comida"


def test_keyword_match_transport():
    assert categorize.fallback_by_keywords("Viaje en Uber") == "Transporte"


def test_keyword_accent_insensitive():
    assert categorize.fallback_by_keywords("DROGUERÍA la rebaja") == "Salud"


def test_no_match_returns_none():
    assert categorize.fallback_by_keywords("xyz transacción rara 123") is None


def test_empty_description():
    assert categorize.fallback_by_keywords(None) is None
    assert categorize.fallback_by_keywords("") is None


def test_suggest_without_ai_uses_keyword(monkeypatch):
    monkeypatch.setattr(gemini, "is_available", lambda: False)
    result = categorize.suggest("Compra en Amazon")
    assert result["category_name"] == "Compras"
    assert result["status"] == "ai_suggested"
    assert result["source"] == "keyword"


def test_suggest_without_ai_no_match_uncategorized(monkeypatch):
    monkeypatch.setattr(gemini, "is_available", lambda: False)
    result = categorize.suggest("qwerty sin sentido")
    assert result["category_name"] is None
    assert result["status"] == "uncategorized"
    assert result["source"] == "none"
