"use client";

import Link from "next/link";
import { Check, Pencil } from "lucide-react";

import { ConfirmDeleteButton } from "@/components/ConfirmDeleteButton";
import { formatDate, priorityLabel, priorityTone, statusLabel } from "@/lib/format";

type TaskCardProps = {
  task: Record<string, unknown>;
  onComplete: () => void;
  onEdit: () => void;
  onDelete?: () => Promise<void>;
  assetName?: string;
  completing?: boolean;
};

export function TaskCard({ task, onComplete, onEdit, onDelete, assetName, completing }: TaskCardProps) {
  const completed = Boolean(task.completed) || task.status === "completed";
  const title = String(task.title ?? "Uten tittel");
  const due = formatDate(task.due_date);
  const assetId = task.asset_id ? String(task.asset_id) : "";

  return (
    <article
      className={`rounded-2xl border border-border p-4 transition ${
        completed ? "opacity-60" : "bg-zinc-950/40"
      }`}
    >
      <div className="flex items-start gap-3">
        <button
          type="button"
          disabled={completed || completing}
          onClick={onComplete}
          aria-label="Fullfør oppgave"
          className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${
            completed
              ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
              : "border-border hover:border-accent hover:text-accent"
          } disabled:opacity-50`}
        >
          <Check className="h-4 w-4" />
        </button>
        <div className="min-w-0 flex-1">
          <p className={`font-medium ${completed ? "line-through" : ""}`}>{title}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className={`rounded-full px-2.5 py-0.5 text-xs ${priorityTone(task.priority)}`}>
              {priorityLabel(task.priority)}
            </span>
            {due && (
              <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-muted">
                Frist {due}
              </span>
            )}
            <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-muted">
              {statusLabel(task.status)}
            </span>
            {assetName && assetId && (
              <Link
                href={`/assets/${assetId}`}
                className="rounded-full bg-accent/10 px-2.5 py-0.5 text-xs text-accent"
              >
                {assetName}
              </Link>
            )}
          </div>
        </div>
        {!completed && (
          <div className="flex shrink-0 items-center gap-1">
            {onDelete && (
              <ConfirmDeleteButton
                confirmMessage="Slette oppgaven?"
                onConfirm={onDelete}
              />
            )}
            <button
              type="button"
              onClick={onEdit}
              aria-label="Rediger oppgave"
              className="rounded-lg border border-border p-2 text-muted hover:text-foreground"
            >
              <Pencil className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </article>
  );
}
