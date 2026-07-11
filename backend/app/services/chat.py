"""Chat anclado a datos reales (Principio I y IV).

Pipeline: (1) detectar intención y periodo, (2) CALCULAR cifras con finance.py,
(3) construir contexto mínimo + citations, (4) pedir a Gemini SOLO que redacte.
Las cifras del texto provienen del cálculo, nunca del modelo. Sin IA → degradado.
"""
from __future__ import annotations

import re
import sqlite3
import unicodedata
from typing import Optional

from .. import config
from ..clock import today_iso
from ..llm import gemini
from ..money import MoneyError, format_minor, parse_to_minor
from ..repositories import budgets as bud_repo
from ..repositories import categories as cat_repo
from . import finance


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _current_month() -> str:
    return today_iso()[:7]


def _detect_period(question: str) -> str:
    m = re.search(r"(20\d{2})[-/](0[1-9]|1[0-2])", question)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return _current_month()


def _detect_category(conn: sqlite3.Connection, question: str) -> Optional[dict]:
    norm = _normalize(question)
    best = None
    for cat in cat_repo.list_all(conn):
        if _normalize(cat["name"]) in norm:
            best = cat
            break
    return best


def _detect_amount(question: str) -> Optional[int]:
    # Busca un número (con separadores) en la pregunta.
    m = re.search(r"(\d[\d.,]*\d|\d)", question)
    if not m:
        return None
    try:
        return parse_to_minor(m.group(1), config.DEFAULT_CURRENCY)
    except MoneyError:
        return None


def answer(conn: sqlite3.Connection, question: str) -> dict:
    """Resuelve la pregunta de forma determinista y (si hay IA) la redacta."""
    period = _detect_period(question)
    category = _detect_category(conn, question)
    norm = _normalize(question)

    is_affordability = any(
        kw in norm
        for kw in ["puedo permitirme", "me alcanza", "puedo gastar", "puedo comprar", "alcanza para"]
    )
    is_net = any(
        kw in norm for kw in ["neto", "cuanto me queda", "balance", "ahorre", "cuanto gane", "cuanto ingrese"]
    )

    if is_affordability:
        payload = _resolve_affordability(conn, question, period, category)
    elif is_net or category is None:
        payload = _resolve_net(conn, period)
    else:
        payload = _resolve_category_spend(conn, period, category)

    # needs_input corta el pipeline: no se llama a la IA.
    if payload.get("needs_input"):
        return {
            "answer": payload["needs_input"],
            "degraded": not gemini.is_available(),
            "citations": [],
            "needs_input": payload["needs_input"],
        }

    facts_text = payload["facts_text"]
    citations = payload["citations"]

    # Redacción con IA (solo redacta). Degradación explícita si no hay clave/falla.
    drafted = _draft(question, facts_text)
    if drafted is None:
        return {
            "answer": facts_text,
            "degraded": True,
            "citations": citations,
            "needs_input": None,
        }
    return {
        "answer": drafted,
        "degraded": False,
        "citations": citations,
        "needs_input": None,
    }


def _resolve_category_spend(conn, period, category) -> dict:
    from . import reports

    report = reports.by_category(conn, period)
    item = next((i for i in report["items"] if i["category_id"] == category["id"]), None)
    amount = item["amount_minor"] if item else 0
    tx_ids = item["transaction_ids"] if item else []
    facts = f"Gasto en {category['name']} en {period}: {format_minor(amount, config.DEFAULT_CURRENCY)}."
    return {
        "facts_text": facts,
        "citations": [
            {
                "label": f"Gasto en {category['name']}, {period}",
                "amount_minor": amount,
                "period": period,
                "category_id": category["id"],
                "transaction_ids": tx_ids,
            }
        ],
    }


def _resolve_net(conn, period) -> dict:
    totals = finance.monthly_totals(conn, period)
    facts = (
        f"En {period}: ingresos {format_minor(totals['income_minor'], config.DEFAULT_CURRENCY)}, "
        f"gastos {format_minor(totals['expense_minor'], config.DEFAULT_CURRENCY)}, "
        f"neto {format_minor(totals['net_minor'], config.DEFAULT_CURRENCY)}."
    )
    return {
        "facts_text": facts,
        "citations": [
            {
                "label": f"Neto del mes, {period}",
                "amount_minor": totals["net_minor"],
                "period": period,
                "category_id": None,
                "transaction_ids": [],
            }
        ],
    }


def _resolve_affordability(conn, question, period, category) -> dict:
    amount = _detect_amount(question)
    if amount is None:
        return {"needs_input": "¿De qué monto sería el gasto que quieres evaluar?"}

    totals = finance.monthly_totals(conn, period)
    net = totals["net_minor"]
    citations = [
        {
            "label": f"Neto del mes, {period}",
            "amount_minor": net,
            "period": period,
            "category_id": None,
            "transaction_ids": [],
        }
    ]

    budget_note = ""
    if category is not None:
        budgets = bud_repo.list_for_month(conn, period)
        budget = next((b for b in budgets if b["category_id"] == category["id"]), None)
        if budget is not None:
            spent = finance.spent_for_category(conn, category["id"], period)
            remaining = budget["limit_minor"] - spent
            budget_note = (
                f" Presupuesto restante en {category['name']}: "
                f"{format_minor(remaining, config.DEFAULT_CURRENCY)}."
            )
            citations.append(
                {
                    "label": f"Presupuesto restante en {category['name']}, {period}",
                    "amount_minor": remaining,
                    "period": period,
                    "category_id": category["id"],
                    "transaction_ids": [],
                }
            )

    verdict = "sí" if amount <= net else "no"
    facts = (
        f"Gasto evaluado: {format_minor(amount, config.DEFAULT_CURRENCY)}. "
        f"Neto disponible del mes ({period}): {format_minor(net, config.DEFAULT_CURRENCY)}.{budget_note} "
        f"Según el neto disponible, {verdict} alcanza."
    )
    return {"facts_text": facts, "citations": citations}


def _draft(question: str, facts_text: str) -> Optional[str]:
    """Pide a Gemini redactar en lenguaje natural usando SOLO las cifras dadas."""
    if not gemini.is_available():
        return None
    system = (
        "Eres un asistente de finanzas. Redacta una respuesta breve y clara en "
        "español usando EXCLUSIVAMENTE las cifras proporcionadas. No inventes ni "
        "recalcules números. Cita la categoría y el periodo cuando aplique."
    )
    prompt = f"Pregunta del usuario: {question}\nCifras ya calculadas: {facts_text}"
    res = gemini.redactar_texto(system=system, prompt=prompt, max_tokens=250)
    if not res.ok or not isinstance(res.datos, str):
        return None
    return res.datos
