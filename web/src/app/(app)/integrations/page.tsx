"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import {
  connectIntegration,
  disconnectIntegration,
  fetchIntegrations,
  syncIntegration,
  type IntegrationStatus,
} from "@/lib/api";

function statusLabel(status: string) {
  switch (status) {
    case "connected":
      return "Tilkoblet";
    case "pending":
      return "Venter…";
    case "error":
      return "Feil";
    default:
      return "Ikke tilkoblet";
  }
}

function IntegrationsPageInner() {
  const searchParams = useSearchParams();
  const [items, setItems] = useState<IntegrationStatus[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setItems(await fetchIntegrations());
  }, []);

  useEffect(() => {
    load().catch(() => setItems([]));
  }, [load]);

  useEffect(() => {
    const connected = searchParams.get("connected");
    const error = searchParams.get("error");
    if (connected) setMessage(`${connected} er tilkoblet.`);
    if (error) setMessage(`Feil: ${error}`);
  }, [searchParams]);

  async function handleConnect(provider: string, connectType: string) {
    setBusy(provider);
    setMessage(null);
    try {
      const result = await connectIntegration(provider);
      if (connectType === "oauth" && result.auth_url) {
        window.location.href = result.auth_url;
        return;
      }
      setMessage(`${provider} er klar (manuell modus).`);
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Kunne ikke koble til.");
    } finally {
      setBusy(null);
    }
  }

  async function handleSync(provider: string) {
    setBusy(`sync-${provider}`);
    try {
      const result = await syncIntegration(provider);
      const parts = [];
      if (result.synced_events) parts.push(`${result.synced_events} kalenderhendelser`);
      if (result.synced_signals) parts.push(`${result.synced_signals} inbox-signaler`);
      setMessage(
        parts.length
          ? `Synkroniserte ${parts.join(" og ")}.`
          : result.message ?? "Synkronisert."
      );
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Synk feilet.");
    } finally {
      setBusy(null);
    }
  }

  async function handleDisconnect(provider: string) {
    setBusy(`disc-${provider}`);
    await disconnectIntegration(provider);
    await load();
    setBusy(null);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Integrasjoner</h1>
        <p className="text-sm text-muted">Google Calendar, Gmail, Apple Health, Garmin og Strava.</p>
      </div>

      {message && (
        <p className="rounded-xl border border-border bg-zinc-900/60 px-4 py-3 text-sm">{message}</p>
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <article key={item.provider} className="rounded-2xl border border-border p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-medium">{item.label}</h2>
                <p className="text-sm text-muted">{item.description}</p>
                <p className="mt-1 text-xs text-muted">
                  {statusLabel(item.status)}
                  {item.last_sync_at ? ` · sist synk ${String(item.last_sync_at).slice(0, 10)}` : ""}
                </p>
                {!item.configured && item.provider === "google" && (
                  <p className="mt-2 text-xs text-amber-200">
                    Sett GOOGLE_CLIENT_ID og GOOGLE_CLIENT_SECRET i .env
                  </p>
                )}
              </div>
              <div className="flex shrink-0 flex-col gap-2">
                {item.status === "connected" ? (
                  <>
                    <button
                      type="button"
                      disabled={busy !== null}
                      onClick={() => handleSync(item.provider)}
                      className="rounded-lg bg-accent px-3 py-1.5 text-xs text-white disabled:opacity-60"
                    >
                      Synk til Inbox
                    </button>
                    <button
                      type="button"
                      disabled={busy !== null}
                      onClick={() => handleDisconnect(item.provider)}
                      className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted"
                    >
                      Koble fra
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    disabled={busy === item.provider || !item.configured}
                    onClick={() => handleConnect(item.provider, item.connect_type)}
                    className="rounded-lg bg-accent px-3 py-1.5 text-xs text-white disabled:opacity-60"
                  >
                    Koble til
                  </button>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>

      <p className="text-sm text-muted">
        Google sender kalender og uleste e-poster som{" "}
        <Link href="/inbox" className="text-accent">
          Inbox-signaler
        </Link>
        . Apple Health krever iPhone-app (PWA/Capacitor) for automatisk sync.
      </p>
    </div>
  );
}

export default function IntegrationsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted">Laster integrasjoner…</p>}>
      <IntegrationsPageInner />
    </Suspense>
  );
}
