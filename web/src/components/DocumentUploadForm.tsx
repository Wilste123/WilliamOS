"use client";

import Link from "next/link";
import { FormEvent, useRef, useState } from "react";

import {
  applyDocumentSuggestion,
  uploadDocument,
  type DocumentSuggestion,
  type DocumentUploadResult,
} from "@/lib/api";

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
  const [uploadResult, setUploadResult] = useState<DocumentUploadResult | null>(null);
  const [applyingId, setApplyingId] = useState<string | null>(null);

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
    setUploadResult(null);

    try {
      const result = await uploadDocument(file, { assetId, projectId });
      setUploadResult(result);
      const docType = result.intelligence?.doc_type;
      setSuccess(
        `${String(result.filename ?? file.name)}${docType ? ` (${docType})` : ""}`
      );
      if (inputRef.current) inputRef.current.value = "";
      onUploaded?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Opplasting feilet.");
    } finally {
      setUploading(false);
    }
  }

  async function handleSuggestion(suggestion: DocumentSuggestion) {
    if (!uploadResult?.id) return;
    setApplyingId(suggestion.id);
    try {
      await applyDocumentSuggestion(String(uploadResult.id), suggestion.id, suggestion.payload ?? {});
      setSuccess(`Forslag brukt: ${suggestion.label}`);
      setUploadResult(null);
      onUploaded?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kunne ikke bruke forslag.");
    } finally {
      setApplyingId(null);
    }
  }

  const suggestions = uploadResult?.intelligence?.suggestions ?? [];

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
      {success && (
        <div className="space-y-2">
          <p className="text-sm text-emerald-300">Lagret: {success}</p>
          {uploadResult?.id != null && String(uploadResult.id) !== "" && (
            <div className="flex flex-wrap gap-2">
              <Link
                href={`/chat?document_id=${encodeURIComponent(String(uploadResult.id))}&prompt=${encodeURIComponent(`Analyser dokumentet «${String(uploadResult.filename ?? "dokument")}»`)}&send=1`}
                className="rounded-lg bg-accent/15 px-3 py-1.5 text-xs text-accent"
              >
                Chat om dokumentet
              </Link>
            </div>
          )}
        </div>
      )}
      {suggestions.length > 0 && (
        <div className="space-y-2 rounded-xl border border-border/70 bg-zinc-900/40 p-3">
          <p className="text-xs uppercase tracking-wide text-muted">Forslag fra dokumentanalyse</p>
          <p className="text-xs text-muted">Sjekk også Inbox for samme forslag.</p>
          {suggestions.map((suggestion) => (
            <div key={suggestion.id} className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm">{suggestion.message}</p>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={applyingId === suggestion.id}
                  onClick={() => handleSuggestion(suggestion)}
                  className="rounded-lg bg-accent px-3 py-1.5 text-xs text-white disabled:opacity-60"
                >
                  {applyingId === suggestion.id ? "…" : suggestion.label}
                </button>
                <button
                  type="button"
                  onClick={() => setUploadResult(null)}
                  className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted"
                >
                  Ignorer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </form>
  );
}
