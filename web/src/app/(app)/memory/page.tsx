"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { fetchGoals, fetchMemory, saveMemory } from "@/lib/api";

export default function MemoryPage() {
  const [text, setText] = useState("");
  const [stored, setStored] = useState("");
  const [key, setKey] = useState("");
  const [category, setCategory] = useState("");
  const [goals, setGoals] = useState<Record<string, unknown>[]>([]);
  const [goalRefresh, setGoalRefresh] = useState(0);

  async function load() {
    const [memory, goalRows] = await Promise.all([fetchMemory(), fetchGoals().catch(() => [])]);
    setStored(memory.text);
    setGoals(goalRows);
  }

  useEffect(() => {
    load().catch(() => setStored("Kunne ikke laste minne."));
  }, [goalRefresh]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    try {
      await saveMemory(text.trim(), key || undefined, category || undefined);
      setText("");
      await load();
    } catch {
      setStored("Kunne ikke lagre minne.");
    }
  }

  const activeGoals = goals.filter((goal) => goal.status === "active");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Minne</h1>
        <p className="text-sm text-muted">Lagre fakta assistenten skal vite, og følg aktive mål.</p>
      </div>

      <section className="space-y-3 rounded-2xl border border-border p-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Mål</h2>
          <Link href="/goals" className="text-xs text-accent">
            Alle mål
          </Link>
        </div>
        {activeGoals.length > 0 ? (
          <ul className="space-y-2">
            {activeGoals.slice(0, 5).map((goal) => (
              <li key={String(goal.id)} className="rounded-xl bg-zinc-900/60 px-3 py-2 text-sm">
                <p className="font-medium">{String(goal.title)}</p>
                {goal.next_step ? <p className="text-xs text-muted">Neste: {String(goal.next_step)}</p> : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted">Ingen aktive mål ennå.</p>
        )}
        <CreateRecordForm
          path="/goals"
          submitLabel="Legg til mål"
          fields={[
            { name: "title", label: "Mål", type: "text", required: true, placeholder: "Hva vil du oppnå?" },
            { name: "next_step", label: "Neste steg", type: "text", placeholder: "Hva er neste handling?" },
          ]}
          onCreated={() => setGoalRefresh((value) => value + 1)}
        />
      </section>

      <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-border p-4">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Lagre minne</h2>
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
        <pre className="whitespace-pre-wrap text-sm text-muted">{stored}</pre>
      </section>
    </div>
  );
}
