"use client";

import { VISIBILITY_OPTIONS, type Visibility } from "@/lib/visibility";

type VisibilitySelectProps = {
  value: Visibility;
  onChange: (value: Visibility) => void;
};

export function VisibilitySelect({ value, onChange }: VisibilitySelectProps) {
  return (
    <label className="block space-y-1 text-sm">
      <span>Synlighet</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as Visibility)}
        className="w-full rounded-xl border border-border bg-transparent px-4 py-3"
      >
        {VISIBILITY_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
