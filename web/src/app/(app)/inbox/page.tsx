"use client";

import { FormEvent, useEffect, useState } from "react";

import { applyInboxSuggestion, captureInbox, dismissInboxItem, fetchInbox } from "@/lib/api";

const OBJECT_LABELS: Record<string, string> = {
  asset: "Eiendel",
  task: "Oppgave",
  decision: "Beslutning",
  project: "Prosjekt",
  document: "Dokument",
  gmail_attachment: "PDF fra e-post",
};

function suggestionLabel(suggestion: Record<string, unknown>): string {
  const objectType = String(suggestion.object_type ?? "unknown");
  const fields = (suggestion.fields as Record<string, unknown>) ?? {};

  if (objectType === "document") {
    return String(fields.message ?? fields.label ?? "Dokumentforslag");
  }

  if (objectType === "gmail_attachment") {
    return `Importer PDF: ${fields.filename ?? "vedlegg"}`;
  }

  const name = fields.name ?? fields.title ?? objectType;
  return `${OBJECT_LABELS[objectType] ?? objectType}: ${name}`;
}

function suggestionActionLabel(suggestion: Record<string, unknown>): string {
  const objectType = String(suggestion.object_type ?? "unknown");
  if (objectType === "document") {
    const fields = (suggestion.fields as Record<string, unknown>) ?? {};
    return String(fields.label ?? "Godta");
  }
  if (objectType === "gmail_attachment") {
    return "Importer";
  }
  return "Opprett";
}

type InboxItem = Record<string, unknown> & {
  id: string;
  text?: string;
  status?: string;
  signal_type?: string;
  doc_type?: string;
  suggestions?: Record<string, unknown>[];
};

export default function InboxPage() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [applyingKey, setApplyingKey] = useState<string | null>(null);
  const [dismissingId, setDismissingId] = useState<string | null>(null);

  async function load() {
    const data = await fetchInbox();
    setItems(data as InboxItem[]);
  }

  useEffect(() => {
    load().catch(() => setItems([]));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    try {
      await captureInbox(text.trim());
      setText("");
      await load();
    } catch {
      setItems((current) => current);
    } finally {
      setLoading(false);
    }
  }

  async function handleApply(itemId: string, index: number) {
    const key = `${itemId}:${index}`;
    setApplyingKey(key);
    try {
      await applyInboxSuggestion(itemId, index);
      await load();
    } finally {
      setApplyingKey(null);
    }
  }

  async function handleDismiss(itemId: string) {
    setDismissingId(itemId);
    try {
      await dismissInboxItem(itemId);
      await load();
    } finally {
      setDismissingId(null);
    }
  }

  const pending = items.filter((item) => !["processed", "ignored"].includes(String(item.status ?? "")));

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Inbox</h1>
        <p className="text-sm text-muted">Fang opp ting — assistenten foreslår neste steg.</p>
      </div>

      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ny inbox-linje…"
          className="flex-1 rounded-xl border border-border bg-transparent px-4 py-3"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          Legg til
        </button>
      </form>

      <div className="space-y-3">
        {pending.map((item) => {
          const suggestions = item.suggestions ?? [];
          const isDocument = item.signal_type === "document";
          return (
            <article key={String(item.id)} className="rounded-2xl border border-border bg-zinc-950/40 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">{String(item.text ?? "Uten tekst")}</p>
                  <p className="mt-1 text-xs text-muted capitalize">
                    {isDocument ? `Dokument · ${item.doc_type ?? "fil"}` : `Status: ${item.status ?? "captured"}`}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={dismissingId === String(item.id)}
                  onClick={() => handleDismiss(String(item.id))}
                  className="shrink-0 rounded-lg border border-border px-3 py-1.5 text-xs text-muted disabled:opacity-60"
                >
                  Ignorer
                </button>
              </div>

              {suggestions.length > 0 ? (
                <div className="mt-4 space-y-2">
                  <p className="text-xs uppercase tracking-wide text-muted">Forslag</p>
                  {suggestions.map((suggestion, index) => (
                    <div
                      key={`${item.id}-${index}`}
                      className="flex items-center justify-between gap-3 rounded-xl border border-border px-3 py-2"
                    >
                      <span className="text-sm">{suggestionLabel(suggestion)}</span>
                      <button
                        type="button"
                        disabled={applyingKey === `${item.id}:${index}`}
                        onClick={() => handleApply(String(item.id), index)}
                        className="shrink-0 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white disabled:opacity-60"
                      >
                        {suggestionActionLabel(suggestion)}
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-muted">Ingen forslag for dette signalet.</p>
              )}
            </article>
          );
        })}
        {pending.length === 0 && <p className="text-sm text-muted">Inbox er tom.</p>}
      </div>
    </div>
  );
}
