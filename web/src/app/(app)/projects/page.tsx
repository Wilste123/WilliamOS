"use client";

import { useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { RecordListPage } from "@/components/RecordListPage";

export default function ProjectsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <RecordListPage
      title="Prosjekter"
      description="Aktive og avsluttede prosjekter — åpne for å knytte oppgaver, dokumenter og mål."
      path="/projects"
      fields={["name", "status", "next_action"]}
      refreshKey={refreshKey}
      deletable
      deleteConfirmMessage="Slette prosjektet?"
      itemHref={(item) => (item.id ? `/projects/${String(item.id)}` : undefined)}
    >
      <CreateRecordForm
        path="/projects"
        submitLabel="Opprett prosjekt"
        showVisibility
        fields={[
          { name: "name", label: "Navn", type: "text", required: true, placeholder: "Hva jobber du med?" },
          { name: "next_action", label: "Neste handling", type: "text", placeholder: "Neste steg" },
        ]}
        onCreated={() => setRefreshKey((key) => key + 1)}
      />
    </RecordListPage>
  );
}
