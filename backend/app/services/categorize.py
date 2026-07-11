"""Categorización: IA (Gemini) con fallback determinista por palabras clave.

Nunca bloquea el registro: si no hay clave, la IA falla, o la confianza < umbral,
se usa el fallback por keywords; si tampoco hay match confiable → "Sin categorizar"
(category_status = uncategorized).
"""
from __future__ import annotations

import unicodedata

from .. import config
from ..llm import gemini

# Mapa comercio/keyword → nombre de categoría del sistema.
_KEYWORD_MAP: dict[str, str] = {
    # Comida
    "rappi": "Comida",
    "restaurante": "Comida",
    "mercado": "Comida",
    "supermercado": "Comida",
    "cafe": "Comida",
    "almuerzo": "Comida",
    "pizza": "Comida",
    "comida": "Comida",
    # Transporte
    "uber": "Transporte",
    "didi": "Transporte",
    "taxi": "Transporte",
    "gasolina": "Transporte",
    "combustible": "Transporte",
    "bus": "Transporte",
    "metro": "Transporte",
    "peaje": "Transporte",
    # Vivienda
    "arriendo": "Vivienda",
    "alquiler": "Vivienda",
    "renta": "Vivienda",
    "hipoteca": "Vivienda",
    "administracion": "Vivienda",
    # Servicios
    "luz": "Servicios",
    "agua": "Servicios",
    "energia": "Servicios",
    "internet": "Servicios",
    "telefono": "Servicios",
    "celular": "Servicios",
    "gas": "Servicios",
    "netflix": "Servicios",
    "spotify": "Servicios",
    # Ocio
    "cine": "Ocio",
    "bar": "Ocio",
    "concierto": "Ocio",
    "juego": "Ocio",
    "viaje": "Ocio",
    # Salud
    "farmacia": "Salud",
    "droguería": "Salud",
    "drogueria": "Salud",
    "medico": "Salud",
    "clinica": "Salud",
    "eps": "Salud",
    # Compras
    "amazon": "Compras",
    "mercadolibre": "Compras",
    "ropa": "Compras",
    "tienda": "Compras",
    "falabella": "Compras",
    # Ingresos
    "salario": "Salario",
    "nomina": "Salario",
    "sueldo": "Salario",
    "pago nomina": "Salario",
}

# Categorías válidas para la salida de la IA (nombres del sistema).
_ALLOWED = [
    "Comida",
    "Transporte",
    "Vivienda",
    "Servicios",
    "Ocio",
    "Salud",
    "Compras",
    "Salario",
    "Otros ingresos",
]


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def fallback_by_keywords(description: str | None) -> str | None:
    """Devuelve el nombre de categoría por keyword, o None si no hay match confiable."""
    if not description:
        return None
    norm = _normalize(description)
    for keyword, category in _KEYWORD_MAP.items():
        if _normalize(keyword) in norm:
            return category
    return None


def suggest(description: str | None) -> dict:
    """Sugiere una categoría para una descripción.

    Devuelve: {category_name, status, confidence, source}
      - status: 'ai_suggested' | 'uncategorized'
      - source: 'ai' | 'keyword' | 'none'
    La resolución del nombre → category_id la hace el router (usa el repositorio).
    """
    # 1) Ruta IA (si hay clave). Salida JSON: categoria + confianza.
    if gemini.is_available() and description:
        result = _suggest_ai(description)
        if result is not None:
            return result

    # 2) Fallback determinista por palabras clave.
    kw = fallback_by_keywords(description)
    if kw is not None:
        return {
            "category_name": kw,
            "status": "ai_suggested",
            "confidence": None,
            "source": "keyword",
        }

    # 3) Sin match confiable.
    return {
        "category_name": None,
        "status": "uncategorized",
        "confidence": None,
        "source": "none",
    }


_AI_SCHEMA = {
    "type": "object",
    "properties": {
        "categoria": {"type": "string", "enum": _ALLOWED},
        "confianza": {"type": "number"},
    },
    "required": ["categoria", "confianza"],
}


def _suggest_ai(description: str) -> dict | None:
    system = (
        "Eres un clasificador de transacciones financieras. Devuelve SOLO la "
        "categoría más probable de la lista permitida y una confianza 0..1. "
        "No inventes categorías fuera de la lista."
    )
    prompt = (
        f"Descripción de la transacción: {description}\n"
        f"Categorías permitidas: {', '.join(_ALLOWED)}"
    )
    res = gemini.generar_json(system=system, prompt=prompt, schema=_AI_SCHEMA, max_tokens=100)
    if not res.ok or not isinstance(res.datos, dict):
        return None  # degrada al fallback
    categoria = res.datos.get("categoria")
    try:
        confianza = float(res.datos.get("confianza"))
    except (TypeError, ValueError):
        return None
    if categoria not in _ALLOWED:
        return None
    if confianza < config.AI_CONFIDENCE_THRESHOLD:
        # Sugerencia débil: preferimos el fallback / sin categorizar.
        return None
    return {
        "category_name": categoria,
        "status": "ai_suggested",
        "confidence": confianza,
        "source": "ai",
    }
