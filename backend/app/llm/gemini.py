"""Adaptador de IA (Gemini). Aísla el proveedor y degrada de forma explícita.

Contrato: si no hay clave, el SDK falta o la llamada falla/expira, se devuelve un
`LLMResult` con `ok=False` y `datos=None`; NUNCA se propaga una excepción hacia el
usuario. Así el resto del código decide el fallback determinista.

Se envía el mínimo contexto necesario (Principio II); quien llama es responsable de
no incluir volcados masivos.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .. import config, logging_util


@dataclass
class LLMResult:
    ok: bool
    datos: Optional[Any] = None
    modelo: Optional[str] = None
    reason: Optional[str] = None  # motivo de degradación (código, no dato sensible)


def is_available() -> bool:
    return config.ai_available()


def generar_json(
    *, system: str, prompt: str, schema: dict, max_tokens: int = 500
) -> LLMResult:
    """Genera JSON validado contra `schema`. Degrada a ok=False ante cualquier fallo."""
    if not config.GEMINI_API_KEY:
        return LLMResult(ok=False, reason="no_api_key")

    try:
        from google import genai
        from google.genai import types
    except Exception:  # SDK no instalado
        logging_util.error("llm.generar_json", "sdk_missing")
        return LLMResult(ok=False, reason="sdk_missing")

    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=schema,
                max_output_tokens=max_tokens,
                # Extracción estructurada: desactivar "thinking" ahorra tokens/latencia.
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        import json

        datos = json.loads(response.text)
        logging_util.event("llm.generar_json", ok=True, model=config.GEMINI_MODEL)
        return LLMResult(ok=True, datos=datos, modelo=config.GEMINI_MODEL)
    except Exception as exc:  # red, cuota, parseo, etc.
        logging_util.error(
            "llm.generar_json", "call_failed", detail=type(exc).__name__
        )
        return LLMResult(ok=False, reason="call_failed")


def redactar_texto(*, system: str, prompt: str, max_tokens: int = 400) -> LLMResult:
    """Redacta texto libre (para el chat). La IA solo redacta, no calcula."""
    if not config.GEMINI_API_KEY:
        return LLMResult(ok=False, reason="no_api_key")

    try:
        from google import genai
        from google.genai import types
    except Exception:
        logging_util.error("llm.redactar_texto", "sdk_missing")
        return LLMResult(ok=False, reason="sdk_missing")

    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        texto = (response.text or "").strip()
        if not texto:
            return LLMResult(ok=False, reason="empty_response")
        logging_util.event("llm.redactar_texto", ok=True, model=config.GEMINI_MODEL)
        return LLMResult(ok=True, datos=texto, modelo=config.GEMINI_MODEL)
    except Exception as exc:
        logging_util.error(
            "llm.redactar_texto", "call_failed", detail=type(exc).__name__
        )
        return LLMResult(ok=False, reason="call_failed")
