"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { AppNav } from "@/components/AppNav";
import { BottomNav } from "@/components/BottomNav";
import { ApiError, fetchMe, recordAppOpen } from "@/lib/api";
import { logout } from "@/lib/auth";
import { APP_NAME, isHiddenRoute } from "@/lib/navigation";
import { useClientSession, useIsClient } from "@/lib/use-client-session";

const BOOT_TIMEOUT_MS = 12_000;

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const isClient = useIsClient();
  const session = useClientSession();
  const [bootError, setBootError] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const hiddenLabRoute = isHiddenRoute(pathname);
  const usageLoggedRef = useRef(false);
  const validatedTokenRef = useRef<string | null>(null);

  useEffect(() => {
    if (!isClient) return;

    if (!session) {
      validatedTokenRef.current = null;
      setAuthReady(false);
      router.replace("/login");
      return;
    }

    if (validatedTokenRef.current === session.access_token && authReady) return;
    validatedTokenRef.current = session.access_token;
    setAuthReady(false);

    let cancelled = false;
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

    Promise.race([fetchMe(), timeout])
      .then(() => {
        if (cancelled) return;
        setAuthReady(true);
        setBootError(null);
        if (!usageLoggedRef.current) {
          usageLoggedRef.current = true;
          recordAppOpen().catch(() => undefined);
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setAuthReady(false);
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
          validatedTokenRef.current = null;
          logout();
          router.replace("/login");
          return;
        }
        setBootError(
          err instanceof ApiError
            ? err.message
            : "Kunne ikke nå backend. Noen data kan være utdatert."
        );
      });

    return () => {
      cancelled = true;
    };
  }, [isClient, session, router, authReady]);

  if (!isClient) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted">
        Laster…
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted">
        Omdirigerer…
      </div>
    );
  }

  if (!authReady) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted">
        Validerer session…
      </div>
    );
  }

  const displayName = session.display_name ?? session.email;

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
              Intern utviklerside — ikke en del av produkt-UI.
            </p>
          )}
          {children}
        </main>
        <BottomNav onOpenMenu={() => setMenuOpen(true)} />
      </div>
    </div>
  );
}
