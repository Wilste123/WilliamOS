"use client";

import { useCallback, useEffect, useState } from "react";

import { EditSheet } from "@/components/EditSheet";
import { TaskCard } from "@/components/TaskCard";
import { completeTask, deleteTask, fetchCollection, updateTask } from "@/lib/api";

type TaskListProps = {
  refreshKey?: number;
  emptyLabel?: string;
  assetId?: string;
  projectId?: string;
};

export function TaskList({
  refreshKey = 0,
  emptyLabel = "Ingen oppgaver ennå.",
  assetId,
  projectId,
}: TaskListProps) {
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [assetsById, setAssetsById] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [editing, setEditing] = useState<Record<string, unknown> | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    Promise.all([fetchCollection("/tasks"), fetchCollection("/assets")])
      .then(([tasks, assets]) => {
        const names: Record<string, string> = {};
        for (const asset of assets) {
          names[String(asset.id)] = String(asset.name ?? "Eiendel");
        }
        setAssetsById(names);
        const filtered = tasks.filter((task) => {
          if (assetId && String(task.asset_id ?? "") !== assetId) return false;
          if (projectId && String(task.project_id ?? "") !== projectId) return false;
          return true;
        });
        const openFirst = [...filtered].sort((a, b) => {
          const aDone = Boolean(a.completed) || a.status === "completed";
          const bDone = Boolean(b.completed) || b.status === "completed";
          if (aDone !== bDone) return aDone ? 1 : -1;
          return String(a.due_date ?? "9999").localeCompare(String(b.due_date ?? "9999"));
        });
        setItems(openFirst);
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

  async function handleComplete(task: Record<string, unknown>) {
    const id = String(task.id);
    setCompletingId(id);
    try {
      await completeTask(id);
      load();
    } finally {
      setCompletingId(null);
    }
  }

  async function handleSave(values: Record<string, unknown>) {
    if (!editing) return;
    await updateTask(String(editing.id), values);
    load();
  }

  if (loading && items.length === 0) {
    return <p className="text-sm text-muted">Laster…</p>;
  }

  return (
    <>
      {error && <p className="text-sm text-red-400">Kunne ikke laste data.</p>}
      <div className="space-y-3">
        {items.map((task) => (
          <TaskCard
            key={String(task.id)}
            task={task}
            completing={completingId === String(task.id)}
            onComplete={() => handleComplete(task)}
            onEdit={() => setEditing(task)}
            onDelete={async () => {
              await deleteTask(String(task.id));
              load();
            }}
            assetName={
              task.asset_id ? assetsById[String(task.asset_id)] : undefined
            }
          />
        ))}
        {!error && items.length === 0 && <p className="text-sm text-muted">{emptyLabel}</p>}
      </div>
      <EditSheet
        open={editing !== null}
        title="Rediger oppgave"
        initialValues={editing ?? {}}
        fields={[
          { name: "title", label: "Tittel", type: "text" },
          { name: "due_date", label: "Frist", type: "date" },
        ]}
        onClose={() => setEditing(null)}
        onSubmit={handleSave}
      />
    </>
  );
}
