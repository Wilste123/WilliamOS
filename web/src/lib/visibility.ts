export const VISIBILITY_OPTIONS = [
  { value: "household", label: "Delt med husholdning" },
  { value: "private", label: "Privat" },
] as const;

export type Visibility = (typeof VISIBILITY_OPTIONS)[number]["value"];

export function visibilityLabel(value: unknown): string {
  const match = VISIBILITY_OPTIONS.find((item) => item.value === value);
  return match?.label ?? "Delt med husholdning";
}
