"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchHome } from "@/lib/api";
import { getTimeGreeting, type HomeSummary } from "@/lib/home";

function StatCard({
  label,
  value,
  hint,
  href,
}: {
  label: string;
  value: string | number;
  hint?: string;
  href?: string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-zinc-950/50 p-4">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
      {hint && href && (
        <Link href={href} className="mt-2 inline-block text-sm text-accent">
          {hint}
        </Link>
      )}
    </div>
  );
}

function HomeSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Laster oversikt">
      <header className="space-y-2 pt-2">
        <div className="h-9 w-56 animate-pulse rounded-lg bg-zinc-800" />
        <div className="h-4 w-40 animate-pulse rounded bg-zinc-800" />
      </header>
      <div className="grid grid-cols-2 gap-3">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="h-24 animate-pulse rounded-2xl border border-border bg-zinc-900/50"
          />
        ))}
      </div>
      <div className="h-40 animate-pulse rounded-2xl border border-border bg-zinc-900/50" />
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
    return <HomeSkeleton />;
  }

  const hasNetWorth = Boolean(summary.net_worth_nok) && summary.net_worth_formatted !== "—";

  return (
    <div className="space-y-6">
      <header className="space-y-1 pt-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          {getTimeGreeting(summary.greeting_name)}
        </h1>
        <p className="text-sm text-muted">Her er dagen din i korthet.</p>
      </header>

      <div className="grid grid-cols-2 gap-3">
        <StatCard
          label="Verdier"
          value={summary.net_worth_formatted}
          hint={hasNetWorth ? undefined : "Ingen eiendeler ennå"}
          href={hasNetWorth ? undefined : "/assets"}
        />
        <StatCard label="Mål" value={`${summary.active_goals} aktive`} />
        <StatCard
          label="Oppgaver"
          value={`${summary.open_tasks} åpne`}
          hint={summary.open_tasks === 0 ? "Opprett en oppgave" : undefined}
          href={summary.open_tasks === 0 ? "/tasks" : undefined}
        />
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
          <div className="space-y-2">
            <p className="text-sm text-muted">Ingen presserende prioriteringer akkurat nå.</p>
            <Link href="/tasks" className="text-sm text-accent">
              Opprett en oppgave
            </Link>
          </div>
        )}
      </section>
    </div>
  );
}
