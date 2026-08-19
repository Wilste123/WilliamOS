"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, FolderKanban } from "lucide-react";

import { ConfirmDeleteButton } from "@/components/ConfirmDeleteButton";
import { CreateRecordForm } from "@/components/CreateRecordForm";
import { DetailTabs } from "@/components/DetailTabs";
import { DocumentList } from "@/components/DocumentList";
import { TaskList } from "@/components/TaskList";
import {
  deleteRecord,
  fetchCollection,
  fetchProjectDetail,
  linkProjectEntity,
  unlinkProjectLink,
  type ProjectDetail,
} from "@/lib/api";
import { entityRecordLabel, PROJECT_LINK_TYPES, projectLinkTypeLabel } from "@/lib/project-links";
import { formatDate, statusLabel } from "@/lib/format";

type TabId = "tasks" | "documents" | "goals" | "finance" | "links";

const TABS: { id: TabId; label: string }[] = [
  { id: "tasks", label: "Oppgaver" },
  { id: "documents", label: "Dokumenter" },
  { id: "goals", label: "Mål" },
  { id: "finance", label: "Økonomi" },
  { id: "links", label: "Koblinger" },
];

const LINK_LOADERS: Record<string, () => Promise<Record<string, unknown>[]>> = {
  asset: () => fetchCollection("/assets"),
  goal: () => fetchCollection("/goals"),
  task: () => fetchCollection("/tasks"),
  document: () => fetchCollection("/documents"),
  finance_account: () => fetchCollection("/finance/accounts").catch(() => []),
  decision: () => fetchCollection("/decisions"),
};

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = String(params.id ?? "");
  const [detail, setDetail] = useState<ProjectDetail | null>(null);
  const [tab, setTab] = useState<TabId>("tasks");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const load = useCallback(() => {
    if (!projectId) return;
    setLoading(true);
    fetchProjectDetail(projectId)
      .then((data) => {
        setDetail(data);
        setLoading(false);
        setError(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  if (loading && !detail) {
    return <p className="text-sm text-muted">Laster prosjekt…</p>;
  }

  if (error || !detail) {
    return (
      <div className="space-y-4">
        <Link href="/projects" className="inline-flex items-center gap-2 text-sm text-accent">
          <ArrowLeft className="h-4 w-4" />
          Tilbake til prosjekter
        </Link>
        <p className="text-sm text-red-400">Kunne ikke laste prosjektet.</p>
      </div>
    );
  }

  const { project, links, goals, finance_accounts, events } = detail;
  const name = String(project.name ?? "Prosjekt");

  return (
    <div className="space-y-4">
      <Link href="/projects" className="inline-flex items-center gap-2 text-sm text-accent">
        <ArrowLeft className="h-4 w-4" />
        Prosjekter
      </Link>

      <header className="rounded-2xl border border-border bg-zinc-950/40 p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent/15 text-accent">
            <FolderKanban className="h-6 w-6" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-semibold">{name}</h1>
            <p className="mt-2 text-sm text-muted">
              {statusLabel(project.status)}
              {project.next_action ? ` · ${String(project.next_action)}` : ""}
            </p>
            {project.notes != null && String(project.notes) !== "" && (
              <p className="mt-3 text-sm text-muted">{String(project.notes)}</p>
            )}
          </div>
          <ConfirmDeleteButton
            confirmMessage="Slette prosjektet?"
            onConfirm={async () => {
              await deleteRecord(`/projects/${projectId}`);
              window.location.href = "/projects";
            }}
          />
        </div>
      </header>

      <DetailTabs tabs={TABS} active={tab} onChange={setTab} />

      {tab === "tasks" && (
        <section className="space-y-4">
          <CreateRecordForm
            path="/tasks"
            submitLabel="Opprett oppgave i prosjektet"
            showVisibility
            extraPayload={{ project_id: projectId }}
            fields={[
              { name: "title", label: "Tittel", type: "text", required: true, placeholder: "Hva skal gjøres?" },
              { name: "due_date", label: "Frist", type: "date" },
            ]}
            onCreated={() => setRefreshKey((key) => key + 1)}
          />
          <TaskList
            projectId={projectId}
            refreshKey={refreshKey}
            emptyLabel="Ingen oppgaver i prosjektet ennå."
          />
        </section>
      )}

      {tab === "documents" && (
        <DocumentList projectId={projectId} refreshKey={refreshKey} emptyLabel="Ingen dokumenter ennå." />
      )}

      {tab === "goals" && (
        <section className="space-y-3">
          {goals.length === 0 ? (
            <p className="text-sm text-muted">Ingen mål koblet via project_links ennå.</p>
          ) : (
            goals.map((goal) => (
              <Link
                key={String(goal.id)}
                href={`/goals/${String(goal.id)}`}
                className="block rounded-xl border border-border bg-zinc-950/30 px-4 py-3"
              >
                <p className="font-medium">{String(goal.title)}</p>
                <p className="mt-1 text-xs text-muted">{statusLabel(goal.status)}</p>
              </Link>
            ))
          )}
        </section>
      )}

      {tab === "finance" && (
        <section className="space-y-3">
          {finance_accounts.length === 0 ? (
            <p className="text-sm text-muted">Ingen finanskontoer koblet ennå. Bruk Koblinger-fanen.</p>
          ) : (
            finance_accounts.map((account) => (
              <article key={String(account.id)} className="rounded-xl border border-border bg-zinc-950/30 px-4 py-3">
                <p className="font-medium">{String(account.name)}</p>
                <p className="mt-1 text-xs text-muted">{String(account.account_type)}</p>
              </article>
            ))
          )}
        </section>
      )}

      {tab === "links" && (
        <section className="space-y-4">
          <ProjectLinkForm
            projectId={projectId}
            onLinked={() => setRefreshKey((key) => key + 1)}
          />
          <div className="space-y-2">
            {links.length === 0 ? (
              <p className="text-sm text-muted">Ingen ekstra koblinger ennå.</p>
            ) : (
              links.map((link) => (
                <article
                  key={String(link.id)}
                  className="flex items-center justify-between rounded-xl border border-border px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-medium">{String(link.label ?? link.entity_id)}</p>
                    <p className="text-xs text-muted">{projectLinkTypeLabel(link.entity_type)}</p>
                  </div>
                  <ConfirmDeleteButton
                    confirmMessage="Fjerne koblingen?"
                    onConfirm={async () => {
                      await unlinkProjectLink(projectId, String(link.id));
                      setRefreshKey((key) => key + 1);
                    }}
                  />
                </article>
              ))
            )}
          </div>
        </section>
      )}

      {events.length > 0 && (
        <section className="space-y-2 rounded-2xl border border-border p-4">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Historikk</h2>
          {events.slice(0, 5).map((event) => (
            <article key={String(event.id)} className="rounded-xl bg-zinc-900/60 px-3 py-2 text-sm">
              <p>{String(event.title)}</p>
              <p className="text-xs text-muted">{formatDate(event.created_at)}</p>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}

function ProjectLinkForm({
  projectId,
  onLinked,
}: {
  projectId: string;
  onLinked: () => void;
}) {
  const [entityType, setEntityType] = useState(PROJECT_LINK_TYPES[0].value);
  const [entityId, setEntityId] = useState("");
  const [options, setOptions] = useState<Record<string, unknown>[]>([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const loader = LINK_LOADERS[entityType];
    if (!loader) return;
    loader().then(setOptions).catch(() => setOptions([]));
    setEntityId("");
  }, [entityType]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!entityId) return;
    setSubmitting(true);
    try {
      await linkProjectEntity(projectId, entityType, entityId);
      setEntityId("");
      onLinked();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-border p-4">
      <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Knytt til…</h2>
      <select
        value={entityType}
        onChange={(e) => setEntityType(e.target.value as typeof entityType)}
        className="w-full rounded-xl border border-border bg-transparent px-3 py-3 text-sm"
      >
        {PROJECT_LINK_TYPES.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
      <select
        value={entityId}
        onChange={(e) => setEntityId(e.target.value)}
        className="w-full rounded-xl border border-border bg-transparent px-3 py-3 text-sm"
      >
        <option value="">Velg…</option>
        {options.map((option) => (
          <option key={String(option.id)} value={String(option.id)}>
            {entityRecordLabel(option)}
          </option>
        ))}
      </select>
      <button
        type="submit"
        disabled={submitting || !entityId}
        className="rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        Legg til kobling
      </button>
    </form>
  );
}
