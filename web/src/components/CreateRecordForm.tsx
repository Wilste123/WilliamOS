"use client";

import { FormEvent, useState } from "react";

import { VisibilitySelect } from "@/components/VisibilitySelect";
import { ApiError, createRecord } from "@/lib/api";
import type { Visibility } from "@/lib/visibility";

export type CreateField = {
  name: string;
  label: string;
  type: "text" | "number" | "date" | "select" | "textarea";
  required?: boolean;
  placeholder?: string;
  step?: string;
  numeric?: boolean;
  options?: { value: string; label: string }[];
};

type CreateRecordFormProps = {
  path: string;
  submitLabel: string;
  fields: CreateField[];
  extraPayload?: Record<string, unknown>;
  showVisibility?: boolean;
  defaultVisibility?: Visibility;
  onCreated?: (record: Record<string, unknown>) => void;
};

export function CreateRecordForm({
  path,
  submitLabel,
  fields,
  extraPayload,
  showVisibility = false,
  defaultVisibility = "household",
  onCreated,
}: CreateRecordFormProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [visibility, setVisibility] = useState<Visibility>(defaultVisibility);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setField(name: string, value: string) {
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const body: Record<string, unknown> = { ...extraPayload };
    if (showVisibility) {
      body.visibility = visibility;
    }

    for (const field of fields) {
      const raw = (values[field.name] ?? "").trim();
      if (!raw) {
        if (field.required) {
          setError(`${field.label} er påkrevd.`);
          return;
        }
        continue;
      }
      if (field.type === "number" || (field.type === "select" && field.numeric)) {
        const num = Number(raw.replace(/\s/g, "").replace(",", "."));
        if (Number.isNaN(num)) {
          setError(`${field.label} må være et tall.`);
          return;
        }
        body[field.name] = num;
      } else {
        body[field.name] = raw;
      }
    }

    setSubmitting(true);
    try {
      const created = await createRecord(path, body);
      setValues({});
      onCreated?.(created);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kunne ikke opprette.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-border p-4">
      {fields.map((field) => (
        <label key={field.name} className="block space-y-1 text-sm">
          <span>{field.label}</span>
          {field.type === "select" ? (
            <select
              required={field.required}
              value={values[field.name] ?? ""}
              onChange={(e) => setField(field.name, e.target.value)}
              className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3"
            >
              <option value="">{field.placeholder ?? "Velg…"}</option>
              {(field.options ?? []).map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : field.type === "textarea" ? (
            <textarea
              required={field.required}
              value={values[field.name] ?? ""}
              onChange={(e) => setField(field.name, e.target.value)}
              placeholder={field.placeholder}
              className="min-h-24 w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3"
            />
          ) : (
            <input
              type={field.type}
              required={field.required}
              value={values[field.name] ?? ""}
              onChange={(e) => setField(field.name, e.target.value)}
              placeholder={field.placeholder}
              step={field.type === "number" ? field.step ?? "1" : undefined}
              min={field.type === "number" ? "0" : undefined}
              className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3"
            />
          )}
        </label>
      ))}
      {showVisibility && <VisibilitySelect value={visibility} onChange={setVisibility} />}
      {error && <p className="text-sm text-red-400">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitLabel}
      </button>
    </form>
  );
}
