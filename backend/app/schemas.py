"""Esquemas Pydantic (entrada/salida). Montos como enteros `*_minor` + `currency`.

Espejan `contracts/openapi.yaml`. El frontend nunca hace aritmética: consume estas
cifras ya calculadas.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

TxType = Literal["income", "expense"]
CategoryKind = Literal["expense", "income", "both"]
CategoryStatus = Literal["ai_suggested", "user_confirmed", "uncategorized"]
BudgetStatus = Literal["ok", "near", "exceeded"]
GoalStatus = Literal["in_progress", "reached", "overdue"]


# --- Categorías ---
class Category(BaseModel):
    id: int
    name: str
    kind: CategoryKind
    is_system: bool
    color: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1)
    kind: CategoryKind
    color: Optional[str] = None


# --- Transacciones ---
class Transaction(BaseModel):
    id: int
    type: TxType
    amount_minor: int
    currency: str
    date: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    category_status: CategoryStatus
    ai_confidence: Optional[float] = None
    source: Literal["manual", "imported"]


class TransactionCreate(BaseModel):
    type: TxType
    amount_minor: int = Field(gt=0)
    currency: str
    date: str
    description: Optional[str] = None
    category_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    type: Optional[TxType] = None
    amount_minor: Optional[int] = Field(default=None, gt=0)
    date: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None


# --- Presupuestos ---
class BudgetCreate(BaseModel):
    category_id: int
    year_month: str
    limit_minor: int = Field(gt=0)
    currency: str


class BudgetProgress(BaseModel):
    id: int
    category_id: int
    category_name: str
    year_month: str
    limit_minor: int
    spent_minor: int
    percent: float
    over_by_minor: int
    status: BudgetStatus
    currency: str


# --- Metas ---
class GoalCreate(BaseModel):
    name: str = Field(min_length=1)
    target_minor: int = Field(gt=0)
    currency: str
    target_date: Optional[str] = None


class ContributionCreate(BaseModel):
    amount_minor: int = Field(gt=0)
    date: str
    note: Optional[str] = None


class GoalProgress(BaseModel):
    id: int
    name: str
    target_minor: int
    saved_minor: int
    percent: float
    status: GoalStatus
    target_date: Optional[str] = None
    currency: str


# --- Reportes ---
class CategoryReportItem(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    amount_minor: int
    transaction_ids: list[int]


class CategoryReport(BaseModel):
    year_month: str
    currency: str
    total_minor: int
    items: list[CategoryReportItem]


class MonthlyPoint(BaseModel):
    year_month: str
    income_minor: int
    expense_minor: int
    net_minor: int
    currency: str


# --- Importación ---
class ProposedMapping(BaseModel):
    date: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None


class InvalidRow(BaseModel):
    row_index: int
    reason: str


class DuplicateRow(BaseModel):
    row_index: int
    existing_transaction_id: int


class ImportPreview(BaseModel):
    columns: list[str]
    proposed_mapping: ProposedMapping
    valid_rows: list[TransactionCreate]
    invalid_rows: list[InvalidRow]
    possible_duplicates: list[DuplicateRow]


class ImportCommit(BaseModel):
    rows: list[TransactionCreate]
    skip_duplicates: bool = True


class SkippedRow(BaseModel):
    row_index: int
    reason: str


class ImportResult(BaseModel):
    created_count: int
    skipped_count: int
    skipped: list[SkippedRow]


# --- Chat ---
class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


class Citation(BaseModel):
    label: str
    amount_minor: Optional[int] = None
    period: Optional[str] = None
    category_id: Optional[int] = None
    transaction_ids: list[int] = Field(default_factory=list)


class ChatAnswer(BaseModel):
    answer: str
    degraded: bool
    citations: list[Citation] = Field(default_factory=list)
    needs_input: Optional[str] = None
