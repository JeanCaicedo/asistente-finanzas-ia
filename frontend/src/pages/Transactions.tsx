import { useEffect, useState } from "react";
import { api, ApiRequestError } from "../api/client";
import { CategoryBadge } from "../components/Badges";
import { Icon } from "../components/Icon";
import { EmptyState, Skeleton, useConfirm, useToast } from "../components/ui";
import { currentYearMonth, formatMoney, toMinor, todayIso } from "../lib/format";
import type { Category, Transaction } from "../types";

export default function Transactions() {
  const [txs, setTxs] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [ym, setYm] = useState(currentYearMonth());
  const [typeFilter, setTypeFilter] = useState("");
  const [catFilter, setCatFilter] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const toast = useToast();
  const confirm = useConfirm();

  // Formulario de alta
  const [form, setForm] = useState({ type: "expense", amount: "", date: todayIso(), description: "", category_id: "" });

  async function load() {
    setLoading(true);
    try {
      const [t, c] = await Promise.all([
        api.listTransactions({
          year_month: ym,
          type: typeFilter || undefined,
          category_id: catFilter ? Number(catFilter) : undefined,
        }),
        api.listCategories(),
      ]);
      setTxs(t);
      setCategories(c);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ym, typeFilter, catFilter]);

  async function createTx(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const amount_minor = toMinor(form.amount);
    if (amount_minor == null) {
      setError("El monto debe ser un número mayor que cero.");
      return;
    }
    setSaving(true);
    try {
      await api.createTransaction({
        type: form.type as "income" | "expense",
        amount_minor,
        currency: "COP",
        date: form.date,
        description: form.description || null,
        category_id: form.category_id ? Number(form.category_id) : null,
      });
      setForm({ type: "expense", amount: "", date: todayIso(), description: "", category_id: "" });
      toast("Transacción agregada.", "success");
      await load();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "No se pudo crear la transacción.");
    } finally {
      setSaving(false);
    }
  }

  async function changeCategory(tx: Transaction, categoryId: string) {
    await api.updateTransaction(tx.id, { category_id: categoryId ? Number(categoryId) : null });
    toast("Categoría actualizada.", "success");
    await load();
  }

  async function remove(id: number) {
    const ok = await confirm({
      title: "Eliminar transacción",
      message: "Esta acción no se puede deshacer.",
      confirmLabel: "Eliminar",
      danger: true,
    });
    if (!ok) return;
    await api.deleteTransaction(id);
    toast("Transacción eliminada.", "success");
    await load();
  }

  async function doReset() {
    const ok = await confirm({
      title: "Empezar de cero",
      message: "Se borrarán TODOS tus datos (transacciones, presupuestos y metas). ¿Continuar?",
      confirmLabel: "Borrar todo",
      danger: true,
    });
    if (!ok) return;
    await api.reset();
    toast("Datos borrados.", "info");
    await load();
  }

  async function doReseed() {
    const ok = await confirm({
      title: "Recargar datos de ejemplo",
      message: "Se reemplazarán los datos actuales por ~3 meses de ejemplo. ¿Continuar?",
      confirmLabel: "Recargar",
    });
    if (!ok) return;
    await api.reseed();
    toast("Datos de ejemplo recargados.", "success");
    await load();
  }

  return (
    <>
      {/* Alta */}
      <div className="card">
        <div className="card-header">
          <span className="card-icon">
            <Icon name="plus" size={17} />
          </span>
          <h2>Nueva transacción</h2>
        </div>
        <form onSubmit={createTx}>
          <div className="form-grid">
            <div className="field">
              <label>Tipo</label>
              <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                <option value="expense">Gasto</option>
                <option value="income">Ingreso</option>
              </select>
            </div>
            <div className="field">
              <label>Monto</label>
              <input value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="50.000" inputMode="decimal" />
            </div>
            <div className="field">
              <label>Fecha</label>
              <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
            </div>
            <div className="field">
              <label>Categoría</label>
              <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
                <option value="">Automática (IA)</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="field" style={{ marginTop: 14 }}>
            <label>Descripción</label>
            <input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Ej: Pago Rappi restaurante"
            />
          </div>
          {error && (
            <div className="error-msg">
              <Icon name="alert" size={15} /> {error}
            </div>
          )}
          <button className="btn primary" type="submit" disabled={saving} style={{ marginTop: 16 }}>
            <Icon name="plus" size={16} /> {saving ? "Agregando…" : "Agregar transacción"}
          </button>
        </form>
      </div>

      {/* Lista + filtros */}
      <div className="card">
        <div className="card-header">
          <span className="card-icon">
            <Icon name="transactions" size={17} />
          </span>
          <h2>Movimientos</h2>
          <span className="header-note">{loading ? "cargando…" : `${txs.length} resultado(s)`}</span>
        </div>

        <div className="form-grid" style={{ marginBottom: 18 }}>
          <div className="field">
            <label>Mes</label>
            <input value={ym} onChange={(e) => setYm(e.target.value)} placeholder="2026-07" />
          </div>
          <div className="field">
            <label>Tipo</label>
            <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
              <option value="">Todos</option>
              <option value="expense">Gastos</option>
              <option value="income">Ingresos</option>
            </select>
          </div>
          <div className="field">
            <label>Categoría</label>
            <select value={catFilter} onChange={(e) => setCatFilter(e.target.value)}>
              <option value="">Todas</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field" style={{ display: "flex", gap: 8, flex: "0 0 auto" }}>
            <button className="btn secondary" onClick={doReseed}>
              <Icon name="reload" size={15} /> Recargar ejemplo
            </button>
            <button className="btn danger" onClick={doReset}>
              <Icon name="reset" size={15} /> Empezar de cero
            </button>
          </div>
        </div>

        {loading ? (
          <div className="stack">
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} height={44} radius={10} />
            ))}
          </div>
        ) : txs.length === 0 ? (
          <EmptyState icon="transactions" title="No hay transacciones para este filtro" hint="Prueba con otro mes o agrega una transacción arriba." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Descripción</th>
                  <th>Categoría</th>
                  <th className="num">Monto</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {txs.map((t) => (
                  <tr key={t.id}>
                    <td className="num" style={{ textAlign: "left" }}>{t.date}</td>
                    <td>
                      <span className={`badge ${t.type === "income" ? "ok" : "exceeded"}`}>
                        {t.type === "income" ? "Ingreso" : "Gasto"}
                      </span>
                    </td>
                    <td>{t.description || <span className="faint">—</span>}</td>
                    <td>
                      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        <select
                          value={t.category_id ?? ""}
                          onChange={(e) => changeCategory(t, e.target.value)}
                          style={{ maxWidth: 180 }}
                        >
                          <option value="">Sin categorizar</option>
                          {categories.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.name}
                            </option>
                          ))}
                        </select>
                        <CategoryBadge status={t.category_status} confidence={t.ai_confidence} />
                      </div>
                    </td>
                    <td className={`num amount ${t.type}`}>
                      {t.type === "income" ? "+" : "−"}
                      {formatMoney(t.amount_minor, t.currency)}
                    </td>
                    <td className="num">
                      <button className="icon-btn" style={{ width: 32, height: 32 }} onClick={() => remove(t.id)} title="Borrar" aria-label="Borrar">
                        <Icon name="trash" size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <CategoryManager categories={categories} onChange={load} />
    </>
  );
}

function CategoryManager({ categories, onChange }: { categories: Category[]; onChange: () => void }) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState("expense");
  const [error, setError] = useState("");
  const toast = useToast();

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.createCategory({ name, kind });
      setName("");
      toast("Categoría creada.", "success");
      onChange();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "No se pudo crear.");
    }
  }

  async function remove(id: number) {
    setError("");
    try {
      await api.deleteCategory(id);
      toast("Categoría eliminada.", "info");
      onChange();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "No se pudo borrar.");
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-icon">
          <Icon name="budgets" size={17} />
        </span>
        <h2>Categorías</h2>
      </div>
      <form onSubmit={create} className="form-grid">
        <div className="field">
          <label>Nueva categoría</label>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ej: Mascotas" required />
        </div>
        <div className="field">
          <label>Tipo</label>
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="expense">Gasto</option>
            <option value="income">Ingreso</option>
            <option value="both">Ambos</option>
          </select>
        </div>
        <div className="field" style={{ flex: "0 0 auto" }}>
          <button className="btn primary" type="submit">
            <Icon name="plus" size={16} /> Crear
          </button>
        </div>
      </form>
      {error && (
        <div className="error-msg">
          <Icon name="alert" size={15} /> {error}
        </div>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 9, marginTop: 16 }}>
        {categories.map((c) => (
          <span key={c.id} className="chip">
            {c.name}
            {c.is_system ? (
              <span className="sys">sistema</span>
            ) : (
              <button onClick={() => remove(c.id)} title="Borrar" aria-label="Borrar categoría">
                <Icon name="close" size={14} />
              </button>
            )}
          </span>
        ))}
      </div>
    </div>
  );
}
