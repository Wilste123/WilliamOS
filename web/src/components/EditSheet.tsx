"use client";

import { FormEvent, useEffect, useState } from "react";

type EditField = {
  name: string;
  label: string;
  type: "text" | "number" | "date" | "select";
  options?: { value: string; label: string }[];
};

type EditSheetProps = {
  open: boolean;
  title: string;
  fields: EditField[];
  initialValues: Record<string, unknown>;
  submitLabel?: string;
  onClose: () => void;
  onSubmit: (values: Record<string, unknown>) => Promise<void>;
};

export function EditSheet({
  open,
  title,
  fields,
  initialValues,
  submitLabel = "Lagre",
  onClose,
  onSubmit,
}: EditSheetProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const next: Record<string, string> = {};
    for (const field of fields) {
      const raw = initialValues[field.name];
      if (raw === null || raw === undefined) {
        next[field.name] = "";
      } else if (field.type === "date" && typeof raw === "string") {
        next[field.name] = raw.includes("T") ? raw.split("T")[0] : raw;
      } else {
        next[field.name] = String(raw);
      }
    }
    setValues(next);
    setError(null);
  }, [open, fields, initialValues]);

  if (!open) return null;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    const body: Record<string, unknown> = {};
    for (const field of fields) {
      const raw = (values[field.name] ?? "").trim();
      if (!raw && field.type !== "number") continue;
      if (field.type === "number") {
        const num = Number(raw.replace(/\s/g, "").replace(",", "."));
        body[field.name] = Number.isNaN(num) ? null : num;
      } else {
        body[field.name] = raw;
      }
    }
    try {
      await onSubmit(body);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kunne ikke lagre.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <button
        type="button"
        aria-label="Lukk"
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
      />
      <form
        onSubmit={handleSubmit}
        className="relative z-10 w-full max-w-lg rounded-t-3xl border border-border bg-background p-5 sm:rounded-3xl"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button type="button" onClick={onClose} className="text-sm text-muted">
            Lukk
          </button>
        </div>
        <div className="space-y-3">
          {fields.map((field) => (
            <label key={field.name} className="block space-y-1 text-sm">
              <span>{field.label}</span>
              {field.type === "select" ? (
                <select
                  value={values[field.name] ?? ""}
                  onChange={(e) => setValues((prev) => ({ ...prev, [field.name]: e.target.value }))}
                  className="w-full rounded-xl border border-border bg-transparent px-4 py-3"
                >
                  {(field.options ?? []).map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.type}
                  value={values[field.name] ?? ""}
                  onChange={(e) => setValues((prev) => ({ ...prev, [field.name]: e.target.value }))}
                  step={field.type === "number" ? "1000" : undefined}
                  min={field.type === "number" ? "0" : undefined}
                  className="w-full rounded-xl border border-border bg-transparent px-4 py-3"
                />
              )}
            </label>
          ))}
        </div>
        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={saving}
          className="mt-4 w-full rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          {saving ? "Lagrer…" : submitLabel}
        </button>
      </form>
    </div>
  );
}
