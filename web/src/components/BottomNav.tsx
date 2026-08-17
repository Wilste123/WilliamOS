"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CheckSquare, Menu } from "lucide-react";

import { NavIcon } from "@/components/NavIcon";
import { isNavActive, MORE_NAV, PRIMARY_NAV } from "@/lib/navigation";

type BottomNavProps = {
  onOpenMenu: () => void;
};

export function BottomNav({ onOpenMenu }: BottomNavProps) {
  const pathname = usePathname();
  const quickLinks = PRIMARY_NAV.filter((item) => item.href !== "/tasks");
  const moreActive = MORE_NAV.some((item) => isNavActive(pathname, item.href));

  return (
    <nav className="fixed bottom-0 inset-x-0 z-40 border-t border-border bg-background/95 backdrop-blur pb-[env(safe-area-inset-bottom)] lg:hidden">
      <div className="mx-auto flex max-w-lg items-stretch justify-around px-1 py-2">
        {quickLinks.map((link) => {
          const active = isNavActive(pathname, link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex min-h-11 min-w-14 flex-col items-center justify-center gap-1 rounded-xl px-2 py-1 text-[11px] ${
                active ? "text-accent" : "text-muted"
              }`}
            >
              <NavIcon name={link.icon} className="h-5 w-5" />
              <span>{link.label}</span>
            </Link>
          );
        })}
        <Link
          href="/tasks"
          className={`flex min-h-11 min-w-14 flex-col items-center justify-center gap-1 rounded-xl px-2 py-1 text-[11px] ${
            isNavActive(pathname, "/tasks") ? "text-accent" : "text-muted"
          }`}
        >
          <CheckSquare className="h-5 w-5" />
          <span>Oppgaver</span>
        </Link>
        <button
          type="button"
          onClick={onOpenMenu}
          className={`flex min-h-11 min-w-14 flex-col items-center justify-center gap-1 rounded-xl px-2 py-1 text-[11px] ${
            moreActive ? "text-accent" : "text-muted"
          }`}
        >
          <Menu className="h-5 w-5" />
          <span>Mer</span>
        </button>
      </div>
    </nav>
  );
}
