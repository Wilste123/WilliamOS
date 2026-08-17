"use client";

import { useState } from "react";

import { DocumentUploadForm } from "@/components/DocumentUploadForm";
import { RecordListPage } from "@/components/RecordListPage";

export default function DocumentsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Dokumenter</h1>
        <p className="text-sm text-muted">
          Last opp og se dokumenter knyttet til eiendeler og prosjekter.
        </p>
      </div>

      <DocumentUploadForm onUploaded={() => setRefreshKey((key) => key + 1)} />

      <RecordListPage
        title="Lagrede dokumenter"
        description="Filer du har lastet opp."
        path="/documents/"
        fields={["filename", "source_module", "created_at"]}
        refreshKey={refreshKey}
        emptyLabel="Ingen dokumenter ennå. Last opp den første over."
      />
    </div>
  );
}
