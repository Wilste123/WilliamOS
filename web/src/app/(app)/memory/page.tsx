"use client";

import { FormEvent, useEffect, useState } from "react";

import { fetchMemory, saveMemory } from "@/lib/api";

export default function MemoryPage() {
  const [text, setText] = useState("");
  const [stored, setStored] = useState("");
  const [key, setKey] = useState("");
  const [category, setCategory] = useState("");

  async function load() {
    const data = await fetchMemory();
    setStored(data.text);
  }

  useEffect(() => {
    load().catch(() => setStored("Kunne ikke laste minne."));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    await saveMemory(text.trim(), key || undefined, category || undefined);
    setText("");
    await load();
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Minne</h1>
        <p className="text-sm text-muted">Lagre fakta assistenten skal vite.</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-border p-4">
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
