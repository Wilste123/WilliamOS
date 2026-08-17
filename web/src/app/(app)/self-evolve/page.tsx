"use client";

import { useEffect, useState } from "react";

import { fetchSelfEvolve } from "@/lib/api";

export default function SelfEvolvePage() {
  const [analysis, setAnalysis] = useState<{ count: number; top_signals: [string, number][] } | null>(
    null
  );

  useEffect(() => {
    fetchSelfEvolve()
      .then(setAnalysis)
      .catch(() => setAnalysis(null));
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">self-evolve</h1>
        <p className="text-sm text-muted">Signaler fra chat som kan bli nye funksjoner.</p>
      </div>

      {!analysis && <p className="text-sm text-muted">Kunne ikke laste signaler.</p>}

      {analysis && (
        <>
          <div className="rounded-2xl border border-border p-4">
            <p className="text-xs uppercase tracking-wide text-muted">Forespørsler logget</p>
            <p className="mt-1 text-2xl font-semibold">{analysis.count}</p>
          </div>

          <section className="rounded-2xl border border-border p-4">
            <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">Toppsignaler</h2>
            {analysis.top_signals.length === 0 ? (
              <p className="text-sm text-muted">Ingen signaler ennå. Bruk chatten først.</p>
            ) : (
              <ul className="space-y-2">
                {analysis.top_signals.map(([keyword, count]) => (
                  <li key={keyword} className="text-sm">
                    <span className="font-medium">{keyword}</span>: {count} ganger
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
