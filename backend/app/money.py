"""Utilidades de dinero: aritmética entera exacta en unidades menores (céntimos).

Regla del Principio I: el dinero JAMÁS se representa con float. Todo monto vive
como entero en unidades menores (`*_minor`). Este módulo centraliza el parseo de
texto a enteros, el formato de presentación y la aritmética.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

# Número de decimales por moneda (unidades menores por unidad mayor).
# La demo usa moneda única, pero dejamos el mapa por claridad.
_MINOR_UNITS: dict[str, int] = {
    "COP": 2,
    "USD": 2,
    "EUR": 2,
    "CLP": 0,
    "JPY": 0,
}
_DEFAULT_MINOR_UNITS = 2


class MoneyError(ValueError):
    """Error de parseo/validación de un monto de dinero."""


def minor_units(currency: str) -> int:
    return _MINOR_UNITS.get((currency or "").upper(), _DEFAULT_MINOR_UNITS)


def parse_to_minor(value: str | int | float | Decimal, currency: str = "COP") -> int:
    """Convierte un texto/numero a entero en unidades menores.

    Acepta strings como "1.234,56", "1234.56", "$ 1.234", "1000". Rechaza vacío,
    no numérico y valores no positivos con MoneyError. Nunca usa float internamente.
    """
    if value is None:
        raise MoneyError("El monto es obligatorio.")

    exp = minor_units(currency)

    if isinstance(value, bool):  # bool es subclase de int; no es un monto válido
        raise MoneyError("El monto no es un número válido.")

    if isinstance(value, int):
        dec = Decimal(value)
    elif isinstance(value, Decimal):
        dec = value
    elif isinstance(value, float):
        # NaN/inf (p. ej. celdas vacías de pandas) no son montos válidos.
        if value != value or value in (float("inf"), float("-inf")):
            raise MoneyError("El monto no es un número válido.")
        # Convertimos vía str para evitar arrastrar ruido binario del float.
        dec = Decimal(str(value))
    else:
        text = str(value).strip()
        if not text:
            raise MoneyError("El monto es obligatorio.")
        dec = _parse_decimal_text(text)

    if dec <= 0:
        raise MoneyError("El monto debe ser mayor que cero.")

    # Escala a unidades menores. Debe quedar exacto (sin más decimales que la moneda).
    scaled = dec * (Decimal(10) ** exp)
    if scaled != scaled.to_integral_value():
        raise MoneyError(
            f"El monto tiene más decimales de los que admite la moneda ({exp})."
        )
    return int(scaled)


def _parse_decimal_text(text: str) -> Decimal:
    # Quita símbolos de moneda y espacios (incluye no-break space).
    cleaned = re.sub(r"[^\d.,\-]", "", text.replace(" ", " ")).strip()
    if not cleaned or cleaned in {"-", ".", ","}:
        raise MoneyError("El monto no es un número válido.")

    has_dot = "." in cleaned
    has_comma = "," in cleaned

    if has_dot and has_comma:
        # El separador decimal es el que aparece más a la derecha.
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif has_comma:
        # Coma sola: si hay exactamente 1-2 dígitos tras la única coma la tratamos
        # como decimal; si no, como separador de miles.
        parts = cleaned.split(",")
        tail = parts[-1]
        if len(parts) == 2 and 1 <= len(tail) <= 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif has_dot:
        # Punto solo: mismo criterio. 1-2 dígitos tras un único punto = decimal;
        # cualquier otro caso (varios puntos, o 3 dígitos) = separador de miles.
        parts = cleaned.split(".")
        tail = parts[-1]
        if len(parts) == 2 and 1 <= len(tail) <= 2:
            pass  # ya es decimal parseable
        else:
            cleaned = cleaned.replace(".", "")
    # Solo dígitos: ya es parseable como Decimal.

    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:  # pragma: no cover - defensivo
        raise MoneyError("El monto no es un número válido.") from exc


def format_minor(amount_minor: int, currency: str = "COP") -> str:
    """Formatea un entero menor a texto de presentación (solo para mostrar)."""
    exp = minor_units(currency)
    negative = amount_minor < 0
    n = abs(int(amount_minor))
    if exp == 0:
        body = f"{n:,}".replace(",", ".")
    else:
        unit, frac = divmod(n, 10 ** exp)
        body = f"{unit:,}".replace(",", ".") + "," + str(frac).zfill(exp)
    sign = "-" if negative else ""
    return f"{sign}{body} {currency.upper()}"


def add(*amounts_minor: int) -> int:
    """Suma exacta de enteros menores."""
    total = 0
    for a in amounts_minor:
        total += int(a)
    return total


def percent(part_minor: int, whole_minor: int) -> float:
    """Porcentaje 0..1+ como float SOLO para presentación/estado (nunca para dinero).

    Devuelve 0.0 si el total es 0 para evitar división por cero.
    """
    if whole_minor == 0:
        return 0.0
    return part_minor / whole_minor
