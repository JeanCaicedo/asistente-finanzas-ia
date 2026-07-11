"""Test de privacidad de logs (SC-009 / FR-030): ni montos ni descripciones."""
from __future__ import annotations

import logging

from app import logging_util


def test_event_filters_forbidden_keys(caplog):
    with caplog.at_level(logging.INFO, logger="finanzas"):
        logging_util.event(
            "tx.create",
            amount_minor=123456,
            description="Pago secreto Rappi",
            count=3,
            ok=True,
        )
    text = caplog.text
    assert "123456" not in text
    assert "Pago secreto Rappi" not in text
    assert "tx.create" in text
    assert "count" in text  # metadato no sensible sí aparece


def test_error_filters_forbidden_keys(caplog):
    with caplog.at_level(logging.WARNING, logger="finanzas"):
        logging_util.error("chat", "call_failed", question="dato privado", latency_ms=42)
    text = caplog.text
    assert "dato privado" not in text
    assert "call_failed" in text
    assert "42" in text


def test_string_values_truncated(caplog):
    with caplog.at_level(logging.INFO, logger="finanzas"):
        logging_util.event("op", model="x" * 200)
    # No debe volcar cadenas arbitrariamente largas.
    for record in caplog.records:
        assert len(record.getMessage()) < 300
