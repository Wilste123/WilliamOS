"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { ConfirmDeleteButton } from "@/components/ConfirmDeleteButton";
import { VisibilitySelect } from "@/components/VisibilitySelect";
import { createEvent, deleteEvent, fetchCollection, fetchTimeline } from "@/lib/api";
import { entityRecordLabel } from "@/lib/project-links";
import type { Visibility } from "@/lib/visibility";
import { formatDate } from "@/lib/format";

const EVENT_TYPES = [
  { value: "general", label: "Generelt" },
  { value: "maintenance", label: "Vedlikehold" },
  { value: "meeting", label: "Møte" },
  { value: "deadline", label: "Frist" },
  { value: "purchase", label: "Kjøp" },
  { value: "manual", label: "Manuell" },
];

export default function TimelinePage() {
  const [events, setEvents] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [eventType, setEventType] = useState("general");
  const [eventDate, setEventDate] = useState("");
  const [assetId, setAssetId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [decisionId, setDecisionId] = useState("");
  const [visibility, setVisibility] = useState<Visibility>("household");
  const [assets, setAssets] = useState<Record<string, unknown>[]>([]);
  const [projects, setProjects] = useState<Record<string, unknown>[]>([]);
  const [decisions, setDecisions] = useState<Record<string, unknown>[]>([]);
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      fetchTimeline(),
      fetchCollection("/assets"),
      fetchCollection("/projects"),
      fetchCollection("/decisions"),
    ])
      .then(([timeline, assetRows, projectRows, decisionRows]) => {
        setEvents(timeline);
        setAssets(assetRows);
        setProjects(projectRows);
        setDecisions(decisionRows);
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
        event_type: eventType,
        notes: notes.trim() || undefined,
        event_date: eventDate || undefined,
        asset_id: assetId || undefined,
        project_id: projectId || undefined,
        decision_id: decisionId || undefined,
        visibility,
      });
      setTitle("");
      setNotes("");
      setEventDate("");
      setAssetId("");
      setProjectId("");
      setDecisionId("");
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
          required
          className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        />
        <select
          value={eventType}
          onChange={(e) => setEventType(e.target.value)}
          className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        >
          {EVENT_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={eventDate}
          onChange={(e) => setEventDate(e.target.value)}
          className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        />
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notater (valgfritt)"
          className="min-h-20 w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        />
        <select
          value={assetId}
          onChange={(e) => setAssetId(e.target.value)}
          className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        >
          <option value="">Ingen eiendel</option>
          {assets.map((asset) => (
            <option key={String(asset.id)} value={String(asset.id)}>
              {entityRecordLabel(asset)}
            </option>
          ))}
        </select>
        <select
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        >
          <option value="">Ingen prosjekt</option>
          {projects.map((project) => (
            <option key={String(project.id)} value={String(project.id)}>
              {entityRecordLabel(project)}
            </option>
          ))}
        </select>
        <select
          value={decisionId}
          onChange={(e) => setDecisionId(e.target.value)}
          className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        >
          <option value="">Ingen beslutning</option>
          {decisions.map((decision) => (
            <option key={String(decision.id)} value={String(decision.id)}>
              {entityRecordLabel(decision)}
            </option>
          ))}
        </select>
        <VisibilitySelect value={visibility} onChange={setVisibility} />
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
            <div className="min-w-0 flex-1">
              <p className="break-words font-medium">{String(item.title ?? "Hendelse")}</p>
              <p className="mt-1 text-sm text-muted">
                {String(item.event_type ?? "event")} ·{" "}
                {formatDate(item.event_date ?? item.created_at) ?? "—"}
              </p>
              {item.notes != null && String(item.notes) !== "" && (
                <p className="mt-2 break-words text-sm text-muted">{String(item.notes)}</p>
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
