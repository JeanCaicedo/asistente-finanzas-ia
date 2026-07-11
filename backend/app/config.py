"""Carga de configuración desde el entorno (.env).

Nunca se hardcodea la clave de Gemini: solo se lee de variables de entorno.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Carga .env ubicado en backend/ (un nivel por encima de app/).
_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env")


def _get(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return value if value is not None else default


# --- IA (Gemini) ---
GEMINI_API_KEY: str = _get("GEMINI_API_KEY").strip()
GEMINI_MODEL: str = _get("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

# Umbral de confianza para aceptar la sugerencia de la IA (D4).
AI_CONFIDENCE_THRESHOLD: float = float(_get("AI_CONFIDENCE_THRESHOLD", "0.6") or "0.6")

# --- Dinero / moneda ---
DEFAULT_CURRENCY: str = _get("DEFAULT_CURRENCY", "COP").strip() or "COP"

# --- Persistencia ---
_db_env = _get("DB_PATH").strip()
DB_PATH: Path = Path(_db_env) if _db_env else (_BACKEND_DIR / "data" / "finanzas.db")
if not DB_PATH.is_absolute():
    DB_PATH = _BACKEND_DIR / DB_PATH

# --- CORS (origen de Vite) ---
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in _get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]


def ai_available() -> bool:
    """True si hay clave configurada (no garantiza que la llamada tenga éxito)."""
    return bool(GEMINI_API_KEY)
