"use client";

import { useEffect, useState } from "react";

import { fetchTimeline } from "@/lib/api";

export default function TimelinePage() {
  const [events, setEvents] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    fetchTimeline()
      .then(setEvents)
      .catch(() => setEvents([]));
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Timeline</h1>
        <p className="text-sm text-muted">Aktivitetshistorikk.</p>
      </div>
      <div className="space-y-3">
        {events.map((event) => (
          <article key={String(event.id)} className="rounded-2xl border border-border p-4">
            <p className="font-medium">{String(event.title ?? "Hendelse")}</p>
            <p className="text-sm text-muted">
              {String(event.event_type ?? "event")} · {String(event.event_date ?? event.created_at ?? "—")}
            </p>
          </article>
        ))}
        {events.length === 0 && <p className="text-sm text-muted">Ingen hendelser ennå.</p>}
      </div>
    </div>
  );
}
