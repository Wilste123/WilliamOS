"use client";

import Link from "next/link";
import { Package, Pencil } from "lucide-react";

import { formatNok, statusLabel } from "@/lib/format";

type AssetCardProps = {
  asset: Record<string, unknown>;
  onEdit: () => void;
};

export function AssetCard({ asset, onEdit }: AssetCardProps) {
  const name = String(asset.name ?? "Uten navn");
  const assetType = asset.type ? String(asset.type) : null;
  const value = formatNok(asset.estimated_value);
  const assetId = String(asset.id ?? "");

  return (
    <article className="rounded-2xl border border-border bg-zinc-950/40 p-4">
      <div className="flex items-start gap-3">
        <Link
          href={`/assets/${assetId}`}
          className="flex min-w-0 flex-1 items-start gap-3"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/15 text-accent">
            <Package className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="font-medium">{name}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {assetType && (
                <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-muted">
                  {assetType}
                </span>
              )}
              <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-muted">
                {statusLabel(asset.status)}
              </span>
              <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs text-emerald-300">
                {value}
              </span>
            </div>
          </div>
        </Link>
        <button
          type="button"
          onClick={onEdit}
          aria-label="Rediger eiendel"
          className="rounded-lg border border-border p-2 text-muted hover:text-foreground"
        >
          <Pencil className="h-4 w-4" />
        </button>
      </div>
    </article>
  );
}
