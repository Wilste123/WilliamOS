"use client";

import { useCallback, useEffect, useState } from "react";

import { EditSheet } from "@/components/EditSheet";
import { TaskCard } from "@/components/TaskCard";
import { completeTask, fetchCollection, updateTask } from "@/lib/api";

type TaskListProps = {
  refreshKey?: number;
  emptyLabel?: string;
};

export function TaskList({
  refreshKey = 0,
  emptyLabel = "Ingen oppgaver ennå.",
}: TaskListProps) {
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [editing, setEditing] = useState<Record<string, unknown> | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    fetchCollection("/tasks")
      .then((data) => {
        const openFirst = [...data].sort((a, b) => {
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
  }, []);

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
