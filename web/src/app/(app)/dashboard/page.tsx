"use client";

import { useEffect, useState } from "react";

import { fetchDashboard, fetchWeeklyBrief, type DashboardSummary } from "@/lib/api";

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-border p-4">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function ItemList({
  title,
  items,
  render,
}: {
  title: string;
  items: Record<string, unknown>[];
  render: (item: Record<string, unknown>) => string;
}) {
  return (
    <section className="rounded-2xl border border-border p-4">
      <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">{title}</h2>
      {items.length === 0 ? (
        <p className="text-sm text-muted">Ingen poster.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={String(item.id)} className="text-sm">
              {render(item)}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [brief, setBrief] = useState<string>("");

  useEffect(() => {
    Promise.all([fetchDashboard(), fetchWeeklyBrief()])
      .then(([dash, weekly]) => {
        setDashboard(dash);
        setBrief(weekly.summary_text);
      })
      .catch(() => {
        setDashboard(null);
      });
  }, []);

  if (!dashboard) {
    return <p className="text-sm text-muted">Kunne ikke laste dashboard.</p>;
  }

  const { metrics } = dashboard;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted">Oversikt og prioriteringer.</p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Metric label="Eiendeler" value={metrics.assets} />
        <Metric label="Åpne oppgaver" value={metrics.open_tasks} />
        <Metric label="Aktive prosjekter" value={metrics.projects} />
        <Metric label="Dokumenter" value={metrics.documents} />
        <Metric label="Åpne beslutninger" value={metrics.open_decisions} />
      </div>

      {brief && (
        <section className="rounded-2xl border border-border p-4">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">
            Hva bør du gjøre denne uka?
          </h2>
          <pre className="whitespace-pre-wrap text-sm text-foreground">{brief}</pre>
        </section>
      )}

      <ItemList
        title="Prioriterte oppgaver"
        items={dashboard.priorities}
        render={(item) =>
          `${item.title} · P${item.priority ?? 2}${item.due_date ? ` · ${item.due_date}` : ""}`
        }
      />

      <ItemList
        title="Kommende hendelser"
        items={dashboard.upcoming_events}
        render={(item) => `${item.title} · ${item.event_date ?? "dato ukjent"}`}
      />

      <ItemList
        title="Aktive prosjekter"
        items={dashboard.active_projects}
        render={(item) => `${item.name} · ${item.next_action ?? "Ingen neste handling"}`}
      />

      <ItemList
        title="Nye dokumenter"
        items={dashboard.new_documents}
        render={(item) => String(item.filename ?? item.title ?? "Dokument")}
      />

      <ItemList
        title="Nylig aktivitet"
        items={dashboard.recent_activity}
        render={(item) => `${item.title} · ${item.event_type ?? "event"}`}
      />
    </div>
  );
}
