"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { ConfirmDeleteButton } from "@/components/ConfirmDeleteButton";
import { createEvent, deleteEvent, fetchTimeline } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default function TimelinePage() {
  const [events, setEvents] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    fetchTimeline()
      .then((data) => {
        setEvents(data);
        setLoading(false);
      })
      .catch(() => {
        setEvents([]);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    try {
      await createEvent({
        title: title.trim(),
        event_type: "manual",
        notes: notes.trim() || undefined,
      });
      setTitle("");
      setNotes("");
      load();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Historikk</h1>
        <p className="text-sm text-muted">Hendelser og aktivitet på tvers av WilliamOS.</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-border p-4">
        <h2 className="text-sm font-medium">Legg til hendelse</h2>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Tittel"
          className="w-full rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        />
        <input
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notater (valgfritt)"
          className="w-full rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        />
        <button
          type="submit"
          disabled={saving || !title.trim()}
          className="rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-white disabled:opacity-60"
        >
          {saving ? "Lagrer…" : "Lagre hendelse"}
        </button>
      </form>

      {loading && events.length === 0 && <p className="text-sm text-muted">Laster…</p>}

      <div className="space-y-3">
        {events.map((item) => (
          <article
            key={String(item.id)}
            className="flex items-start justify-between gap-3 rounded-2xl border border-border p-4"
          >
            <div className="min-w-0">
              <p className="font-medium">{String(item.title ?? "Hendelse")}</p>
              <p className="mt-1 text-sm text-muted">
                {String(item.event_type ?? "event")} ·{" "}
                {formatDate(item.event_date ?? item.created_at) ?? "—"}
              </p>
              {item.notes != null && String(item.notes) !== "" && (
                <p className="mt-2 text-sm text-muted">{String(item.notes)}</p>
              )}
            </div>
            <ConfirmDeleteButton
              confirmMessage="Slette hendelsen?"
              onConfirm={async () => {
                await deleteEvent(String(item.id));
                load();
              }}
            />
          </article>
        ))}
        {!loading && events.length === 0 && (
          <p className="text-sm text-muted">Ingen hendelser ennå.</p>
        )}
      </div>
    </div>
  );
}
