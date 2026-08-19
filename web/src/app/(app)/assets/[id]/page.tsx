"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Package } from "lucide-react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { DocumentList } from "@/components/DocumentList";
import { DocumentUploadForm } from "@/components/DocumentUploadForm";
import { TaskList } from "@/components/TaskList";
import { fetchAssetDetail, type AssetDetail } from "@/lib/api";
import { assetTypeLabel } from "@/lib/asset-types";
import { formatDate, formatNok, statusLabel } from "@/lib/format";

type TabId = "tasks" | "projects" | "documents" | "timeline";

const TABS: { id: TabId; label: string }[] = [
  { id: "tasks", label: "Oppgaver" },
  { id: "projects", label: "Prosjekter" },
  { id: "documents", label: "Dokumenter" },
  { id: "timeline", label: "Historikk" },
];

export default function AssetDetailPage() {
  const params = useParams();
  const assetId = String(params.id ?? "");
  const [detail, setDetail] = useState<AssetDetail | null>(null);
  const [tab, setTab] = useState<TabId>("tasks");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const load = useCallback(() => {
    if (!assetId) return;
    setLoading(true);
    setError(false);
    fetchAssetDetail(assetId)
      .then((data) => {
        setDetail(data);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, [assetId]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  if (loading && !detail) {
    return <p className="text-sm text-muted">Laster eiendel…</p>;
  }

  if (error || !detail) {
    return (
      <div className="space-y-4">
        <Link href="/assets" className="inline-flex items-center gap-2 text-sm text-accent">
          <ArrowLeft className="h-4 w-4" />
          Tilbake til eiendeler
        </Link>
        <p className="text-sm text-red-400">Kunne ikke laste eiendelen.</p>
      </div>
    );
  }

  const { asset, projects, events } = detail;
  const name = String(asset.name ?? "Uten navn");

  return (
    <div className="space-y-4">
      <Link href="/assets" className="inline-flex items-center gap-2 text-sm text-accent">
        <ArrowLeft className="h-4 w-4" />
        Eiendeler
      </Link>

      <header className="rounded-2xl border border-border bg-zinc-950/40 p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent/15 text-accent">
            <Package className="h-6 w-6" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-semibold">{name}</h1>
            <div className="mt-2 flex flex-wrap gap-2">
              {asset.type != null && asset.type !== "" && (
                <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-muted">
                  {assetTypeLabel(asset.type)}
                </span>
              )}
              <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-muted">
                {statusLabel(asset.status)}
              </span>
              <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs text-emerald-300">
                {formatNok(asset.estimated_value)}
              </span>
            </div>
            {asset.description != null && String(asset.description) !== "" && (
              <p className="mt-3 text-sm text-muted">{String(asset.description)}</p>
            )}
          </div>
        </div>
      </header>

      <div className="flex gap-2 overflow-x-auto">
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setTab(item.id)}
            className={`shrink-0 rounded-full px-4 py-2 text-sm ${
              tab === item.id
                ? "bg-accent text-white"
                : "border border-border text-muted hover:text-foreground"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === "tasks" && (
        <section className="space-y-4">
          <CreateRecordForm
            path="/tasks"
            submitLabel="Opprett oppgave for eiendelen"
            extraPayload={{ asset_id: assetId }}
            fields={[
              {
                name: "title",
                label: "Tittel",
                type: "text",
                required: true,
                placeholder: "Hva skal gjøres?",
              },
              { name: "due_date", label: "Frist", type: "date" },
            ]}
            onCreated={() => setRefreshKey((key) => key + 1)}
          />
          <TaskList
            assetId={assetId}
            refreshKey={refreshKey}
            emptyLabel="Ingen oppgaver knyttet til denne eiendelen ennå."
          />
        </section>
      )}

      {tab === "projects" && (
        <section className="space-y-3">
          {projects.length === 0 ? (
            <p className="text-sm text-muted">Ingen prosjekter knyttet til denne eiendelen.</p>
          ) : (
            projects.map((project) => (
              <Link
                key={String(project.id)}
                href={`/projects/${String(project.id)}`}
                className="block rounded-xl border border-border bg-zinc-950/30 px-4 py-3"
              >
                <p className="font-medium">{String(project.name ?? "Prosjekt")}</p>
                <p className="mt-1 text-xs text-muted">
                  {statusLabel(project.status)}
                  {project.next_action ? ` · ${String(project.next_action)}` : ""}
                </p>
              </Link>
            ))
          )}
        </section>
      )}

      {tab === "documents" && (
        <section className="space-y-4">
          <DocumentUploadForm
            assetId={assetId}
            onUploaded={() => setRefreshKey((key) => key + 1)}
          />
          <DocumentList
            assetId={assetId}
            refreshKey={refreshKey}
            emptyLabel="Ingen dokumenter ennå."
          />
        </section>
      )}

      {tab === "timeline" && (
        <section className="space-y-3">
          {events.length === 0 ? (
            <p className="text-sm text-muted">Ingen hendelser ennå.</p>
          ) : (
            events.map((event) => (
              <article
                key={String(event.id)}
                className="rounded-xl border border-border bg-zinc-950/30 px-4 py-3"
              >
                <p className="font-medium">{String(event.title ?? "Hendelse")}</p>
                <p className="mt-1 text-xs text-muted">
                  {String(event.event_type ?? "")} · {formatDate(event.created_at)}
                </p>
                {event.notes != null && String(event.notes) !== "" && (
                  <p className="mt-2 text-sm text-muted">{String(event.notes)}</p>
                )}
              </article>
            ))
          )}
        </section>
      )}
    </div>
  );
}
