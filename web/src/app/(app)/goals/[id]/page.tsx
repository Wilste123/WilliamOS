"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { ArrowLeft, Target } from "lucide-react";

import { ConfirmDeleteButton } from "@/components/ConfirmDeleteButton";
import {
  deleteRecord,
  fetchGoalDetail,
  updateGoal,
  type GoalDetail,
} from "@/lib/api";
import { GOAL_MODULES, goalModuleLabel, goalModuleNeedsLink, type GoalModule } from "@/lib/goal-modules";
import { entityRecordLabel } from "@/lib/project-links";
import { formatDate, statusLabel } from "@/lib/format";

export default function GoalDetailPage() {
  const params = useParams();
  const goalId = String(params.id ?? "");
  const [detail, setDetail] = useState<GoalDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: "",
    status: "active",
    next_step: "",
    progress: "0",
    module: "general" as GoalModule,
  });

  const load = useCallback(() => {
    if (!goalId) return;
    setLoading(true);
    fetchGoalDetail(goalId)
      .then((data) => {
        setDetail(data);
        const goal = data.goal;
        setForm({
          title: String(goal.title ?? ""),
          status: String(goal.status ?? "active"),
          next_step: String(goal.next_step ?? ""),
          progress: String(goal.progress ?? 0),
          module: (goal.module as GoalModule) ?? "general",
        });
        setError(false);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, [goalId]);

  useEffect(() => {
    load();
  }, [load]);

  async function onSave(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await updateGoal(goalId, {
        title: form.title.trim(),
        status: form.status,
        next_step: form.next_step.trim() || null,
        progress: Number(form.progress) || 0,
        module: form.module,
      });
      load();
    } finally {
      setSaving(false);
    }
  }

  if (loading && !detail) {
    return <p className="text-sm text-muted">Laster mål…</p>;
  }

  if (error || !detail) {
    return (
      <div className="space-y-4">
        <Link href="/goals" className="inline-flex items-center gap-2 text-sm text-accent">
          <ArrowLeft className="h-4 w-4" />
          Tilbake til mål
        </Link>
        <p className="text-sm text-red-400">Kunne ikke laste målet.</p>
      </div>
    );
  }

  const { goal, linked_record } = detail;

  return (
    <div className="space-y-4">
      <Link href="/goals" className="inline-flex items-center gap-2 text-sm text-accent">
        <ArrowLeft className="h-4 w-4" />
        Mål
      </Link>

      <header className="rounded-2xl border border-border bg-zinc-950/40 p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent/15 text-accent">
            <Target className="h-6 w-6" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-semibold">{String(goal.title)}</h1>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted">
              <span className="rounded-full bg-zinc-800 px-2.5 py-0.5">{goalModuleLabel(goal.module)}</span>
              <span className="rounded-full bg-zinc-800 px-2.5 py-0.5">{statusLabel(goal.status)}</span>
              {goal.target_date ? (
                <span className="rounded-full bg-zinc-800 px-2.5 py-0.5">
                  Frist {formatDate(goal.target_date)}
                </span>
              ) : null}
            </div>
            {linked_record && (
              <p className="mt-3 text-sm text-muted">
                Knyttet til:{" "}
                {goal.module === "asset" && linked_record.id ? (
                  <Link href={`/assets/${String(linked_record.id)}`} className="text-accent">
                    {entityRecordLabel(linked_record)}
                  </Link>
                ) : (
                  entityRecordLabel(linked_record)
                )}
              </p>
            )}
          </div>
          <ConfirmDeleteButton
            confirmMessage="Slette målet?"
            onConfirm={async () => {
              await deleteRecord(`/goals/${goalId}`);
              window.location.href = "/goals";
            }}
          />
        </div>
      </header>

      <form onSubmit={onSave} className="space-y-3 rounded-2xl border border-border p-4">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Rediger</h2>
        <input
          value={form.title}
          onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
          className="w-full rounded-xl border border-border bg-transparent px-3 py-3 text-sm"
        />
        <select
          value={form.module}
          onChange={(e) => setForm((prev) => ({ ...prev, module: e.target.value as GoalModule }))}
          className="w-full rounded-xl border border-border bg-transparent px-3 py-3 text-sm"
        >
          {GOAL_MODULES.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
        <select
          value={form.status}
          onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))}
          className="w-full rounded-xl border border-border bg-transparent px-3 py-3 text-sm"
        >
          <option value="active">Aktiv</option>
          <option value="paused">Pauset</option>
          <option value="completed">Fullført</option>
        </select>
        <input
          value={form.next_step}
          onChange={(e) => setForm((prev) => ({ ...prev, next_step: e.target.value }))}
          placeholder="Neste steg"
          className="w-full rounded-xl border border-border bg-transparent px-3 py-3 text-sm"
        />
        <input
          type="number"
          min={0}
          max={100}
          value={form.progress}
          onChange={(e) => setForm((prev) => ({ ...prev, progress: e.target.value }))}
          placeholder="Fremdrift %"
          className="w-full rounded-xl border border-border bg-transparent px-3 py-3 text-sm"
        />
        {goalModuleNeedsLink(form.module) && !linked_record && (
          <p className="text-xs text-muted">Modulkobling settes ved opprettelse. Opprett nytt mål for ny kobling.</p>
        )}
        <button
          type="submit"
          disabled={saving}
          className="rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          Lagre endringer
        </button>
      </form>
    </div>
  );
}
