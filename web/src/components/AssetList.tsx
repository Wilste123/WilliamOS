"use client";

import { useCallback, useEffect, useState } from "react";

import { AssetCard } from "@/components/AssetCard";
import { EditSheet } from "@/components/EditSheet";
import { fetchCollection, updateAsset } from "@/lib/api";

type AssetListProps = {
  refreshKey?: number;
  emptyLabel?: string;
};

const STATUS_OPTIONS = [
  { value: "active", label: "Aktiv" },
  { value: "considering_purchase", label: "Vurderes" },
  { value: "inactive", label: "Inaktiv" },
];

export function AssetList({
  refreshKey = 0,
  emptyLabel = "Ingen eiendeler ennå.",
}: AssetListProps) {
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [editing, setEditing] = useState<Record<string, unknown> | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    fetchCollection("/assets")
      .then((data) => {
        setItems(data);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  async function handleSave(values: Record<string, unknown>) {
    if (!editing) return;
    await updateAsset(String(editing.id), values);
    load();
  }

  if (loading && items.length === 0) {
    return <p className="text-sm text-muted">Laster…</p>;
  }

  return (
    <>
      {error && <p className="text-sm text-red-400">Kunne ikke laste data.</p>}
      <div className="space-y-3">
        {items.map((asset) => (
          <AssetCard key={String(asset.id)} asset={asset} onEdit={() => setEditing(asset)} />
        ))}
        {!error && items.length === 0 && <p className="text-sm text-muted">{emptyLabel}</p>}
      </div>
      <EditSheet
        open={editing !== null}
        title="Rediger eiendel"
        initialValues={editing ?? {}}
        fields={[
          { name: "name", label: "Navn", type: "text" },
          { name: "type", label: "Type", type: "text" },
          { name: "estimated_value", label: "Estimert verdi (NOK)", type: "number" },
          { name: "status", label: "Status", type: "select", options: STATUS_OPTIONS },
        ]}
        onClose={() => setEditing(null)}
        onSubmit={handleSave}
      />
    </>
  );
}
