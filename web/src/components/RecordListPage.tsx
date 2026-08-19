"use client";

import Link from "next/link";
import { type ReactNode, useCallback, useEffect, useState } from "react";

import { ConfirmDeleteButton } from "@/components/ConfirmDeleteButton";
import { deleteRecord, fetchCollection } from "@/lib/api";

type RecordListPageProps = {
  title: string;
  description: string;
  path: string;
  fields: string[];
  emptyLabel?: string;
  refreshKey?: number;
  deletable?: boolean;
  deleteConfirmMessage?: string;
  itemHref?: (item: Record<string, unknown>) => string | undefined;
  children?: ReactNode;
};

function fieldValue(record: Record<string, unknown>, field: string): string {
  const value = record[field];
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Ja" : "Nei";
  return String(value);
}

export function RecordListPage({
  title,
  description,
  path,
  fields,
  emptyLabel = "Ingen poster ennå.",
  refreshKey = 0,
  deletable = false,
  deleteConfirmMessage = "Slette posten?",
  itemHref,
  children,
}: RecordListPageProps) {
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    fetchCollection(path)
      .then((data) => {
        setItems(data);
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, [path]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">{title}</h1>
        <p className="text-sm text-muted">{description}</p>
      </div>

      {children}

      {error && <p className="text-sm text-red-400">Kunne ikke laste data.</p>}

      {loading && items.length === 0 && <p className="text-sm text-muted">Laster…</p>}

      {(!loading || items.length > 0) && (
        <div className="space-y-3">
          {items.map((item) => {
            const href = itemHref?.(item);
            const card = (
              <article
                key={String(item.id)}
                className={`flex items-start justify-between gap-3 rounded-2xl border border-border p-4 ${
                  href ? "transition hover:border-accent/40" : ""
                }`}
              >
                <div className="min-w-0 space-y-1">
                  {fields.map((field) => (
                    <p key={field} className="text-sm">
                      <span className="text-muted capitalize">{field.replace(/_/g, " ")}: </span>
                      {fieldValue(item, field)}
                    </p>
                  ))}
                </div>
                {deletable && (
                  <ConfirmDeleteButton
                    confirmMessage={deleteConfirmMessage}
                    onConfirm={async () => {
                      const base = path.replace(/\/$/, "");
                      await deleteRecord(`${base}/${item.id}`);
                      load();
                    }}
                  />
                )}
              </article>
            );

            return href ? (
              <Link key={String(item.id)} href={href} className="block">
                {card}
              </Link>
            ) : (
              card
            );
          })}
          {!error && items.length === 0 && <p className="text-sm text-muted">{emptyLabel}</p>}
        </div>
      )}
    </div>
  );
}
