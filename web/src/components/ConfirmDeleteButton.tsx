"use client";

import { Trash2 } from "lucide-react";
import { useState } from "react";

type ConfirmDeleteButtonProps = {
  label?: string;
  confirmMessage: string;
  onConfirm: () => Promise<void>;
  className?: string;
};

export function ConfirmDeleteButton({
  label = "Slett",
  confirmMessage,
  onConfirm,
  className = "",
}: ConfirmDeleteButtonProps) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  async function handleDelete() {
    setBusy(true);
    try {
      await onConfirm();
      setConfirming(false);
    } finally {
      setBusy(false);
    }
  }

  if (confirming) {
    return (
      <div className={`flex flex-wrap items-center gap-2 ${className}`}>
        <span className="text-xs text-muted">{confirmMessage}</span>
        <button
          type="button"
          disabled={busy}
          onClick={handleDelete}
          className="rounded-lg bg-red-500/20 px-2.5 py-1 text-xs text-red-300 disabled:opacity-50"
        >
          {busy ? "Sletter…" : "Bekreft"}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => setConfirming(false)}
          className="rounded-lg border border-border px-2.5 py-1 text-xs text-muted"
        >
          Avbryt
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      aria-label={label}
      onClick={() => setConfirming(true)}
      className={`rounded-lg border border-border p-2 text-muted hover:border-red-500/40 hover:text-red-300 ${className}`}
    >
      <Trash2 className="h-4 w-4" />
    </button>
  );
}
