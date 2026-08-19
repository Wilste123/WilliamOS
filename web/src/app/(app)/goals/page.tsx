"use client";

import { useState } from "react";

import { GoalCreateSection } from "@/components/GoalCreateSection";
import { RecordListPage } from "@/components/RecordListPage";

export default function GoalsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <RecordListPage
      title="Mål"
      description="Aktive mål som mater inn i Priority Engine — knytt til helse, økonomi eller eiendeler."
      path="/goals"
      fields={["title", "status", "module", "next_step", "progress"]}
      emptyLabel="Ingen mål ennå."
      refreshKey={refreshKey}
      deletable
      deleteConfirmMessage="Slette målet?"
      itemHref={(item) => (item.id ? `/goals/${String(item.id)}` : undefined)}
    >
      <GoalCreateSection onCreated={() => setRefreshKey((key) => key + 1)} />
    </RecordListPage>
  );
}
