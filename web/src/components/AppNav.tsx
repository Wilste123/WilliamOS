"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { NavIcon } from "@/components/NavIcon";
import {
  APP_NAME,
  isNavActive,
  LIFE_NAV,
  MORE_NAV,
  OVERVIEW_NAV,
  PRIMARY_NAV,
  SYSTEM_NAV,
  type NavItem,
} from "@/lib/navigation";

type AppNavProps = {
  onNavigate?: () => void;
};

function NavLink({
  item,
  active,
  onNavigate,
}: {
  item: NavItem;
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
      <NavIcon name={item.icon} />
      {item.label}
    </Link>
  );
}

function NavSection({
  title,
  items,
  pathname,
  onNavigate,
}: {
  title: string;
  items: NavItem[];
  pathname: string;
  onNavigate?: () => void;
}) {
  if (items.length === 0) return null;
  return (
    <div>
      <p className="px-3 pb-2 text-xs font-medium uppercase tracking-wide text-muted">{title}</p>
      <div className="space-y-1">
        {items.map((item) => (
          <NavLink
            key={item.href}
            item={item}
            active={isNavActive(pathname, item.href)}
            onNavigate={onNavigate}
          />
        ))}
      </div>
    </div>
  );
}

export function AppNav({ onNavigate }: AppNavProps) {
  const pathname = usePathname();
  const [moreOpen, setMoreOpen] = useState(MORE_NAV.some((item) => isNavActive(pathname, item.href)));

  return (
    <nav className="space-y-4">
      <NavSection title="Hoved" items={PRIMARY_NAV} pathname={pathname} onNavigate={onNavigate} />
      <NavSection title="Oversikt" items={OVERVIEW_NAV} pathname={pathname} onNavigate={onNavigate} />

      <div>
        <button
          type="button"
          onClick={() => setMoreOpen((open) => !open)}
          className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted hover:bg-zinc-900"
        >
          Liv & data
          <span>{moreOpen ? "▾" : "▸"}</span>
        </button>
        {moreOpen && (
          <div className="mt-1 space-y-4">
            <NavSection title="" items={LIFE_NAV} pathname={pathname} onNavigate={onNavigate} />
            <NavSection title="" items={SYSTEM_NAV} pathname={pathname} onNavigate={onNavigate} />
          </div>
        )}
      </div>

      <p className="px-3 text-xs text-muted">{APP_NAME} — full app</p>
    </nav>
  );
}
