"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { isNavActive, MVP_PRIMARY_NAV } from "@/lib/navigation";

type BottomNavProps = {
  onOpenMenu: () => void;
};

export function BottomNav({ onOpenMenu }: BottomNavProps) {
  const pathname = usePathname();
  const quickLinks = MVP_PRIMARY_NAV.filter((item) => item.href !== "/tasks");

  return (
    <nav className="fixed bottom-0 inset-x-0 z-40 border-t border-border bg-background/95 backdrop-blur pb-[env(safe-area-inset-bottom)] lg:hidden">
      <div className="mx-auto flex max-w-lg items-stretch justify-around px-1 py-2">
        {quickLinks.map((link) => {
          const active = isNavActive(pathname, link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex min-h-11 min-w-14 flex-col items-center justify-center rounded-xl px-2 py-1 text-[11px] ${
                active ? "text-accent" : "text-muted"
              }`}
            >
              <span className="text-lg">{link.icon}</span>
              <span>{link.label}</span>
            </Link>
          );
        })}
        <Link
          href="/tasks"
          className={`flex min-h-11 min-w-14 flex-col items-center justify-center rounded-xl px-2 py-1 text-[11px] ${
            isNavActive(pathname, "/tasks") ? "text-accent" : "text-muted"
          }`}
        >
          <span className="text-lg">✓</span>
          <span>Oppgaver</span>
        </Link>
        <button
          type="button"
          onClick={onOpenMenu}
          className="flex min-h-11 min-w-14 flex-col items-center justify-center rounded-xl px-2 py-1 text-[11px] text-muted"
        >
          <span className="text-lg">☰</span>
          <span>Mer</span>
        </button>
      </div>
    </nav>
  );
}
