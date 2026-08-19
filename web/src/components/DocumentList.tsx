"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ConfirmDeleteButton } from "@/components/ConfirmDeleteButton";
import {
  analyzeDocument,
  deleteDocument,
  downloadDocumentFile,
  fetchCollection,
  fetchDocumentPreviewBlob,
} from "@/lib/api";
import { formatDate } from "@/lib/format";

type DocumentListProps = {
  refreshKey?: number;
  assetId?: string;
  projectId?: string;
  emptyLabel?: string;
};

function isPreviewable(filename: string): boolean {
  const lower = filename.toLowerCase();
  return lower.endsWith(".pdf") || /\.(png|jpe?g|gif|webp)$/i.test(lower);
}

export function DocumentList({
  refreshKey = 0,
  assetId,
  projectId,
  emptyLabel = "Ingen dokumenter ennå.",
}: DocumentListProps) {
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewTitle, setPreviewTitle] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    fetchCollection("/documents")
      .then((data) => {
        const filtered = data.filter((doc) => {
          if (assetId && String(doc.asset_id ?? "") !== assetId) return false;
          if (projectId && String(doc.project_id ?? "") !== projectId) return false;
          return true;
        });
        setItems(filtered);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, [assetId, projectId]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  async function handlePreview(doc: Record<string, unknown>) {
    const id = String(doc.id);
    const filename = String(doc.filename ?? "dokument");
    setBusyId(id);
    try {
      const blob = await fetchDocumentPreviewBlob(id);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      setPreviewTitle(filename);
    } finally {
      setBusyId(null);
    }
  }

  async function handleAnalyze(doc: Record<string, unknown>) {
    const id = String(doc.id);
    setBusyId(id);
    try {
      await analyzeDocument(id);
      load();
    } finally {
      setBusyId(null);
    }
  }

  if (loading && items.length === 0) {
    return <p className="text-sm text-muted">Laster…</p>;
  }

  return (
    <>
      {error && <p className="text-sm text-red-400">Kunne ikke laste data.</p>}
      <div className="space-y-3">
        {items.map((doc) => {
          const id = String(doc.id);
          const filename = String(doc.filename ?? "Dokument");
          const canPreview = isPreviewable(filename);
          return (
            <article
              key={id}
              className="flex flex-col gap-3 rounded-2xl border border-border p-4 sm:flex-row sm:items-start sm:justify-between"
            >
              <div className="min-w-0 space-y-1">
                <p className="truncate font-medium">{filename}</p>
                <p className="text-sm text-muted">
                  {String(doc.source_module ?? "documents")} · {formatDate(doc.created_at) ?? "—"}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {canPreview && (
                  <button
                    type="button"
                    disabled={busyId === id}
                    onClick={() => handlePreview(doc)}
                    className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted hover:text-foreground disabled:opacity-60"
                  >
                    Vis
                  </button>
                )}
                <button
                  type="button"
                  disabled={busyId === id}
                  onClick={() => downloadDocumentFile(id, filename)}
                  className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted hover:text-foreground disabled:opacity-60"
                >
                  Last ned
                </button>
                <button
                  type="button"
                  disabled={busyId === id}
                  onClick={() => handleAnalyze(doc)}
                  className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted hover:text-foreground disabled:opacity-60"
                >
                  Analyser
                </button>
                <Link
                  href={`/chat?document_id=${encodeURIComponent(id)}&prompt=${encodeURIComponent(`Analyser dokumentet «${filename}»`)}&send=1`}
                  className="rounded-lg bg-accent/15 px-3 py-1.5 text-xs text-accent hover:bg-accent/25"
                >
                  Chat
                </Link>
                <ConfirmDeleteButton
                  confirmMessage="Slette dokumentet?"
                  onConfirm={async () => {
                    await deleteDocument(id);
                    load();
                  }}
                />
              </div>
            </article>
          );
        })}
        {!error && items.length === 0 && <p className="text-sm text-muted">{emptyLabel}</p>}
      </div>

      {previewUrl && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-4 sm:items-center">
          <div className="flex max-h-[90vh] w-full max-w-4xl flex-col rounded-2xl border border-border bg-background">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <p className="truncate text-sm font-medium">{previewTitle}</p>
              <button
                type="button"
                onClick={() => {
                  URL.revokeObjectURL(previewUrl);
                  setPreviewUrl(null);
                  setPreviewTitle("");
                }}
                className="text-sm text-muted"
              >
                Lukk
              </button>
            </div>
            <div className="min-h-[50vh] flex-1 overflow-hidden p-2">
              {previewTitle.toLowerCase().endsWith(".pdf") ? (
                <iframe src={previewUrl} title={previewTitle} className="h-[70vh] w-full rounded-lg" />
              ) : (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={previewUrl} alt={previewTitle} className="mx-auto max-h-[70vh] rounded-lg object-contain" />
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
