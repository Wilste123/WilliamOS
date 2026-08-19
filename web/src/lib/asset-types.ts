export const ASSET_TYPES = [
  { value: "vehicle", label: "Bil" },
  { value: "boat", label: "Båt" },
  { value: "property", label: "Bolig" },
  { value: "cabin", label: "Hytte" },
  { value: "other", label: "Annet" },
] as const;

export type AssetTypeValue = (typeof ASSET_TYPES)[number]["value"];

export function assetTypeLabel(value: unknown): string {
  const match = ASSET_TYPES.find((item) => item.value === value);
  if (match) return match.label;
  return value ? String(value) : "—";
}

export const ASSET_TYPE_OPTIONS = ASSET_TYPES.map(({ value, label }) => ({ value, label }));
