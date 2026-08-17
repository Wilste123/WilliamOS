"use client";

import { FormEvent, useEffect, useState } from "react";

import { captureInbox, fetchInbox } from "@/lib/api";

export default function InboxPage() {
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  async function load() {
    const data = await fetchInbox();
    setItems(data as Record<string, unknown>[]);
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
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Inbox</h1>
        <p className="text-sm text-muted">Fang opp ting du vil følge opp senere.</p>
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
          className="rounded-xl border border-border px-4 py-3"
        >
          Legg til
        </button>
      </form>

      <div className="space-y-3">
        {items.map((item) => (
          <article key={String(item.id)} className="rounded-2xl border border-border p-4">
            <p className="text-sm">{String(item.text ?? item.title ?? "Uten tekst")}</p>
          </article>
        ))}
        {items.length === 0 && <p className="text-sm text-muted">Inbox er tom.</p>}
      </div>
    </div>
  );
}
