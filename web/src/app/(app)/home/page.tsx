"use client";

import { useEffect, useState } from "react";

import { fetchHome } from "@/lib/api";
import { getTimeGreeting, type HomeSummary } from "@/lib/home";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-border bg-zinc-950/50 p-4">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

export default function HomePage() {
  const [summary, setSummary] = useState<HomeSummary | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchHome()
      .then(setSummary)
      .catch(() => setError(true));
  }, []);

  if (error) {
    return <p className="text-sm text-muted">Kunne ikke laste startsiden.</p>;
  }

  if (!summary) {
    return <p className="text-sm text-muted">Laster oversikt…</p>;
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1 pt-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          {getTimeGreeting(summary.greeting_name)}
        </h1>
        <p className="text-sm text-muted">Her er dagen din i korthet.</p>
      </header>

      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Nettoformue" value={summary.net_worth_formatted} />
        <StatCard label="Mål" value={`${summary.active_goals} aktive`} />
        <StatCard label="Oppgaver" value={`${summary.open_tasks} åpne`} />
        <StatCard
          label="Prosjekter"
          value={`${summary.metrics?.projects ?? 0} aktive`}
        />
      </div>

      <section className="rounded-2xl border border-border p-4">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-muted">
          Prioriteringer
        </h2>
        {summary.priorities.length > 0 ? (
          <ol className="space-y-3">
            {summary.priorities.map((title, index) => (
              <li key={title} className="flex items-start gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/15 text-sm font-medium text-accent">
                  {index + 1}
                </span>
                <span className="pt-0.5 text-base">{title}</span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-sm text-muted">Ingen presserende prioriteringer akkurat nå.</p>
        )}
      </section>
    </div>
  );
}
