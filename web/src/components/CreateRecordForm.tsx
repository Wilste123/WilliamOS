"use client";

import { FormEvent, useState } from "react";

import { ApiError, createRecord } from "@/lib/api";

export type CreateField = {
  name: string;
  label: string;
  type: "text" | "number" | "date";
  required?: boolean;
  placeholder?: string;
  step?: string;
};

type CreateRecordFormProps = {
  path: string;
  submitLabel: string;
  fields: CreateField[];
  extraPayload?: Record<string, unknown>;
  onCreated?: (record: Record<string, unknown>) => void;
};

export function CreateRecordForm({
  path,
  submitLabel,
  fields,
  extraPayload,
  onCreated,
}: CreateRecordFormProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setField(name: string, value: string) {
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const body: Record<string, unknown> = { ...extraPayload };
    for (const field of fields) {
      const raw = (values[field.name] ?? "").trim();
      if (!raw) {
        if (field.required) {
          setError(`${field.label} er påkrevd.`);
          return;
        }
        continue;
      }
      if (field.type === "number") {
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
          <input
            type={field.type}
            required={field.required}
            value={values[field.name] ?? ""}
            onChange={(e) => setField(field.name, e.target.value)}
            placeholder={field.placeholder}
            step={field.type === "number" ? field.step ?? "1" : undefined}
            min={field.type === "number" ? "0" : undefined}
            className="w-full rounded-xl border border-border bg-transparent px-4 py-3"
          />
        </label>
      ))}
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
