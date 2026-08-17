"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef } from "react";

import { completeOutlookIntegration } from "@/lib/api";

function OutlookCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const handled = useRef(false);

  useEffect(() => {
    if (handled.current) return;
    handled.current = true;

    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const error = searchParams.get("error");

    if (error) {
      router.replace(`/integrations?error=${encodeURIComponent(error)}`);
      return;
    }
    if (!code || !state) {
      router.replace("/integrations?error=mangler_code_eller_state");
      return;
    }

    completeOutlookIntegration(code, state)
      .then(() => router.replace("/integrations?connected=outlook"))
      .catch((err) =>
        router.replace(
          `/integrations?error=${encodeURIComponent(err instanceof Error ? err.message : "outlook_feilet")}`
        )
      );
  }, [router, searchParams]);

  return <p className="text-sm text-muted">Kobler til Outlook…</p>;
}

export default function IntegrationsCallbackPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted">Laster…</p>}>
      <OutlookCallbackInner />
    </Suspense>
  );
}
