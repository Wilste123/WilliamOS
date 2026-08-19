"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { fetchGoals, fetchMemory, saveMemory } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default function MemoryPage() {
  const [text, setText] = useState("");
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [key, setKey] = useState("");
  const [category, setCategory] = useState("");
  const [goals, setGoals] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const [memory, goalRows] = await Promise.all([fetchMemory(), fetchGoals().catch(() => [])]);
    setItems(memory.items ?? []);
    setGoals(goalRows);
    setError(null);
  }

  useEffect(() => {
    load().catch(() => setError("Kunne ikke laste minne."));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    try {
      await saveMemory(text.trim(), key || undefined, category || undefined);
      setText("");
      setKey("");
      setCategory("");
      await load();
    } catch {
      setError("Kunne ikke lagre minne.");
    }
  }

  const activeGoals = goals.filter((goal) => goal.status === "active");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Minne</h1>
        <p className="text-sm text-muted">
          Assistenten husker viktige hendelser automatisk. Du kan også lagre manuelt eller skrive «husk …» i chat.
        </p>
      </div>

      <section className="space-y-3 rounded-2xl border border-border p-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Aktive mål</h2>
          <Link href="/goals" className="text-xs text-accent">
            Alle mål
          </Link>
        </div>
        {activeGoals.length > 0 ? (
          <ul className="space-y-2">
            {activeGoals.slice(0, 5).map((goal) => (
              <li key={String(goal.id)}>
                <Link
                  href={`/goals/${String(goal.id)}`}
                  className="block rounded-xl bg-zinc-900/60 px-3 py-2 text-sm hover:bg-zinc-900"
                >
                  <p className="font-medium">{String(goal.title)}</p>
                  {goal.next_step ? (
                    <p className="text-xs text-muted">Neste: {String(goal.next_step)}</p>
                  ) : null}
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted">Ingen aktive mål. Opprett under Mål.</p>
        )}
      </section>

      <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-border p-4">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Lagre minne manuelt</h2>
        <input
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="Nøkkel (valgfritt)"
          className="w-full rounded-xl border border-border bg-transparent px-3 py-3 text-sm"
        />
        <input
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Kategori (valgfritt)"
          className="w-full rounded-xl border border-border bg-transparent px-3 py-3 text-sm"
        />
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Hva skal huskes?"
          className="min-h-28 w-full rounded-xl border border-border bg-transparent px-3 py-3 text-sm"
        />
        <button type="submit" className="rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white">
          Lagre minne
        </button>
      </form>

      <section className="rounded-2xl border border-border p-4">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">Lagret kontekst</h2>
        {error && <p className="text-sm text-red-400">{error}</p>}
        {items.length === 0 ? (
          <p className="text-sm text-muted">Ingen minne ennå. Systemet fyller på når du oppretter eiendeler, oppgaver, dokumenter m.m.</p>
        ) : (
          <ul className="space-y-2">
            {items.map((item) => (
              <li key={String(item.id)} className="rounded-xl border border-border/60 px-3 py-3 text-sm">
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                  {item.category ? (
                    <span className="rounded-full bg-zinc-800 px-2 py-0.5">{String(item.category)}</span>
                  ) : null}
                  {item.source ? (
                    <span className="rounded-full bg-accent/10 px-2 py-0.5 text-accent">{String(item.source)}</span>
                  ) : (
                    <span className="rounded-full bg-zinc-800 px-2 py-0.5">manuell</span>
                  )}
                  {item.created_at ? <span>{formatDate(item.created_at)}</span> : null}
                </div>
                {item.key ? <p className="mt-1 text-xs text-muted">{String(item.key)}</p> : null}
                <p className="mt-2">{String(item.value)}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
