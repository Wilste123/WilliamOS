"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import {
  exportUserData,
  fetchMe,
  fetchUsageStats,
  updateProfile,
  type UsageStats,
} from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { ASSET_TYPE_OPTIONS } from "@/lib/asset-types";
import { APP_NAME } from "@/lib/navigation";
import type { UserPreferences } from "@/lib/auth";

export default function SettingsPage() {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [householdId, setHouseholdId] = useState("");
  const [assistantName, setAssistantName] = useState(APP_NAME);
  const [preferences, setPreferences] = useState<UserPreferences>({
    language: "nb",
    default_asset_type: "other",
    inbox_automation: true,
  });
  const [saved, setSaved] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchMe()
      .then((me) => {
        setDisplayName(me.display_name ?? "");
        setEmail(me.email);
        setHouseholdId(me.household_id);
        setAssistantName(me.assistant_name ?? APP_NAME);
        if (me.preferences) setPreferences({ ...preferences, ...me.preferences });
      })
      .catch(() => undefined);
    fetchUsageStats()
      .then(setUsage)
      .catch(() => setUsage(null));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const result = await updateProfile({
        display_name: displayName.trim(),
        assistant_name: assistantName.trim(),
        preferences,
      });
      setDisplayName(String(result.display_name ?? displayName));
      setAssistantName(String(result.assistant_name ?? assistantName));
      if (result.preferences && typeof result.preferences === "object") {
        setPreferences(result.preferences as UserPreferences);
      }
      setSaved("Innstillinger lagret.");
    } catch (err) {
      setSaved(null);
      setError(err instanceof Error ? err.message : "Kunne ikke lagre.");
    }
  }

  async function handleExport() {
    setExporting(true);
    try {
      const data = await exportUserData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `williamos-export-${new Date().toISOString().slice(0, 10)}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eksport feilet.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Innstillinger</h1>
        <p className="text-sm text-muted">Profil, assistent og preferanser.</p>
      </div>

      {usage && (
        <section className="rounded-2xl border border-border p-4">
          <h2 className="font-medium">7-dagers utfordring</h2>
          <p className="mt-1 text-sm text-muted">Bruk appen daglig i 7 dager for å bygge vanen.</p>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <StatCard label="Denne uka" value={String(usage.days_opened_this_week)} />
            <StatCard label="Streak" value={String(usage.streak_days)} />
            <StatCard label="Totalt" value={String(usage.total_opens)} />
            <StatCard label="7-dagers mål" value={usage.seven_day_goal_met ? "✓" : "—"} />
          </div>
        </section>
      )}

      <form onSubmit={onSubmit} className="space-y-6">
        <section className="space-y-3 rounded-2xl border border-border p-4">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Profil</h2>
          <label className="block space-y-1 text-sm">
            <span>Visningsnavn</span>
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
            />
          </label>
          <label className="block space-y-1 text-sm">
            <span>E-post</span>
            <input value={email} readOnly className="w-full rounded-xl border border-border bg-zinc-900/40 px-3 py-3 text-muted" />
          </label>
          <label className="block space-y-1 text-sm">
            <span>Husholdning</span>
            <input
              value={householdId}
              readOnly
              className="w-full break-all rounded-xl border border-border bg-zinc-900/40 px-3 py-3 text-xs text-muted"
            />
          </label>
        </section>

        <section className="space-y-3 rounded-2xl border border-border p-4">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Assistent</h2>
          <label className="block space-y-1 text-sm">
            <span>Assistentnavn</span>
            <input
              value={assistantName}
              onChange={(e) => setAssistantName(e.target.value)}
              className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
            />
          </label>
        </section>

        <section className="space-y-3 rounded-2xl border border-border p-4">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Preferanser</h2>
          <label className="block space-y-1 text-sm">
            <span>Språk</span>
            <select
              value={preferences.language}
              onChange={(e) => setPreferences((prev) => ({ ...prev, language: e.target.value }))}
              className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
            >
              <option value="nb">Norsk bokmål</option>
              <option value="en">English</option>
            </select>
          </label>
          <label className="block space-y-1 text-sm">
            <span>Standard eiendelstype</span>
            <select
              value={preferences.default_asset_type}
              onChange={(e) => setPreferences((prev) => ({ ...prev, default_asset_type: e.target.value }))}
              className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
            >
              {ASSET_TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-3 text-sm">
            <input
              type="checkbox"
              checked={preferences.inbox_automation}
              onChange={(e) => setPreferences((prev) => ({ ...prev, inbox_automation: e.target.checked }))}
            />
            <span>Foreslå inbox-handlinger automatisk</span>
          </label>
        </section>

        <section className="space-y-3 rounded-2xl border border-border p-4">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Integrasjoner</h2>
          <Link href="/integrations" className="inline-flex text-sm text-accent">
            Administrer Gmail, Google m.m. →
          </Link>
        </section>

        <section className="space-y-3 rounded-2xl border border-border p-4">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Data</h2>
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting}
            className="rounded-xl border border-border px-4 py-3 text-sm disabled:opacity-60"
          >
            {exporting ? "Eksporterer…" : "Eksporter JSON"}
          </button>
        </section>

        <button type="submit" className="rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white">
          Lagre innstillinger
        </button>
        {saved && <p className="text-sm text-muted">{saved}</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
      </form>
    </div>
  );
}
