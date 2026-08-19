"use client";

import { useEffect, useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { TaskList } from "@/components/TaskList";
import { fetchCollection } from "@/lib/api";

export default function TasksPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [assetOptions, setAssetOptions] = useState<{ value: string; label: string }[]>([]);

  useEffect(() => {
    fetchCollection("/assets")
      .then((assets) =>
        setAssetOptions(
          assets.map((asset) => ({
            value: String(asset.id),
            label: String(asset.name ?? "Eiendel"),
          }))
        )
      )
      .catch(() => setAssetOptions([]));
  }, [refreshKey]);

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
          {
            name: "asset_id",
            label: "Eiendel",
            type: "select",
            placeholder: "Ingen eiendel",
            options: assetOptions,
          },
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
