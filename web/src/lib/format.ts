export function formatNok(value: unknown): string {
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num) || num === 0) return "—";
  if (num >= 1_000_000) {
    const millions = num / 1_000_000;
    const text = millions.toFixed(1).replace(".", ",");
    return text.endsWith(",0") ? `${text.slice(0, -2)} MNOK` : `${text} MNOK`;
  }
  if (num >= 1_000) return `${Math.round(num / 1_000).toLocaleString("nb-NO")} kNOK`;
  return `${Math.round(num).toLocaleString("nb-NO")} NOK`;
}

export function formatDate(value: unknown): string {
  if (!value) return "";
  const raw = String(value);
  const datePart = raw.includes("T") ? raw.split("T")[0] : raw;
  const [year, month, day] = datePart.split("-");
  if (!year || !month || !day) return raw;
  return `${day}.${month}.${year}`;
}

export function priorityLabel(priority: unknown): string {
  const p = Number(priority) || 2;
  if (p >= 3) return "Høy";
  if (p <= 1) return "Lav";
  return "Middels";
}

export function priorityTone(priority: unknown): string {
  const p = Number(priority) || 2;
  if (p >= 3) return "bg-red-500/15 text-red-300";
  if (p <= 1) return "bg-zinc-500/15 text-zinc-300";
  return "bg-amber-500/15 text-amber-200";
}

export function statusLabel(status: unknown): string {
  const map: Record<string, string> = {
    open: "Åpen",
    in_progress: "Pågår",
    completed: "Fullført",
    active: "Aktiv",
    inactive: "Inaktiv",
    considering_purchase: "Vurderes",
  };
  return map[String(status ?? "")] ?? String(status ?? "—");
}
