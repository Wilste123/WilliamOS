"use client";

import { useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { RecordListPage } from "@/components/RecordListPage";

export default function AssetsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <RecordListPage
      title="Eiendeler"
      description="Boliger, kjøretøy, båter og andre eiendeler."
      path="/assets/"
      fields={["name", "type", "status", "estimated_value"]}
      emptyLabel="Ingen eiendeler ennå. Opprett den første over — verdien vises på Hjem."
      refreshKey={refreshKey}
    >
      <CreateRecordForm
        path="/assets/"
        submitLabel="Opprett eiendel"
        extraPayload={{ status: "active" }}
        fields={[
          { name: "name", label: "Navn", type: "text", required: true, placeholder: "F.eks. Tun32, Mazda, båt" },
          {
            name: "estimated_value",
            label: "Estimert verdi (NOK)",
            type: "number",
            placeholder: "0",
            step: "1000",
          },
        ]}
        onCreated={() => setRefreshKey((key) => key + 1)}
      />
    </RecordListPage>
  );
}
