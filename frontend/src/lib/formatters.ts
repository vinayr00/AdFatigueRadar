/**
 * Reusable formatting utilities.
 * Handles null/undefined and boundary representations gracefully according to spec:
 * - CPA = null -> "—"
 * - Economic risk = null -> "N/A"
 * - Never returns Infinity or NaN
 */

export function formatNumber(val: number | null | undefined, compact = false): string {
  if (val === null || val === undefined || isNaN(val) || !isFinite(val)) {
    return "—";
  }
  if (compact) {
    if (Math.abs(val) >= 1_000_000) {
      return (val / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
    }
    if (Math.abs(val) >= 1_000) {
      return (val / 1_000).toFixed(1).replace(/\.0$/, "") + "K";
    }
  }
  return new Intl.NumberFormat("en-US").format(val);
}

export function formatCurrency(val: number | null | undefined, decimals = 0): string {
  if (val === null || val === undefined || isNaN(val) || !isFinite(val)) {
    return "—";
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: decimals,
  }).format(val);
}

export function formatPercent(val: number | null | undefined, decimals = 1, isRatio = false): string {
  if (val === null || val === undefined || isNaN(val) || !isFinite(val)) {
    return "—";
  }
  const multiplied = isRatio ? val * 100 : val;
  return `${multiplied.toFixed(decimals)}%`;
}

export function formatRiskScore(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val) || !isFinite(val)) {
    return "N/A";
  }
  return val.toFixed(2);
}

export function formatDate(val: string | Date): string {
  try {
    const d = typeof val === "string" ? new Date(val) : val;
    if (isNaN(d.getTime())) return String(val);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "2-digit",
      year: "numeric",
    });
  } catch {
    return String(val);
  }
}

export function formatDateTime(val: string | Date): string {
  try {
    const d = typeof val === "string" ? new Date(val) : val;
    if (isNaN(d.getTime())) return String(val);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return String(val);
  }
}

export function formatTimeOnly(val: string | Date): string {
  try {
    const d = typeof val === "string" ? new Date(val) : val;
    if (isNaN(d.getTime())) return String(val);
    return d.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return String(val);
  }
}
