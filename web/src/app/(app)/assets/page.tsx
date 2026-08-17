"use client";

import { useState } from "react";

import { AssetList } from "@/components/AssetList";
import { CreateRecordForm } from "@/components/CreateRecordForm";

export default function AssetsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Eiendeler</h1>
        <p className="text-sm text-muted">Boliger, kjøretøy, båter og andre eiendeler.</p>
      </div>

      <CreateRecordForm
        path="/assets"
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

      <AssetList
        refreshKey={refreshKey}
        emptyLabel="Ingen eiendeler ennå. Opprett den første over — verdien vises på Hjem."
      />
    </div>
  );
}
