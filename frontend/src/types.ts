// Tipos TS espejo de los contratos (contracts/openapi.yaml).
// El frontend NUNCA hace aritmética de dinero: consume estas cifras ya calculadas.

export type TxType = "income" | "expense";
export type CategoryKind = "expense" | "income" | "both";
export type CategoryStatus = "ai_suggested" | "user_confirmed" | "uncategorized";
export type BudgetStatus = "ok" | "near" | "exceeded";
export type GoalStatus = "in_progress" | "reached" | "overdue";

export interface Category {
  id: number;
  name: string;
  kind: CategoryKind;
  is_system: boolean;
  color?: string | null;
}

export interface Transaction {
  id: number;
  type: TxType;
  amount_minor: number;
  currency: string;
  date: string;
  description?: string | null;
  category_id?: number | null;
  category_status: CategoryStatus;
  ai_confidence?: number | null;
  source: "manual" | "imported";
}

export interface TransactionCreate {
  type: TxType;
  amount_minor: number;
  currency: string;
  date: string;
  description?: string | null;
  category_id?: number | null;
}

export interface BudgetProgress {
  id: number;
  category_id: number;
  category_name: string;
  year_month: string;
  limit_minor: number;
  spent_minor: number;
  percent: number;
  over_by_minor: number;
  status: BudgetStatus;
  currency: string;
}

export interface GoalProgress {
  id: number;
  name: string;
  target_minor: number;
  saved_minor: number;
  percent: number;
  status: GoalStatus;
  target_date?: string | null;
  currency: string;
}

export interface CategoryReportItem {
  category_id?: number | null;
  category_name: string;
  amount_minor: number;
  transaction_ids: number[];
}

export interface CategoryReport {
  year_month: string;
  currency: string;
  total_minor: number;
  items: CategoryReportItem[];
}

export interface MonthlyPoint {
  year_month: string;
  income_minor: number;
  expense_minor: number;
  net_minor: number;
  currency: string;
}

export interface ImportPreview {
  columns: string[];
  proposed_mapping: { date?: string | null; description?: string | null; amount?: string | null };
  valid_rows: TransactionCreate[];
  invalid_rows: { row_index: number; reason: string }[];
  possible_duplicates: { row_index: number; existing_transaction_id: number }[];
}

export interface ImportResult {
  created_count: number;
  skipped_count: number;
  skipped: { row_index: number; reason: string }[];
}

export interface Citation {
  label: string;
  amount_minor?: number | null;
  period?: string | null;
  category_id?: number | null;
  transaction_ids: number[];
}

export interface ChatAnswer {
  answer: string;
  degraded: boolean;
  citations: Citation[];
  needs_input?: string | null;
}

export interface ApiError {
  error: { code: string; message: string; details: string[] };
}
