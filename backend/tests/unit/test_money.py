"""Tests de utilidades de dinero: casos normal, límite y error."""
from __future__ import annotations

import pytest

from app.money import MoneyError, add, format_minor, parse_to_minor


# --- Casos normales ---
def test_parse_integer_string():
    assert parse_to_minor("1000", "COP") == 100000  # 2 decimales


def test_parse_decimal_dot():
    assert parse_to_minor("1234.56", "USD") == 123456


def test_parse_thousands_and_decimal_comma():
    # "1.234,56" → 1234.56
    assert parse_to_minor("1.234,56", "USD") == 123456


def test_parse_thousands_dot_only():
    # "1.234" con separador de miles (>2 decimales tras el punto no aplica aquí)
    assert parse_to_minor("1.000", "COP") == 100000  # 1000.00


def test_parse_currency_symbol_stripped():
    assert parse_to_minor("$ 2.500", "COP") == 250000


def test_parse_int_input():
    assert parse_to_minor(500, "COP") == 50000


def test_zero_decimal_currency():
    assert parse_to_minor("1500", "CLP") == 1500  # CLP no tiene decimales


# --- Límite ---
def test_smallest_positive():
    assert parse_to_minor("0.01", "USD") == 1


# --- Errores ---
def test_empty_raises():
    with pytest.raises(MoneyError):
        parse_to_minor("", "COP")


def test_non_numeric_raises():
    with pytest.raises(MoneyError):
        parse_to_minor("abc", "COP")


def test_zero_raises():
    with pytest.raises(MoneyError):
        parse_to_minor("0", "COP")


def test_negative_raises():
    with pytest.raises(MoneyError):
        parse_to_minor("-10", "COP")


def test_too_many_decimals_raises():
    with pytest.raises(MoneyError):
        parse_to_minor("1.234,567", "USD")  # 3 decimales para moneda de 2


def test_bool_raises():
    with pytest.raises(MoneyError):
        parse_to_minor(True, "COP")


# --- Formato y suma ---
def test_format_minor():
    assert format_minor(123456, "USD") == "1.234,56 USD"


def test_format_zero_decimal():
    assert format_minor(1500, "CLP") == "1.500 CLP"


def test_add_exact():
    assert add(10, 20, 30) == 60
