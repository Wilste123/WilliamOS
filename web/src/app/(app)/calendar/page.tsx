"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { ConfirmDeleteButton } from "@/components/ConfirmDeleteButton";
import { VisibilitySelect } from "@/components/VisibilitySelect";
import {
  createCalendarEvent,
  deleteCalendarEvent,
  fetchCalendar,
  syncGoogleCalendar,
  updateCalendarEvent,
  type CalendarEvent,
} from "@/lib/api";
import { formatDate, formatDateTime, formatTime, toDateInputValue, toTimeInputValue } from "@/lib/format";
import type { Visibility } from "@/lib/visibility";

const WEEKDAYS = ["Ma", "Ti", "On", "To", "Fr", "Lø", "Sø"];
const MONTH_NAMES = [
  "Januar",
  "Februar",
  "Mars",
  "April",
  "Mai",
  "Juni",
  "Juli",
  "August",
  "September",
  "Oktober",
  "November",
  "Desember",
];

function dateKey(value: Date): string {
  const y = value.getFullYear();
  const m = String(value.getMonth() + 1).padStart(2, "0");
  const d = String(value.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function eventDateKey(event: CalendarEvent): string {
  return toDateInputValue(event.start_at) || "";
}

function buildIso(date: string, time: string, allDay: boolean): string {
  if (!date) return "";
  if (allDay || !time) return `${date}T00:00:00`;
  return `${date}T${time}:00`;
}

function monthGrid(year: number, month: number): (Date | null)[] {
  const first = new Date(year, month, 1);
  const startOffset = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: (Date | null)[] = Array.from({ length: startOffset }, () => null);
  for (let day = 1; day <= daysInMonth; day += 1) {
    cells.push(new Date(year, month, day));
  }
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}

export default function CalendarPage() {
  const today = new Date();
  const [cursor, setCursor] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));
  const [selected, setSelected] = useState(dateKey(today));
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [date, setDate] = useState(selected);
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("10:00");
  const [allDay, setAllDay] = useState(false);
  const [visibility, setVisibility] = useState<Visibility>("household");
  const [syncGoogle, setSyncGoogle] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await fetchCalendar({ days: 60 });
      setEvents(rows);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    setDate(selected);
  }, [selected]);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const event of events) {
      const key = eventDateKey(event);
      if (!key) continue;
      const list = map.get(key) ?? [];
      list.push(event);
      map.set(key, list);
    }
    return map;
  }, [events]);

  const grid = monthGrid(cursor.getFullYear(), cursor.getMonth());
  const selectedEvents = eventsByDay.get(selected) ?? [];

  function resetForm() {
    setEditingId(null);
    setTitle("");
    setDescription("");
    setLocation("");
    setStartTime("09:00");
    setEndTime("10:00");
    setAllDay(false);
    setVisibility("household");
    setSyncGoogle(true);
  }

  function startEdit(event: CalendarEvent) {
    setEditingId(String(event.id));
    setTitle(String(event.title ?? ""));
    setDescription(String(event.description ?? ""));
    setLocation(String(event.location ?? ""));
    setDate(eventDateKey(event) || selected);
    setStartTime(toTimeInputValue(event.start_at) || "09:00");
    setEndTime(toTimeInputValue(event.end_at) || "10:00");
    setAllDay(Boolean(event.all_day));
    setVisibility((event.visibility as Visibility) ?? "household");
    setSyncGoogle(true);
  }

  async function onSubmit(formEvent: FormEvent) {
    formEvent.preventDefault();
    if (!title.trim() || !date) return;
    setSaving(true);
    try {
      const body = {
        title: title.trim(),
        description: description.trim() || undefined,
        location: location.trim() || undefined,
        start_at: buildIso(date, startTime, allDay),
        end_at: allDay ? undefined : buildIso(date, endTime, false),
        all_day: allDay,
        visibility,
        sync_google: syncGoogle,
      };
      if (editingId) {
        await updateCalendarEvent(editingId, body);
      } else {
        await createCalendarEvent(body);
      }
      resetForm();
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function handleSync() {
    setSyncing(true);
    try {
      await syncGoogleCalendar();
      await load();
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Kalender</h1>
          <p className="text-sm text-muted">Planlegg avtaler — synkes med Google når tilkoblet.</p>
        </div>
        <button
          type="button"
          onClick={handleSync}
          disabled={syncing}
          className="rounded-lg border border-border px-3 py-2 text-xs text-muted disabled:opacity-60"
        >
          {syncing ? "Synker…" : "Synk Google"}
        </button>
      </div>

      <section className="rounded-2xl border border-border p-4">
        <div className="mb-4 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1))}
            className="rounded-lg border border-border px-3 py-1.5 text-sm"
          >
            ←
          </button>
          <h2 className="text-sm font-medium">
            {MONTH_NAMES[cursor.getMonth()]} {cursor.getFullYear()}
          </h2>
          <button
            type="button"
            onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1))}
            className="rounded-lg border border-border px-3 py-1.5 text-sm"
          >
            →
          </button>
        </div>

        <div className="grid grid-cols-7 gap-1 text-center text-xs text-muted">
          {WEEKDAYS.map((label) => (
            <div key={label} className="py-1">
              {label}
            </div>
          ))}
        </div>

        <div className="mt-1 grid grid-cols-7 gap-1">
          {grid.map((day, index) => {
            if (!day) {
              return <div key={`empty-${index}`} className="aspect-square" />;
            }
            const key = dateKey(day);
            const count = eventsByDay.get(key)?.length ?? 0;
            const isSelected = key === selected;
            const isToday = key === dateKey(today);
            return (
              <button
                key={key}
                type="button"
                onClick={() => setSelected(key)}
                className={`flex aspect-square flex-col items-center justify-center rounded-xl text-sm transition ${
                  isSelected
                    ? "bg-accent text-white"
                    : isToday
                      ? "border border-accent/50 bg-accent/10"
                      : "hover:bg-zinc-900"
                }`}
              >
                <span>{day.getDate()}</span>
                {count > 0 && (
                  <span
                    className={`mt-0.5 h-1.5 w-1.5 rounded-full ${
                      isSelected ? "bg-white" : "bg-accent"
                    }`}
                  />
                )}
              </button>
            );
          })}
        </div>
      </section>

      <section className="rounded-2xl border border-border p-4">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">
          {formatDate(`${selected}T12:00:00`)}
        </h2>
        {loading && selectedEvents.length === 0 ? (
          <p className="text-sm text-muted">Laster…</p>
        ) : selectedEvents.length > 0 ? (
          <ul className="space-y-2">
            {selectedEvents.map((event) => (
              <li
                key={String(event.id)}
                className="flex items-start justify-between gap-3 rounded-xl border border-border px-3 py-2"
              >
                <button
                  type="button"
                  onClick={() => startEdit(event)}
                  className="min-w-0 flex-1 text-left"
                >
                  <p className="break-words font-medium">{String(event.title ?? "Hendelse")}</p>
                  <p className="text-xs text-muted">
                    {event.all_day
                      ? "Heldags"
                      : formatDateTime(event.start_at) +
                        (event.end_at ? ` – ${formatTime(event.end_at)}` : "")}
                    {event.source === "google" ? " · Google" : ""}
                  </p>
                  {event.location ? (
                    <p className="break-words text-xs text-muted">{String(event.location)}</p>
                  ) : null}
                </button>
                <ConfirmDeleteButton
                  confirmMessage="Slette avtalen?"
                  onConfirm={async () => {
                    await deleteCalendarEvent(String(event.id));
                    if (editingId === String(event.id)) resetForm();
                    load();
                  }}
                />
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted">Ingen avtaler denne dagen.</p>
        )}
      </section>

      <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-border p-4">
        <h2 className="text-sm font-medium">{editingId ? "Rediger avtale" : "Ny avtale"}</h2>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Tittel"
          required
          className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        />
        <div className="grid grid-cols-2 gap-2">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
            className="min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
          />
          <label className="flex items-center gap-2 rounded-xl border border-border px-4 py-3 text-sm">
            <input type="checkbox" checked={allDay} onChange={(e) => setAllDay(e.target.checked)} />
            Heldags
          </label>
        </div>
        {!allDay && (
          <div className="grid grid-cols-2 gap-2">
            <label className="block space-y-1 text-xs text-muted">
              Start
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm text-foreground"
              />
            </label>
            <label className="block space-y-1 text-xs text-muted">
              Slutt
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm text-foreground"
              />
            </label>
          </div>
        )}
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Sted (valgfritt)"
          className="w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Beskrivelse (valgfritt)"
          className="min-h-20 w-full min-w-0 rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
        />
        <VisibilitySelect value={visibility} onChange={setVisibility} />
        <label className="flex items-center gap-2 text-sm text-muted">
          <input type="checkbox" checked={syncGoogle} onChange={(e) => setSyncGoogle(e.target.checked)} />
          Opprett/oppdater i Google Calendar
        </label>
        <div className="flex flex-wrap gap-2">
          <button
            type="submit"
            disabled={saving || !title.trim()}
            className="rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-white disabled:opacity-60"
          >
            {saving ? "Lagrer…" : editingId ? "Oppdater" : "Opprett avtale"}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="rounded-xl border border-border px-4 py-2.5 text-sm"
            >
              Avbryt
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
