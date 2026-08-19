"use client";

import { useEffect, useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { RecordListPage } from "@/components/RecordListPage";
import { fetchCollection, patchRecord } from "@/lib/api";
import { entityRecordLabel } from "@/lib/project-links";

export default function DecisionsPage() {
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
    <RecordListPage
      title="Beslutninger"
      description="Beslutninger du følger opp — opprett, marker som besluttet, eller slett."
      path="/decisions"
      fields={["title", "status", "next_action"]}
      refreshKey={refreshKey}
      deletable
      deleteConfirmMessage="Slette beslutningen?"
      itemActions={(item, reload) =>
        item.status !== "decided" ? (
          <button
            type="button"
            onClick={async (event) => {
              event.preventDefault();
              event.stopPropagation();
              await patchRecord(`/decisions/${item.id}`, { status: "decided" });
              reload();
            }}
            className="rounded-lg border border-border px-3 py-1.5 text-xs text-accent"
          >
            Marker besluttet
          </button>
        ) : null
      }
    >
      <CreateRecordForm
        path="/decisions"
        submitLabel="Opprett beslutning"
        showVisibility
        extraPayload={{ status: "open" }}
        fields={[
          { name: "title", label: "Tittel", type: "text", required: true, placeholder: "Hva skal avgjøres?" },
          { name: "summary", label: "Beskrivelse", type: "textarea", placeholder: "Kontekst og alternativer" },
          { name: "next_action", label: "Neste handling", type: "text", placeholder: "Hva skjer videre?" },
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
        onCreated={() => setRefreshKey((key) => key + 1)}
      />
    </RecordListPage>
  );
}
