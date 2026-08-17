"use client";

import { FormEvent, useEffect, useState } from "react";

import { fetchMe, updateAssistantName } from "@/lib/api";

export default function SettingsPage() {
  const [assistantName, setAssistantName] = useState("WilliamOS");
  const [saved, setSaved] = useState<string | null>(null);

  useEffect(() => {
    fetchMe().then((me) => setAssistantName(me.assistant_name ?? "WilliamOS"));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const result = await updateAssistantName(assistantName.trim());
    setAssistantName(result.assistant_name);
    setSaved(result.assistant_name);
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Innstillinger</h1>
        <p className="text-sm text-muted">Tilpass assistenten din.</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-border p-4">
        <label className="block space-y-1 text-sm">
          <span>Assistentnavn</span>
          <input
            value={assistantName}
            onChange={(e) => setAssistantName(e.target.value)}
            className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
          />
        </label>
        <button type="submit" className="rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white">
          Lagre navn
        </button>
        {saved && <p className="text-sm text-muted">Assistenten heter nå {saved}.</p>}
      </form>
    </div>
  );
}
