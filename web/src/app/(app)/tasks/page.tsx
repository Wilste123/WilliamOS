"use client";

import { useEffect, useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { TaskList } from "@/components/TaskList";
import { fetchCollection } from "@/lib/api";
import { entityRecordLabel } from "@/lib/project-links";

export default function TasksPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [assetOptions, setAssetOptions] = useState<{ value: string; label: string }[]>([]);
  const [projectOptions, setProjectOptions] = useState<{ value: string; label: string }[]>([]);

  useEffect(() => {
    Promise.all([fetchCollection("/assets"), fetchCollection("/projects")])
      .then(([assets, projects]) => {
        setAssetOptions(
          assets.map((asset) => ({ value: String(asset.id), label: entityRecordLabel(asset) }))
        );
        setProjectOptions(
          projects.map((project) => ({ value: String(project.id), label: entityRecordLabel(project) }))
        );
      })
      .catch(() => {
        setAssetOptions([]);
        setProjectOptions([]);
      });
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
        showVisibility
        fields={[
          { name: "title", label: "Tittel", type: "text", required: true, placeholder: "Hva skal gjøres?" },
          { name: "description", label: "Beskrivelse", type: "textarea", placeholder: "Detaljer (valgfritt)" },
          { name: "due_date", label: "Frist", type: "date" },
          {
            name: "priority",
            label: "Prioritet",
            type: "select",
            numeric: true,
            options: [
              { value: "1", label: "P1 — Høy" },
              { value: "2", label: "P2 — Normal" },
              { value: "3", label: "P3 — Lav" },
            ],
          },
          {
            name: "asset_id",
            label: "Eiendel",
            type: "select",
            placeholder: "Ingen eiendel",
            options: assetOptions,
          },
          {
            name: "project_id",
            label: "Prosjekt",
            type: "select",
            placeholder: "Ingen prosjekt",
            options: projectOptions,
          },
        ]}
        extraPayload={{ status: "open" }}
        onCreated={() => setRefreshKey((key) => key + 1)}
      />

      <TaskList
        refreshKey={refreshKey}
        emptyLabel="Ingen oppgaver ennå. Opprett den første over."
      />
    </div>
  );
}
