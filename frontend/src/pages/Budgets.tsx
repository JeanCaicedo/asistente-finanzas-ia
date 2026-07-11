import { useEffect, useState } from "react";
import { api, ApiRequestError } from "../api/client";
import { BudgetBadge, GoalBadge } from "../components/Badges";
import { Icon } from "../components/Icon";
import { EmptyState, useConfirm, usePrompt, useToast } from "../components/ui";
import { currentYearMonth, formatMoney, formatPercent, toMinor, todayIso } from "../lib/format";
import type { BudgetProgress, Category, GoalProgress } from "../types";

const STATUS_COLOR: Record<string, string> = {
  ok: "var(--income)",
  near: "var(--warn)",
  exceeded: "var(--expense)",
};

export default function Budgets() {
  const [ym, setYm] = useState(currentYearMonth());
  const [budgets, setBudgets] = useState<BudgetProgress[]>([]);
  const [goals, setGoals] = useState<GoalProgress[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState("");
  const toast = useToast();
  const confirm = useConfirm();
  const prompt = usePrompt();

  const [bForm, setBForm] = useState({ category_id: "", limit: "" });
  const [gForm, setGForm] = useState({ name: "", target: "", target_date: "" });

  async function load() {
    const [b, g, c] = await Promise.all([api.listBudgets(ym), api.listGoals(), api.listCategories()]);
    setBudgets(b);
    setGoals(g);
    setCategories(c);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ym]);

  async function createBudget(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const limit_minor = toMinor(bForm.limit);
    if (!bForm.category_id || limit_minor == null) {
      setError("Elige una categoría y un límite válido.");
      return;
    }
    try {
      await api.createBudget({
        category_id: Number(bForm.category_id),
        year_month: ym,
        limit_minor,
        currency: "COP",
      });
      setBForm({ category_id: "", limit: "" });
      toast("Presupuesto definido.", "success");
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "No se pudo crear el presupuesto.");
    }
  }

  async function createGoal(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const target_minor = toMinor(gForm.target);
    if (!gForm.name || target_minor == null) {
      setError("Escribe un nombre y una meta válida.");
      return;
    }
    await api.createGoal({
      name: gForm.name,
      target_minor,
      currency: "COP",
      target_date: gForm.target_date || null,
    });
    setGForm({ name: "", target: "", target_date: "" });
    toast("Meta creada.", "success");
    await load();
  }

  async function contribute(goalId: number, name: string) {
    const raw = await prompt({
      title: `Aporte a "${name}"`,
      label: "Monto del aporte",
      placeholder: "200.000",
      confirmLabel: "Aportar",
    });
    if (raw == null) return;
    const amount_minor = toMinor(raw);
    if (amount_minor == null) {
      toast("Monto inválido.", "error");
      return;
    }
    await api.addContribution(goalId, { amount_minor, date: todayIso(), note: "Aporte manual" });
    toast("Aporte registrado.", "success");
    await load();
  }

  async function deleteBudget(id: number) {
    const ok = await confirm({ title: "Eliminar presupuesto", confirmLabel: "Eliminar", danger: true });
    if (!ok) return;
    await api.deleteBudget(id);
    toast("Presupuesto eliminado.", "info");
    await load();
  }

  const expenseCats = categories.filter((c) => c.kind === "expense" || c.kind === "both");

  return (
    <>
      {/* Presupuestos */}
      <div className="card">
        <div className="card-header">
          <span className="card-icon">
            <Icon name="wallet" size={17} />
          </span>
          <h2>Presupuestos mensuales</h2>
          <div className="header-note" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span>Mes</span>
            <input
              value={ym}
              onChange={(e) => setYm(e.target.value)}
              placeholder="2026-07"
              style={{ width: 110 }}
            />
          </div>
        </div>

        <form onSubmit={createBudget} className="form-grid">
          <div className="field">
            <label>Categoría</label>
            <select value={bForm.category_id} onChange={(e) => setBForm({ ...bForm, category_id: e.target.value })}>
              <option value="">Elige…</option>
              {expenseCats.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Límite mensual</label>
            <input value={bForm.limit} onChange={(e) => setBForm({ ...bForm, limit: e.target.value })} placeholder="400.000" inputMode="decimal" />
          </div>
          <div className="field" style={{ flex: "0 0 auto" }}>
            <button className="btn primary" type="submit">
              <Icon name="plus" size={16} /> Definir
            </button>
          </div>
        </form>
        {error && (
          <div className="error-msg">
            <Icon name="alert" size={15} /> {error}
          </div>
        )}

        {budgets.length === 0 ? (
          <div style={{ marginTop: 8 }}>
            <EmptyState icon="wallet" title={`No hay presupuestos para ${ym}`} hint="Define un límite por categoría para recibir alertas al acercarte o excederlo." />
          </div>
        ) : (
          <div className="grid grid-2" style={{ marginTop: 18 }}>
            {budgets.map((b) => (
              <div key={b.id} className="tile">
                <div className="row-between">
                  <strong>{b.category_name}</strong>
                  <BudgetBadge status={b.status} />
                </div>
                <div className="progress" style={{ margin: "12px 0 8px" }}>
                  <span
                    style={{
                      width: `${Math.min(100, Math.round(b.percent * 100))}%`,
                      background: STATUS_COLOR[b.status],
                    }}
                  />
                </div>
                <div className="hint">
                  {formatMoney(b.spent_minor, b.currency)} de {formatMoney(b.limit_minor, b.currency)} ·{" "}
                  {formatPercent(b.percent)}
                  {b.status === "exceeded" && (
                    <span style={{ color: "var(--expense)" }}>
                      {" "}· excedido por {formatMoney(b.over_by_minor, b.currency)}
                    </span>
                  )}
                </div>
                <button className="link-btn danger" style={{ marginTop: 10 }} onClick={() => deleteBudget(b.id)}>
                  <Icon name="trash" size={14} /> Eliminar
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Metas */}
      <div className="card">
        <div className="card-header">
          <span className="card-icon">
            <Icon name="target" size={17} />
          </span>
          <h2>Metas de ahorro</h2>
        </div>
        <form onSubmit={createGoal} className="form-grid">
          <div className="field">
            <label>Nombre</label>
            <input value={gForm.name} onChange={(e) => setGForm({ ...gForm, name: e.target.value })} placeholder="Fondo de emergencia" />
          </div>
          <div className="field">
            <label>Meta</label>
            <input value={gForm.target} onChange={(e) => setGForm({ ...gForm, target: e.target.value })} placeholder="2.000.000" inputMode="decimal" />
          </div>
          <div className="field">
            <label>Fecha objetivo (opcional)</label>
            <input type="date" value={gForm.target_date} onChange={(e) => setGForm({ ...gForm, target_date: e.target.value })} />
          </div>
          <div className="field" style={{ flex: "0 0 auto" }}>
            <button className="btn primary" type="submit">
              <Icon name="plus" size={16} /> Crear meta
            </button>
          </div>
        </form>

        {goals.length === 0 ? (
          <div style={{ marginTop: 8 }}>
            <EmptyState icon="target" title="Aún no tienes metas" hint="Crea una meta y registra aportes manuales para seguir tu progreso." />
          </div>
        ) : (
          <div className="grid grid-2" style={{ marginTop: 18 }}>
            {goals.map((g) => (
              <div key={g.id} className="tile">
                <div className="row-between">
                  <strong>{g.name}</strong>
                  <GoalBadge status={g.status} />
                </div>
                <div className="progress" style={{ margin: "12px 0 8px" }}>
                  <span style={{ width: `${Math.min(100, Math.round(g.percent * 100))}%`, background: "var(--income)" }} />
                </div>
                <div className="hint">
                  {formatMoney(g.saved_minor, g.currency)} de {formatMoney(g.target_minor, g.currency)} ·{" "}
                  {formatPercent(g.percent)}
                  {g.target_date && <> · meta {g.target_date}</>}
                </div>
                <button className="btn secondary sm" style={{ marginTop: 12 }} onClick={() => contribute(g.id, g.name)}>
                  <Icon name="coins" size={15} /> Aporte manual
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
