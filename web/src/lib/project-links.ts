export const PROJECT_LINK_TYPES = [
  { value: "asset", label: "Eiendel", path: "/assets" },
  { value: "goal", label: "Mål", path: "/goals" },
  { value: "task", label: "Oppgave", path: "/tasks" },
  { value: "document", label: "Dokument", path: "/documents" },
  { value: "finance_account", label: "Finanskonto", path: "/finance" },
  { value: "decision", label: "Beslutning", path: "/decisions" },
] as const;

export type ProjectLinkType = (typeof PROJECT_LINK_TYPES)[number]["value"];

export function projectLinkTypeLabel(type: unknown): string {
  const match = PROJECT_LINK_TYPES.find((item) => item.value === type);
  return match?.label ?? String(type ?? "Kobling");
}

export function entityRecordLabel(record: Record<string, unknown>): string {
  for (const field of ["name", "title", "filename"]) {
    if (record[field]) return String(record[field]);
  }
  return String(record.id ?? "Ukjent");
}
