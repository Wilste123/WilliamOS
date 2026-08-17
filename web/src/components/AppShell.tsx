"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { AppNav } from "@/components/AppNav";
import { BottomNav } from "@/components/BottomNav";
import { ApiError, fetchMe, recordAppOpen } from "@/lib/api";
import { getSession, logout, type AuthSession } from "@/lib/auth";
import { APP_NAME, isHiddenRoute } from "@/lib/navigation";

const BOOT_TIMEOUT_MS = 12_000;

type BootState = "loading" | "ready" | "redirecting" | "error";

function sessionDisplayName(session: AuthSession | null): string | null {
  if (!session) return null;
  return session.display_name ?? session.email ?? null;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const session = getSession();
  const [bootState, setBootState] = useState<BootState>(() =>
    session ? "ready" : "loading"
  );
  const [displayName, setDisplayName] = useState<string | null>(() =>
    sessionDisplayName(session)
  );
  const [bootError, setBootError] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const hiddenLabRoute = isHiddenRoute(pathname);
  const bootStartedRef = useRef(false);
  const usageLoggedRef = useRef(false);

  useEffect(() => {
    if (bootStartedRef.current) return;
    bootStartedRef.current = true;

    let cancelled = false;

    async function boot() {
      const currentSession = getSession();
      if (!currentSession) {
        setBootState("redirecting");
        router.replace("/login");
        return;
      }

      const timeout = new Promise<never>((_, reject) => {
        window.setTimeout(() => {
          reject(
            new ApiError(
              "Backend svarte ikke i tide. Sjekk at FastAPI kjører på port 8000.",
              0
            )
          );
        }, BOOT_TIMEOUT_MS);
      });

      try {
        const me = await Promise.race([fetchMe(), timeout]);
        if (cancelled) return;
        setDisplayName(me.display_name ?? me.email);
        setBootState("ready");
        if (!usageLoggedRef.current) {
          usageLoggedRef.current = true;
          recordAppOpen().catch(() => undefined);
        }
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
          logout();
          setBootState("redirecting");
          router.replace("/login");
          return;
        }
        // Keep shell visible if we already had a cached session — show inline error instead.
        if (currentSession) {
          setBootError(
            err instanceof ApiError
              ? err.message
              : "Kunne ikke nå backend. Noen data kan være utdatert."
          );
          setBootState("ready");
          return;
        }
        setBootError(
          err instanceof ApiError
            ? err.message
            : "Kunne ikke starte appen. Sjekk at backend kjører."
        );
        setBootState("error");
      }
    }

    boot();
    return () => {
      cancelled = true;
    };
    // Boot once per mount; optimistic "ready" state avoids flash on navigation remounts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (bootState === "redirecting") {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted">
        Omdirigerer…
      </div>
    );
  }

  if (bootState === "error") {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="text-sm text-red-400">{bootError}</p>
        <div className="flex flex-wrap justify-center gap-2">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded-xl border border-border px-4 py-2 text-sm"
          >
            Prøv igjen
          </button>
          <button
            type="button"
            onClick={() => {
              logout();
              router.replace("/login");
            }}
            className="rounded-xl bg-accent px-4 py-2 text-sm text-white"
          >
            Logg inn på nytt
          </button>
        </div>
      </div>
    );
  }

  if (bootState !== "ready") {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted">
        Laster…
      </div>
    );
  }

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="hidden border-r border-border bg-zinc-950/40 lg:block">
        <div className="sticky top-0 flex h-dvh flex-col p-4">
          <div className="mb-4 px-3">
            <p className="text-sm text-muted">{APP_NAME}</p>
            <p className="font-medium">{displayName}</p>
          </div>
          <div className="flex-1 overflow-y-auto">
            <AppNav />
          </div>
          <button
            type="button"
            onClick={() => {
              logout();
              router.replace("/login");
            }}
            className="mt-4 rounded-xl border border-border px-3 py-2 text-sm"
          >
            Logg ut
          </button>
        </div>
      </aside>

      <div className="min-h-dvh">
        <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur px-4 py-3 lg:hidden">
          <div className="flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => setMenuOpen(true)}
              className="rounded-lg border border-border px-3 py-2 text-sm"
            >
              Meny
            </button>
            <div className="min-w-0 flex-1 text-right">
              <p className="truncate text-sm text-muted">{APP_NAME}</p>
              <p className="truncate font-medium">{displayName}</p>
            </div>
            <button
              type="button"
              onClick={() => {
                logout();
                router.replace("/login");
              }}
              className="rounded-lg border border-border px-3 py-2 text-sm"
            >
              Logg ut
            </button>
          </div>
        </header>

        {menuOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <button
              type="button"
              aria-label="Lukk meny"
              className="absolute inset-0 bg-black/60"
              onClick={() => setMenuOpen(false)}
            />
            <div className="absolute inset-y-0 left-0 w-[min(88vw,320px)] border-r border-border bg-background p-4">
              <div className="mb-4 flex items-center justify-between px-3">
                <p className="font-medium">Navigasjon</p>
                <button
                  type="button"
                  onClick={() => setMenuOpen(false)}
                  className="rounded-lg border border-border px-2 py-1 text-sm"
                >
                  Lukk
                </button>
              </div>
              <AppNav onNavigate={() => setMenuOpen(false)} />
            </div>
          </div>
        )}

        <main className="mx-auto max-w-3xl px-4 py-4 pb-28 lg:pb-4">
          {bootError && (
            <p className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
              {bootError}
            </p>
          )}
          {hiddenLabRoute && (
            <p className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
              Lab-modul (skjult i MVP). Denne siden er ikke en del av test-appen ennå.
            </p>
          )}
          {children}
        </main>
        <BottomNav onOpenMenu={() => setMenuOpen(true)} />
      </div>
    </div>
  );
}
