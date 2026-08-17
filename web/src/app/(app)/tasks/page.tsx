"use client";

import { useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { RecordListPage } from "@/components/RecordListPage";

export default function TasksPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <RecordListPage
      title="Oppgaver"
      description="Alle oppgaver i systemet."
      path="/tasks/"
      fields={["title", "priority", "due_date", "status"]}
      emptyLabel="Ingen oppgaver ennå. Opprett den første over."
      refreshKey={refreshKey}
    >
      <CreateRecordForm
        path="/tasks/"
        submitLabel="Opprett oppgave"
        fields={[
          { name: "title", label: "Tittel", type: "text", required: true, placeholder: "Hva skal gjøres?" },
          { name: "due_date", label: "Frist", type: "date" },
        ]}
        onCreated={() => setRefreshKey((key) => key + 1)}
      />
    </RecordListPage>
  );
}
