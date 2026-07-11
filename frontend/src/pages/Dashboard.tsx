import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import { Icon } from "../components/Icon";
import { CHART_COLORS, MoneyTooltip, useChartTheme } from "../components/ChartBits";
import { EmptyState, Skeleton } from "../components/ui";
import { currentYearMonth, formatMoney } from "../lib/format";
import type { CategoryReport, MonthlyPoint, Transaction } from "../types";

export default function Dashboard() {
  const [ym] = useState(currentYearMonth());
  const [report, setReport] = useState<CategoryReport | null>(null);
  const [monthly, setMonthly] = useState<MonthlyPoint[]>([]);
  const [drill, setDrill] = useState<{ name: string; txs: Transaction[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const ct = useChartTheme();

  useEffect(() => {
    Promise.all([api.reportByCategory(ym), api.reportMonthly(6)])
      .then(([r, m]) => {
        setReport(r);
        setMonthly(m);
      })
      .finally(() => setLoading(false));
  }, [ym]);

  async function openDrill(name: string, ids: number[]) {
    // Trazabilidad (FR-016): mostrar las transacciones que componen la cifra.
    const all = await api.listTransactions({ year_month: ym, type: "expense" });
    setDrill({ name, txs: all.filter((t) => ids.includes(t.id)) });
  }

  const totals = monthly.find((m) => m.year_month === ym);
  const pieData = (report?.items ?? []).map((i) => ({
    name: i.category_name,
    value: i.amount_minor,
    ids: i.transaction_ids,
  }));
  const currency = report?.currency ?? "COP";
  const tickMoney = (v: number) => `${Math.round(v / 100000)}`;

  if (loading) return <DashboardSkeleton />;

  return (
    <>
      <div className="grid grid-3">
        <StatCard
          icon="up"
          tone="income"
          label={`Ingresos del mes · ${ym}`}
          value={formatMoney(totals?.income_minor ?? 0, currency)}
        />
        <StatCard
          icon="down"
          tone="expense"
          label="Gastos del mes"
          value={formatMoney(totals?.expense_minor ?? 0, currency)}
        />
        <StatCard
          icon="wallet"
          tone="net"
          label="Neto del mes"
          value={formatMoney(totals?.net_minor ?? 0, currency)}
        />
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <span className="card-icon">
              <Icon name="budgets" size={17} />
            </span>
            <h2>Gasto por categoría</h2>
            {report && (
              <span className="header-note">
                Total {formatMoney(report.total_minor, currency)}
              </span>
            )}
          </div>
          {pieData.length === 0 ? (
            <EmptyState icon="budgets" title="Sin gastos este mes" hint="Registra o importa movimientos para ver el desglose." />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={62}
                    outerRadius={100}
                    paddingAngle={2}
                    stroke="none"
                    onClick={(e: any) => openDrill(e.name, e.ids)}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} cursor="pointer" />
                    ))}
                  </Pie>
                  <Tooltip content={<MoneyTooltip currency={currency} />} />
                  <Legend
                    iconType="circle"
                    wrapperStyle={{ fontSize: 12.5, color: ct.axis }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <p className="hint" style={{ marginTop: 4 }}>
                La suma de categorías cuadra con el total. Haz clic en una porción para ver sus
                transacciones.
              </p>
            </>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-icon">
              <Icon name="transactions" size={17} />
            </span>
            <h2>Ingresos vs gastos</h2>
            <span className="header-note">Últimos 6 meses</span>
          </div>
          {monthly.length === 0 ? (
            <EmptyState icon="transactions" title="Sin datos suficientes" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={monthly} barGap={6}>
                <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} vertical={false} />
                <XAxis dataKey="year_month" stroke={ct.axis} fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke={ct.axis} fontSize={12} tickLine={false} axisLine={false} tickFormatter={tickMoney} />
                <Tooltip cursor={{ fill: ct.grid }} content={<MoneyTooltip currency={currency} />} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12.5 }} />
                <Bar dataKey="income_minor" name="Ingresos" fill={ct.income} radius={[6, 6, 0, 0]} maxBarSize={34} />
                <Bar dataKey="expense_minor" name="Gastos" fill={ct.expense} radius={[6, 6, 0, 0]} maxBarSize={34} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-icon">
            <Icon name="up" size={17} />
          </span>
          <h2>Tendencia del saldo neto</h2>
          <span className="header-note">En miles (÷100.000)</span>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={monthly}>
            <defs>
              <linearGradient id="netFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={ct.net} stopOpacity={0.35} />
                <stop offset="100%" stopColor={ct.net} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} vertical={false} />
            <XAxis dataKey="year_month" stroke={ct.axis} fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke={ct.axis} fontSize={12} tickLine={false} axisLine={false} tickFormatter={tickMoney} />
            <Tooltip content={<MoneyTooltip currency={currency} />} />
            <Area
              type="monotone"
              dataKey="net_minor"
              name="Neto"
              stroke={ct.net}
              strokeWidth={2.5}
              fill="url(#netFill)"
              dot={{ r: 3, fill: ct.net, strokeWidth: 0 }}
              activeDot={{ r: 5 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {drill && (
        <div className="card">
          <div className="card-header">
            <span className="card-icon">
              <Icon name="search" size={17} />
            </span>
            <h2>Transacciones de {drill.name}</h2>
            <button className="link-btn" style={{ marginLeft: "auto" }} onClick={() => setDrill(null)}>
              <Icon name="close" size={15} /> Cerrar
            </button>
          </div>
          {drill.txs.length === 0 ? (
            <EmptyState icon="search" title="Sin transacciones para mostrar" />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Descripción</th>
                    <th className="num">Monto</th>
                  </tr>
                </thead>
                <tbody>
                  {drill.txs.map((t) => (
                    <tr key={t.id}>
                      <td>{t.date}</td>
                      <td>{t.description || <span className="faint">—</span>}</td>
                      <td className="num amount expense">{formatMoney(t.amount_minor, t.currency)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </>
  );
}

function StatCard({
  icon,
  tone,
  label,
  value,
}: {
  icon: "up" | "down" | "wallet";
  tone: "income" | "expense" | "net";
  label: string;
  value: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span className={`stat-ico ${tone}`}>
          <Icon name={icon} size={18} />
        </span>
        <span className="stat-label">{label}</span>
      </div>
      <div className={`stat-value ${tone === "income" ? "income" : tone === "expense" ? "expense" : ""}`}>
        {value}
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <>
      <div className="grid grid-3">
        {[0, 1, 2].map((i) => (
          <div className="stat-card" key={i}>
            <div className="stat-top">
              <Skeleton width={34} height={34} radius={10} />
              <Skeleton width={120} height={12} />
            </div>
            <Skeleton width={140} height={26} />
          </div>
        ))}
      </div>
      <div className="grid grid-2">
        {[0, 1].map((i) => (
          <div className="card" key={i}>
            <Skeleton width={180} height={16} style={{ marginBottom: 18 }} />
            <Skeleton height={260} radius={12} />
          </div>
        ))}
      </div>
      <div className="card">
        <Skeleton width={180} height={16} style={{ marginBottom: 18 }} />
        <Skeleton height={220} radius={12} />
      </div>
    </>
  );
}
