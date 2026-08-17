"use client";

import { useEffect, useState } from "react";

import { fetchDashboard } from "@/lib/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    fetchDashboard()
      .then(setSummary)
      .catch(() => setSummary(null));
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Oversikt</h1>
        <p className="text-sm text-muted">Dashboard og prioriteringer.</p>
      </div>

      {!summary && <p className="text-sm text-muted">Kunne ikke laste dashboard.</p>}

      {summary && (
        <div className="space-y-3">
          {Object.entries(summary).map(([key, value]) => (
            <section key={key} className="rounded-2xl border border-border p-4">
              <h2 className="mb-2 text-sm font-medium capitalize">{key.replace(/_/g, " ")}</h2>
              <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-muted">
                {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
              </pre>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
