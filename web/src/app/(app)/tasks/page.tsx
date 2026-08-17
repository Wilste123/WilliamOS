"use client";

import { useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { TaskList } from "@/components/TaskList";

export default function TasksPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Oppgaver</h1>
        <p className="text-sm text-muted">Opprett, fullfør og rediger oppgaver.</p>
      </div>

      <CreateRecordForm
        path="/tasks"
        submitLabel="Opprett oppgave"
        fields={[
          { name: "title", label: "Tittel", type: "text", required: true, placeholder: "Hva skal gjøres?" },
          { name: "due_date", label: "Frist", type: "date" },
        ]}
        onCreated={() => setRefreshKey((key) => key + 1)}
      />

      <TaskList
        refreshKey={refreshKey}
        emptyLabel="Ingen oppgaver ennå. Opprett den første over."
      />
    </div>
  );
}
