"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import {
  isNavActive,
  MVP_PRIMARY_NAV,
  MVP_SECONDARY_NAV,
} from "@/lib/navigation";

type AppNavProps = {
  onNavigate?: () => void;
};

function NavLink({
  item,
  active,
  onNavigate,
}: {
  item: { href: string; label: string; icon?: string };
  active: boolean;
  onNavigate?: () => void;
}) {
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
        active ? "bg-accent/15 font-medium text-accent" : "text-foreground hover:bg-zinc-900"
      }`}
    >
      <span
        className={`flex h-6 w-6 items-center justify-center text-base ${
          item.icon ? "" : "rounded-full border " + (active ? "border-accent bg-accent" : "border-muted")
        }`}
      >
        {item.icon ?? null}
      </span>
      {item.label}
    </Link>
  );
}

export function AppNav({ onNavigate }: AppNavProps) {
  const pathname = usePathname();
  const [moreOpen, setMoreOpen] = useState(
    MVP_SECONDARY_NAV.some((item) => isNavActive(pathname, item.href))
  );

  return (
    <nav className="space-y-4">
      <div>
        <p className="px-3 pb-2 text-xs font-medium uppercase tracking-wide text-muted">Hoved</p>
        <div className="space-y-1">
          {MVP_PRIMARY_NAV.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              active={isNavActive(pathname, item.href)}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      </div>

      <div>
        <button
          type="button"
          onClick={() => setMoreOpen((open) => !open)}
          className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted hover:bg-zinc-900"
        >
          Mer
          <span>{moreOpen ? "▾" : "▸"}</span>
        </button>
        {moreOpen && (
          <div className="mt-1 space-y-1">
            {MVP_SECONDARY_NAV.map((item) => (
              <NavLink
                key={item.href}
                item={item}
                active={isNavActive(pathname, item.href)}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        )}
      </div>

      <p className="px-3 text-xs text-muted">
        MVP-test: Dashboard, prosjekter, dokumenter m.m. er skjult. Bruk Streamlit-lab for full moduliste.
      </p>
    </nav>
  );
}
