"use client";

import { useCallback, useEffect, useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { MigrationRequiredNotice } from "@/components/MigrationRequiredNotice";
import { StatCard } from "@/components/StatCard";
import { fetchFinanceSummary, type FinanceSummary } from "@/lib/api";

function formatNok(value: number) {
  return `${Math.round(value).toLocaleString("nb-NO")} NOK`;
}

export default function FinancePage() {
  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    try {
      setSummary(await fetchFinanceSummary());
      setError(false);
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Økonomi</h1>
        <p className="text-sm text-muted">Formue, gjeld, likviditet og finanskontoer.</p>
      </div>

      {error && !summary && (
        <MigrationRequiredNotice migrationFile="2026-08-17_finance_health_integrations.sql" />
      )}

      {summary && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Nettoformue" value={summary.net_worth_formatted} />
            <StatCard
              label="Siste 12 mnd"
              value={
                summary.change_12m_nok != null
                  ? `${summary.change_12m_nok >= 0 ? "+" : ""}${formatNok(summary.change_12m_nok)}`
                  : "—"
              }
              hint={summary.change_12m_nok == null ? "Lag snapshots over tid" : undefined}
            />
            <StatCard label="Likviditet" value={formatNok(summary.liquidity_nok)} />
            <StatCard label="Gjeld" value={formatNok(summary.debt_nok)} />
          </div>

          <section className="rounded-2xl border border-border p-4">
            <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">Kontoer</h2>
            {summary.accounts.length === 0 ? (
              <p className="text-sm text-muted">Ingen finanskontoer ennå. Eiendeler telles med automatisk.</p>
            ) : (
              <ul className="space-y-2">
                {summary.accounts.map((account) => (
                  <li
                    key={String(account.id)}
                    className="flex items-center justify-between gap-3 rounded-xl bg-zinc-900/60 px-3 py-2 text-sm"
                  >
                    <span className="min-w-0 break-words">
                      {String(account.name)}
                      <span className="ml-2 text-xs text-muted">{String(account.account_type)}</span>
                    </span>
                    <span>{formatNok(Number(account.balance_nok) || 0)}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      <CreateRecordForm
        path="/finance/accounts"
        submitLabel="Legg til konto"
        showVisibility
        fields={[
          { name: "name", label: "Navn", type: "text", required: true, placeholder: "BSU, kredittkort, buffer…" },
          { name: "account_type", label: "Type (asset/debt/liquidity)", type: "text", required: true, placeholder: "liquidity" },
          { name: "balance_nok", label: "Saldo (NOK)", type: "number", required: true, placeholder: "150000" },
          { name: "institution", label: "Bank", type: "text", placeholder: "DNB" },
        ]}
        onCreated={() => setRefreshKey((key) => key + 1)}
      />
    </div>
  );
}
