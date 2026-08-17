"use client";

import { useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { RecordListPage } from "@/components/RecordListPage";

export default function GoalsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <RecordListPage
      title="Mål"
      description="Aktive mål som mater inn i Priority Engine."
      path="/goals"
      fields={["title", "status", "next_step", "progress"]}
      emptyLabel="Ingen mål ennå."
      refreshKey={refreshKey}
    >
      <CreateRecordForm
        path="/goals"
        submitLabel="Opprett mål"
        fields={[
          { name: "title", label: "Tittel", type: "text", required: true, placeholder: "Hva vil du oppnå?" },
          { name: "next_step", label: "Neste steg", type: "text", placeholder: "Neste handling" },
          { name: "target_date", label: "Måldato", type: "date" },
        ]}
        onCreated={() => setRefreshKey((key) => key + 1)}
      />
    </RecordListPage>
  );
}
