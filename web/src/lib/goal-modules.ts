export const GOAL_MODULES = [
  { value: "general", label: "Generelt" },
  { value: "health", label: "Helse" },
  { value: "finance", label: "Økonomi" },
  { value: "asset", label: "Eiendel" },
  { value: "project", label: "Prosjekt" },
] as const;

export type GoalModule = (typeof GOAL_MODULES)[number]["value"];

export const MODULE_LINK_COLLECTIONS: Partial<Record<GoalModule, string>> = {
  finance: "/finance",
  asset: "/assets",
  project: "/projects",
};

export function goalModuleLabel(module: unknown): string {
  const match = GOAL_MODULES.find((item) => item.value === module);
  return match?.label ?? (module ? String(module) : "Generelt");
}

export function goalModuleNeedsLink(module: unknown): boolean {
  return module === "finance" || module === "asset" || module === "project";
}
