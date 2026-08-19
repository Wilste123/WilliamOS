"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { ApiError, fetchOnboarding, skipOnboarding, submitOnboarding } from "@/lib/api";
import { getSession } from "@/lib/auth";
import { APP_NAME } from "@/lib/navigation";

const PRIMARY_USE_OPTIONS = [
  { value: "home", label: "Hjem og vedlikehold" },
  { value: "work", label: "Jobb og produktivitet" },
  { value: "finance", label: "Økonomi" },
  { value: "general", label: "Generelt" },
] as const;

const ASSET_OPTIONS = [
  { value: "bolig", label: "Bolig" },
  { value: "hytte", label: "Hytte" },
  { value: "båt", label: "Båt" },
  { value: "bil", label: "Bil" },
  { value: "annet", label: "Annet" },
] as const;

const STEPS = 4;

function OnboardingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const editMode = searchParams.get("edit") === "1";

  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [assistantName, setAssistantName] = useState(APP_NAME);
  const [primaryUse, setPrimaryUse] = useState("");
  const [assetsMentioned, setAssetsMentioned] = useState<string[]>([]);
  const [focusNow, setFocusNow] = useState("");

  useEffect(() => {
    if (!getSession()) {
      router.replace("/login");
      return;
    }
    fetchOnboarding()
      .then((state) => {
        if (state.assistant_name) setAssistantName(state.assistant_name);
        if (state.primary_use) setPrimaryUse(state.primary_use);
        if (state.assets_mentioned?.length) setAssetsMentioned(state.assets_mentioned);
        if (state.focus_now) setFocusNow(state.focus_now);
        if (state.onboarding_completed && !editMode) {
          router.replace("/home");
        }
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, [editMode, router]);

  function toggleAsset(value: string) {
    setAssetsMentioned((prev) =>
      prev.includes(value) ? prev.filter((a) => a !== value) : [...prev, value]
    );
  }

  async function handleSkip() {
    setSubmitting(true);
    setError(null);
    try {
      await skipOnboarding();
      router.replace("/home");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Noe gikk galt");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFinish() {
    setSubmitting(true);
    setError(null);
    try {
      await submitOnboarding({
        assistant_name: assistantName.trim() || undefined,
        primary_use: primaryUse || undefined,
        assets_mentioned: assetsMentioned,
        focus_now: focusNow.trim() || undefined,
      });
      router.replace("/home");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Noe gikk galt");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted">
        Laster…
      </div>
    );
  }

  return (
    <div className="flex min-h-dvh flex-col px-4 pb-8 pt-[calc(1rem+env(safe-area-inset-top))]">
      <div className="mx-auto w-full max-w-md flex-1 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">
              {editMode ? "Oppdater AI-profil" : "Velkommen"}
            </h1>
            <p className="text-sm text-muted">
              {editMode
                ? "Endre hva assistenten vet om deg"
                : "Hjelp assistenten å forstå deg bedre"}
            </p>
          </div>
          {!editMode && (
            <button
              type="button"
              onClick={handleSkip}
              disabled={submitting}
              className="text-sm text-muted"
            >
              Hopp over
            </button>
          )}
        </div>

        <div className="flex gap-2">
          {Array.from({ length: STEPS }).map((_, i) => (
            <div
              key={i}
              className={`h-1 flex-1 rounded-full ${i <= step ? "bg-accent" : "bg-border"}`}
            />
          ))}
        </div>

        <div className="space-y-4 rounded-2xl border border-border p-5">
          {step === 0 && (
            <label className="block space-y-2 text-sm">
              <span>Hva skal assistenten hete?</span>
              <input
                value={assistantName}
                onChange={(e) => setAssistantName(e.target.value)}
                className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
                placeholder={APP_NAME}
              />
            </label>
          )}

          {step === 1 && (
            <fieldset className="space-y-2 text-sm">
              <legend>Hva vil du bruke appen mest til?</legend>
              <div className="space-y-2 pt-2">
                {PRIMARY_USE_OPTIONS.map((opt) => (
                  <label
                    key={opt.value}
                    className={`flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-3 ${
                      primaryUse === opt.value ? "border-accent bg-accent/10" : "border-border"
                    }`}
                  >
                    <input
                      type="radio"
                      name="primary_use"
                      value={opt.value}
                      checked={primaryUse === opt.value}
                      onChange={() => setPrimaryUse(opt.value)}
                      className="sr-only"
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            </fieldset>
          )}

          {step === 2 && (
            <fieldset className="space-y-2 text-sm">
              <legend>Hva vil du holde styr på?</legend>
              <p className="text-muted">Velg én eller flere</p>
              <div className="flex flex-wrap gap-2 pt-2">
                {ASSET_OPTIONS.map((opt) => {
                  const selected = assetsMentioned.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => toggleAsset(opt.value)}
                      className={`rounded-full border px-4 py-2 text-sm ${
                        selected ? "border-accent bg-accent/15 text-accent" : "border-border"
                      }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </fieldset>
          )}

          {step === 3 && (
            <label className="block space-y-2 text-sm">
              <span>Hva er viktigst for deg akkurat nå?</span>
              <textarea
                value={focusNow}
                onChange={(e) => setFocusNow(e.target.value)}
                rows={4}
                maxLength={500}
                placeholder="F.eks. få styr på hytta før vinteren, eller holde oversikt over oppgaver…"
                className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
              />
            </label>
          )}

          {error && <p className="text-sm text-red-400">{error}</p>}

          <div className="flex gap-3 pt-2">
            {step > 0 && (
              <button
                type="button"
                onClick={() => setStep((s) => s - 1)}
                disabled={submitting}
                className="flex-1 rounded-xl border border-border px-4 py-3 text-sm"
              >
                Tilbake
              </button>
            )}
            {step < STEPS - 1 ? (
              <button
                type="button"
                onClick={() => setStep((s) => s + 1)}
                className="flex-1 rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white"
              >
                Neste
              </button>
            ) : (
              <button
                type="button"
                onClick={handleFinish}
                disabled={submitting}
                className="flex-1 rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
              >
                {submitting ? "Lagrer…" : editMode ? "Lagre" : "Kom i gang"}
              </button>
            )}
          </div>
        </div>

        {editMode && (
          <button
            type="button"
            onClick={() => router.replace("/settings")}
            className="w-full text-center text-sm text-muted"
          >
            Avbryt
          </button>
        )}
      </div>
    </div>
  );
}

export default function OnboardingPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-dvh items-center justify-center text-muted">
          Laster…
        </div>
      }
    >
      <OnboardingContent />
    </Suspense>
  );
}
