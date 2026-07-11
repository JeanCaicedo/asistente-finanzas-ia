// Envoltura de fetch a la API del backend. Maneja el formato de error uniforme
// { error: { code, message, details } } y lo convierte en una excepción con mensaje claro.

import type {
  BudgetProgress,
  Category,
  CategoryReport,
  ChatAnswer,
  GoalProgress,
  ImportPreview,
  ImportResult,
  MonthlyPoint,
  Transaction,
  TransactionCreate,
} from "../types";

const BASE = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000";

export class ApiRequestError extends Error {
  code: string;
  details: string[];
  constructor(code: string, message: string, details: string[] = []) {
    super(message);
    this.code = code;
    this.details = details;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : undefined,
      ...options,
    });
  } catch {
    throw new ApiRequestError("network", "No se pudo conectar con el servidor.");
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const err = data?.error;
    throw new ApiRequestError(
      err?.code ?? "error",
      err?.message ?? "Ocurrió un error.",
      err?.details ?? [],
    );
  }
  return data as T;
}

export const api = {
  health: () => request<{ status: string; ai_available: boolean }>("/health"),

  // Transacciones
  listTransactions: (params: { year_month?: string; category_id?: number; type?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.year_month) q.set("year_month", params.year_month);
    if (params.category_id != null) q.set("category_id", String(params.category_id));
    if (params.type) q.set("type", params.type);
    const qs = q.toString();
    return request<Transaction[]>(`/transactions${qs ? `?${qs}` : ""}`);
  },
  createTransaction: (body: TransactionCreate) =>
    request<Transaction>("/transactions", { method: "POST", body: JSON.stringify(body) }),
  updateTransaction: (id: number, body: Partial<TransactionCreate>) =>
    request<Transaction>(`/transactions/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteTransaction: (id: number) =>
    request<void>(`/transactions/${id}`, { method: "DELETE" }),

  // Categorías
  listCategories: () => request<Category[]>("/categories"),
  createCategory: (body: { name: string; kind: string; color?: string | null }) =>
    request<Category>("/categories", { method: "POST", body: JSON.stringify(body) }),
  deleteCategory: (id: number) => request<void>(`/categories/${id}`, { method: "DELETE" }),

  // Reportes
  reportByCategory: (year_month: string) =>
    request<CategoryReport>(`/reports/by-category?year_month=${year_month}`),
  reportMonthly: (months = 6) => request<MonthlyPoint[]>(`/reports/monthly?months=${months}`),

  // Presupuestos
  listBudgets: (year_month: string) =>
    request<BudgetProgress[]>(`/budgets?year_month=${year_month}`),
  createBudget: (body: { category_id: number; year_month: string; limit_minor: number; currency: string }) =>
    request<BudgetProgress>("/budgets", { method: "POST", body: JSON.stringify(body) }),
  deleteBudget: (id: number) => request<void>(`/budgets/${id}`, { method: "DELETE" }),

  // Metas
  listGoals: () => request<GoalProgress[]>("/goals"),
  createGoal: (body: { name: string; target_minor: number; currency: string; target_date?: string | null }) =>
    request<GoalProgress>("/goals", { method: "POST", body: JSON.stringify(body) }),
  addContribution: (goalId: number, body: { amount_minor: number; date: string; note?: string | null }) =>
    request<GoalProgress>(`/goals/${goalId}/contributions`, { method: "POST", body: JSON.stringify(body) }),

  // Importación
  importPreview: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<ImportPreview>("/import/preview", { method: "POST", body: fd });
  },
  importCommit: (rows: TransactionCreate[], skip_duplicates = true) =>
    request<ImportResult>("/import/commit", {
      method: "POST",
      body: JSON.stringify({ rows, skip_duplicates }),
    }),

  // Chat
  chat: (question: string) =>
    request<ChatAnswer>("/chat", { method: "POST", body: JSON.stringify({ question }) }),

  // Admin
  reset: () => request<{ status: string }>("/admin/reset", { method: "POST" }),
  reseed: () => request<{ status: string }>("/admin/reseed", { method: "POST" }),
};
