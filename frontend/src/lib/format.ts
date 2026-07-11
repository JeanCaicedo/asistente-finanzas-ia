// SOLO formato de presentación (céntimos → display). NUNCA hace sumas ni aritmética
// de negocio: todo cálculo de dinero vive en el backend.

const MINOR_UNITS: Record<string, number> = {
  COP: 2,
  USD: 2,
  EUR: 2,
  CLP: 0,
  JPY: 0,
};

export function formatMoney(amountMinor: number, currency = "COP"): string {
  const exp = MINOR_UNITS[currency] ?? 2;
  const negative = amountMinor < 0;
  const n = Math.abs(amountMinor);
  const factor = 10 ** exp;
  const major = Math.trunc(n / factor);
  const body =
    exp === 0
      ? major.toLocaleString("es-CO")
      : `${major.toLocaleString("es-CO")},${String(n % factor).padStart(exp, "0")}`;
  return `${negative ? "-" : ""}${body} ${currency}`;
}

export function formatPercent(ratio: number): string {
  return `${Math.round(ratio * 100)}%`;
}

// Convierte texto del usuario (mostrado) a unidades menores para enviar al backend.
// El backend re-valida; esto es solo una conversión de conveniencia.
export function toMinor(text: string, currency = "COP"): number | null {
  const exp = MINOR_UNITS[currency] ?? 2;
  const cleaned = text.replace(/[^\d.,-]/g, "").trim();
  if (!cleaned) return null;
  let normalized = cleaned;
  const hasDot = cleaned.includes(".");
  const hasComma = cleaned.includes(",");
  if (hasDot && hasComma) {
    normalized =
      cleaned.lastIndexOf(",") > cleaned.lastIndexOf(".")
        ? cleaned.replace(/\./g, "").replace(",", ".")
        : cleaned.replace(/,/g, "");
  } else if (hasComma) {
    const parts = cleaned.split(",");
    normalized =
      parts.length === 2 && parts[1].length <= 2
        ? cleaned.replace(",", ".")
        : cleaned.replace(/,/g, "");
  } else if (hasDot) {
    const parts = cleaned.split(".");
    normalized = parts.length === 2 && parts[1].length <= 2 ? cleaned : cleaned.replace(/\./g, "");
  }
  const value = Number(normalized);
  if (!isFinite(value) || value <= 0) return null;
  return Math.round(value * 10 ** exp);
}

export function currentYearMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function todayIso(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(
    now.getDate(),
  ).padStart(2, "0")}`;
}
