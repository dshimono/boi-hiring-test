export function formatWeek(dateStr: string): string {
  return new Date(`${dateStr}T00:00:00Z`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

export function formatYear(dateStr: string): number {
  return new Date(`${dateStr}T00:00:00Z`).getUTCFullYear();
}

export function formatCompact(n: number): string {
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n);
}

export function formatNumber(n: number): string {
  return n.toLocaleString("en-US");
}
