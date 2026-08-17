"use client";

import { FormEvent, useEffect, useState } from "react";

import { fetchMe, fetchUsageStats, updateAssistantName, type UsageStats } from "@/lib/api";
import { APP_NAME } from "@/lib/navigation";

export default function SettingsPage() {
  const [assistantName, setAssistantName] = useState(APP_NAME);
  const [saved, setSaved] = useState<string | null>(null);
  const [usage, setUsage] = useState<UsageStats | null>(null);

  useEffect(() => {
    fetchMe().then((me) => setAssistantName(me.assistant_name ?? APP_NAME));
    fetchUsageStats()
      .then(setUsage)
      .catch(() => setUsage(null));
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

      {usage && (
        <section className="rounded-2xl border border-border p-4">
          <h2 className="font-medium">7-dagers test</h2>
          <p className="mt-1 text-sm text-muted">
            Mål: bruk appen daglig i 7 dager uten Streamlit for kjernefunksjoner.
          </p>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-zinc-900/60 p-3">
              <p className="text-xs uppercase tracking-wide text-muted">Denne uka</p>
              <p className="mt-1 text-2xl font-semibold">{usage.days_opened_this_week}</p>
            </div>
            <div className="rounded-xl bg-zinc-900/60 p-3">
              <p className="text-xs uppercase tracking-wide text-muted">Streak</p>
              <p className="mt-1 text-2xl font-semibold">{usage.streak_days}</p>
            </div>
            <div className="rounded-xl bg-zinc-900/60 p-3">
              <p className="text-xs uppercase tracking-wide text-muted">Totalt</p>
              <p className="mt-1 text-2xl font-semibold">{usage.total_opens}</p>
            </div>
            <div className="rounded-xl bg-zinc-900/60 p-3">
              <p className="text-xs uppercase tracking-wide text-muted">7-dagers mål</p>
              <p className="mt-1 text-2xl font-semibold">
                {usage.seven_day_goal_met ? "✓" : "—"}
              </p>
            </div>
          </div>
        </section>
      )}

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
