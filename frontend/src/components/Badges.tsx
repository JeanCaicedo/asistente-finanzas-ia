import type { BudgetStatus, CategoryStatus, GoalStatus } from "../types";

const CATEGORY_LABELS: Record<CategoryStatus, string> = {
  ai_suggested: "Sugerida por IA",
  user_confirmed: "Confirmada",
  uncategorized: "Sin categorizar",
};

const BUDGET_LABELS: Record<BudgetStatus, string> = {
  ok: "En rango",
  near: "Cerca del límite",
  exceeded: "Excedido",
};

const GOAL_LABELS: Record<GoalStatus, string> = {
  in_progress: "En progreso",
  reached: "Alcanzada",
  overdue: "Vencida",
};

export function CategoryBadge({ status, confidence }: { status: CategoryStatus; confidence?: number | null }) {
  return (
    <span className={`badge ${status}`}>
      {CATEGORY_LABELS[status]}
      {status === "ai_suggested" && confidence != null ? ` · ${Math.round(confidence * 100)}%` : ""}
    </span>
  );
}

export function BudgetBadge({ status }: { status: BudgetStatus }) {
  return <span className={`badge ${status}`}>{BUDGET_LABELS[status]}</span>;
}

export function GoalBadge({ status }: { status: GoalStatus }) {
  return <span className={`badge ${status}`}>{GOAL_LABELS[status]}</span>;
}
