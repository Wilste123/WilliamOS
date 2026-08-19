"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { StatCard } from "@/components/StatCard";
import { fetchHome, fetchWeeklyBrief, type WeeklyBrief } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { getTimeGreeting, type HomeSummary } from "@/lib/home";
import { priorityItemActionLabel, priorityItemHref } from "@/lib/priority-links";

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
  const [brief, setBrief] = useState<WeeklyBrief | null>(null);
  const [error, setError] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    const [home, weekly] = await Promise.all([fetchHome(), fetchWeeklyBrief()]);
    setSummary(home);
    setBrief(weekly);
    setError(false);
  }, []);

  useEffect(() => {
    load().catch(() => setError(true));
  }, [load]);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await load();
    } catch {
      setError(true);
    } finally {
      setRefreshing(false);
    }
  }

  if (error && !summary) {
    return <p className="text-sm text-muted">Kunne ikke laste startsiden.</p>;
  }

  if (!summary) {
    return <HomeSkeleton />;
  }

  const hasNetWorth = Boolean(summary.net_worth_nok) && summary.net_worth_formatted !== "—";

  return (
    <div className="space-y-6">
      <header className="flex items-start justify-between gap-3 pt-2">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold tracking-tight">
            {getTimeGreeting(summary.greeting_name)}
          </h1>
          <p className="text-sm text-muted">Her er dagen din i korthet.</p>
        </div>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={refreshing}
          className="rounded-lg border border-border px-3 py-2 text-xs text-muted disabled:opacity-60"
        >
          {refreshing ? "Oppdaterer…" : "Oppdater"}
        </button>
      </header>

      <div className="grid grid-cols-2 gap-3">
        <StatCard
          label="Verdier"
          value={summary.net_worth_formatted}
          hint={hasNetWorth ? undefined : "Ingen eiendeler ennå"}
          href={hasNetWorth ? undefined : "/assets"}
        />
        <StatCard label="Mål" value={`${summary.active_goals} aktive`} hint="Se mål" href="/goals" />
        <StatCard
          label="Oppgaver"
          value={`${summary.open_tasks} åpne`}
          hint={summary.open_tasks === 0 ? "Opprett en oppgave" : undefined}
          href={summary.open_tasks === 0 ? "/tasks" : undefined}
        />
        <StatCard label="Prosjekter" value={`${summary.metrics?.projects ?? 0} aktive`} />
      </div>

      <section className="rounded-2xl border border-border p-4">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Ukens brief</h2>
          <Link
            href={`/chat?prompt=${encodeURIComponent("Hva bør jeg gjøre denne uka?")}&send=1`}
            className="text-xs text-accent"
          >
            Spør i chat
          </Link>
        </div>
        {brief?.focus_items && brief.focus_items.length > 0 ? (
          <ul className="space-y-2">
            {brief.focus_items.slice(0, 5).map((item) => (
              <li key={`${item.source_type}-${item.title}`}>
                <Link
                  href={priorityItemHref(item)}
                  className="block rounded-xl bg-zinc-900/60 px-3 py-2 text-sm transition hover:bg-zinc-900"
                >
                  <span className="text-xs uppercase text-muted">{item.source_type}</span>
                  <p className="break-words">{item.title}</p>
                  {item.reason ? <p className="break-words text-xs text-muted">{item.reason}</p> : null}
                </Link>
              </li>
            ))}
          </ul>
        ) : brief?.priorities && brief.priorities.length > 0 ? (
          <ul className="space-y-2">
            {brief.priorities.slice(0, 3).map((task) => (
              <li key={String(task.id ?? task.title)} className="rounded-xl bg-zinc-900/60 px-3 py-2 text-sm">
                {String(task.title)}
                {task.due_date ? (
                  <span className="ml-2 text-xs text-muted">· {formatDate(task.due_date)}</span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted">{brief?.summary_text?.split("\n")[1] ?? "Ingen presserende ting akkurat nå."}</p>
        )}
      </section>

      <section className="rounded-2xl border border-border p-4">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-muted">Prioriteringer</h2>
        {summary.focus_items && summary.focus_items.length > 0 ? (
          <ol className="space-y-3">
            {summary.focus_items.map((item, index) => {
              const actionLabel = priorityItemActionLabel(item);
              return (
                <li key={`${item.source_type}-${item.title}`}>
                  <Link
                    href={priorityItemHref(item)}
                    className="flex items-start gap-3 rounded-xl px-1 py-1 transition hover:bg-zinc-900/50"
                  >
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/15 text-sm font-medium text-accent">
                      {index + 1}
                    </span>
                    <span className="pt-0.5">
                      <span className="block text-base">{item.title}</span>
                      <span className="text-xs text-muted">{item.reason}</span>
                      {actionLabel ? (
                        <span className="mt-1 block text-xs text-accent">{actionLabel} →</span>
                      ) : null}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ol>
        ) : summary.priorities.length > 0 ? (
          <ol className="space-y-3">
            {summary.priorities.map((title, index) => (
              <li key={title}>
                <Link
                  href={`/chat?prompt=${encodeURIComponent(`Hjelp meg med: ${title}`)}&send=1`}
                  className="flex items-start gap-3 rounded-xl px-1 py-1 transition hover:bg-zinc-900/50"
                >
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/15 text-sm font-medium text-accent">
                    {index + 1}
                  </span>
                  <span className="pt-0.5 text-base">{title}</span>
                </Link>
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
