"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchMe } from "@/lib/api";
import { getSession, logout } from "@/lib/auth";
import { BottomNav } from "@/components/BottomNav";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [displayName, setDisplayName] = useState<string | null>(null);

  useEffect(() => {
    const session = getSession();
    if (!session) {
      router.replace("/login");
      return;
    }

    fetchMe()
      .then((me) => {
        setDisplayName(me.display_name ?? me.email);
        setReady(true);
      })
      .catch(() => {
        logout();
        router.replace("/login");
      });
  }, [router]);

  if (!ready) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted">
        Laster…
      </div>
    );
  }

  return (
    <div className="min-h-dvh pb-24">
      <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur px-4 py-3">
        <div className="mx-auto flex max-w-lg items-center justify-between">
          <div>
            <p className="text-sm text-muted">WilliamOS</p>
            <p className="font-medium">{displayName}</p>
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
      <main className="mx-auto max-w-lg px-4 py-4">{children}</main>
      <BottomNav />
    </div>
  );
}
