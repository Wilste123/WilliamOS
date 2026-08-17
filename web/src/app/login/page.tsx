"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiError, login, signup } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "");
    const password = String(form.get("password") ?? "");

    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await signup({
          email,
          password,
          display_name: String(form.get("display_name") ?? ""),
          household_name: String(form.get("household_name") ?? "Min husholdning"),
        });
      }
      router.replace("/home");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Noe gikk galt";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-dvh flex-col justify-center px-4">
      <div className="mx-auto w-full max-w-md space-y-6">
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-semibold">WilliamOS</h1>
          <p className="text-sm text-muted">Din personlige Chief of Staff</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border border-border p-5">
          {mode === "signup" && (
            <>
              <label className="block space-y-1 text-sm">
                <span>Navn</span>
                <input
                  name="display_name"
                  required
                  className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
                />
              </label>
              <label className="block space-y-1 text-sm">
                <span>Husholdning</span>
                <input
                  name="household_name"
                  defaultValue="Min husholdning"
                  required
                  className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
                />
              </label>
            </>
          )}

          <label className="block space-y-1 text-sm">
            <span>E-post</span>
            <input
              name="email"
              type="email"
              required
              className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
            />
          </label>

          <label className="block space-y-1 text-sm">
            <span>Passord</span>
            <input
              name="password"
              type="password"
              minLength={8}
              required
              className="w-full rounded-xl border border-border bg-transparent px-3 py-3"
            />
          </label>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-accent px-4 py-3 font-medium text-white disabled:opacity-60"
          >
            {loading ? "Vent…" : mode === "login" ? "Logg inn" : "Opprett konto"}
          </button>
        </form>

        <p className="text-center text-sm text-muted">
          {mode === "login" ? "Ny bruker?" : "Har du konto?"}{" "}
          <button
            type="button"
            className="text-accent"
            onClick={() => setMode(mode === "login" ? "signup" : "login")}
          >
            {mode === "login" ? "Registrer deg" : "Logg inn"}
          </button>
        </p>

        <p className="text-center text-xs text-muted">
          Streamlit-prototypen kjører fortsatt parallelt.{" "}
          <Link href="http://localhost:8501" className="underline">
            Åpne lab
          </Link>
        </p>
      </div>
    </div>
  );
}
