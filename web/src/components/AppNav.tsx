"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { isNavActive, NAV_ITEMS } from "@/lib/navigation";

type AppNavProps = {
  onNavigate?: () => void;
};

export function AppNav({ onNavigate }: AppNavProps) {
  const pathname = usePathname();

  return (
    <nav className="space-y-1">
      <p className="px-3 pb-2 text-xs font-medium uppercase tracking-wide text-muted">Velg</p>
      {NAV_ITEMS.map((item) => {
        const active = isNavActive(pathname, item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
              active
                ? "bg-accent/15 font-medium text-accent"
                : "text-foreground hover:bg-zinc-900"
            }`}
          >
            <span
              className={`h-2.5 w-2.5 rounded-full border ${
                active ? "border-accent bg-accent" : "border-muted"
              }`}
            />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
