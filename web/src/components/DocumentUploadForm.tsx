"use client";

import { FormEvent, useRef, useState } from "react";

import { uploadDocument } from "@/lib/api";

type DocumentUploadFormProps = {
  assetId?: string;
  projectId?: string;
  onUploaded?: () => void;
};

export function DocumentUploadForm({ assetId, projectId, onUploaded }: DocumentUploadFormProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const file = inputRef.current?.files?.[0];
    if (!file) {
      setError("Velg en fil først.");
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await uploadDocument(file, { assetId, projectId });
      setSuccess(String(result.filename ?? file.name));
      if (inputRef.current) inputRef.current.value = "";
      onUploaded?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Opplasting feilet.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-border p-4">
      <label className="block space-y-1 text-sm">
        <span>Last opp PDF, bilde eller fil</span>
        <input
          ref={inputRef}
          type="file"
          className="w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-accent file:px-3 file:py-2 file:text-white"
        />
      </label>
      <button
        type="submit"
        disabled={uploading}
        className="rounded-xl bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
      >
        {uploading ? "Laster opp…" : "Lagre dokument"}
      </button>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {success && <p className="text-sm text-emerald-300">Lagret: {success}</p>}
    </form>
  );
}
