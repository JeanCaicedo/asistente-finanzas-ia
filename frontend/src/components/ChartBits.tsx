// Piezas compartidas para los gráficos de Recharts: paleta categórica coherente,
// colores de ejes/rejilla según el tema, y un tooltip estilizado con el formato de dinero.

import { formatMoney } from "../lib/format";
import { useTheme } from "./ui";

// Paleta categórica que funciona en claro y oscuro (para el gráfico de torta).
export const CHART_COLORS = [
  "#6366f1",
  "#34d399",
  "#f59e0b",
  "#fb7185",
  "#22d3ee",
  "#a78bfa",
  "#f472b6",
  "#60a5fa",
  "#4ade80",
  "#fbbf24",
];

export function useChartTheme() {
  const { theme } = useTheme();
  const dark = theme === "dark";
  return {
    axis: dark ? "#93a3bd" : "#64748b",
    grid: dark ? "rgba(148,163,184,0.14)" : "rgba(100,116,139,0.16)",
    income: dark ? "#34d399" : "#059669",
    expense: dark ? "#fb7185" : "#e11d48",
    net: dark ? "#818cf8" : "#6366f1",
  };
}

interface TooltipEntry {
  name?: string;
  value?: number;
  color?: string;
  payload?: Record<string, unknown>;
}

export function MoneyTooltip({
  active,
  payload,
  label,
  currency = "COP",
}: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string;
  currency?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      {label != null && <div className="tt-label">{label}</div>}
      {payload.map((e, i) => (
        <div className="tt-row" key={i}>
          <span className="tt-dot" style={{ background: e.color }} />
          {e.name && <span className="muted">{e.name}:</span>}
          <strong>{formatMoney(Number(e.value ?? 0), currency)}</strong>
        </div>
      ))}
    </div>
  );
}
