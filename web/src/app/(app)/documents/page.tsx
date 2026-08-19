"use client";

import { useState } from "react";

import { DocumentList } from "@/components/DocumentList";
import { DocumentUploadForm } from "@/components/DocumentUploadForm";

export default function DocumentsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Dokumenter</h1>
        <p className="text-sm text-muted">
          Last opp, vis, last ned og analyser dokumenter knyttet til eiendeler og prosjekter.
        </p>
      </div>

      <DocumentUploadForm onUploaded={() => setRefreshKey((key) => key + 1)} />

      <section className="space-y-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">Lagrede dokumenter</h2>
        <DocumentList
          refreshKey={refreshKey}
          emptyLabel="Ingen dokumenter ennå. Last opp den første over."
        />
      </section>
    </div>
  );
}
