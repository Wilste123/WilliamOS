"use client";

import { useCallback, useEffect, useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { fetchHealthSummary, type HealthSummary } from "@/lib/api";

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-zinc-950/50 p-4">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

export default function HealthPage() {
  const [summary, setSummary] = useState<HealthSummary | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    try {
      setSummary(await fetchHealthSummary());
      setError(false);
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const weightGoal = summary?.weight_goal;
  const goalTitle = weightGoal ? String(weightGoal.title ?? "") : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Helse</h1>
        <p className="text-sm text-muted">Vekt, søvn, aktivitet — manuelt eller via integrasjoner.</p>
      </div>

      {error && !summary && (
        <p className="text-sm text-red-400">
          Kunne ikke laste helse. Kjør migrasjonen{" "}
          <code className="text-xs">2026-08-17_finance_health_integrations.sql</code> i Supabase.
        </p>
      )}

      {summary && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <MetricCard
              label="Vekt nå"
              value={summary.latest_weight_kg != null ? `${summary.latest_weight_kg} kg` : "—"}
            />
            <MetricCard
              label="Mål"
              value={goalTitle ?? "—"}
            />
            <MetricCard
              label="Søvn (7d snitt)"
              value={summary.avg_sleep_hours_7d != null ? `${summary.avg_sleep_hours_7d} t` : "—"}
            />
            <MetricCard
              label="Aktivitet (7d snitt)"
              value={
                summary.avg_activity_minutes_7d != null
                  ? `${summary.avg_activity_minutes_7d} min`
                  : summary.avg_steps_7d != null
                    ? `${summary.avg_steps_7d} steg`
                    : "—"
              }
            />
          </div>

          {summary.sources.length > 0 && (
            <p className="text-xs text-muted">Kilder: {summary.sources.join(", ")}</p>
          )}

          <section className="rounded-2xl border border-border p-4">
            <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">Siste registreringer</h2>
            {summary.recent_metrics.length === 0 ? (
              <p className="text-sm text-muted">Ingen helsemetrics ennå.</p>
            ) : (
              <ul className="space-y-2">
                {summary.recent_metrics.map((metric) => (
                  <li key={String(metric.id)} className="rounded-xl bg-zinc-900/60 px-3 py-2 text-sm">
                    {String(metric.metric_type)} · {String(metric.value)} {String(metric.unit ?? "")}
                    <span className="ml-2 text-xs text-muted">{String(metric.source ?? "manual")}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      <CreateRecordForm
        path="/health-data/metrics"
        submitLabel="Registrer metric"
        fields={[
          {
            name: "metric_type",
            label: "Type (weight/sleep_hours/activity_minutes/steps)",
            type: "text",
            required: true,
            placeholder: "weight",
          },
          { name: "value", label: "Verdi", type: "number", required: true, placeholder: "89.6" },
          { name: "notes", label: "Notat", type: "text", placeholder: "Morgenveiing" },
        ]}
        onCreated={() => setRefreshKey((key) => key + 1)}
      />
    </div>
  );
}
