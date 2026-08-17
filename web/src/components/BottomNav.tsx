"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/chat", label: "Chat", icon: "💬" },
  { href: "/inbox", label: "Inbox", icon: "📥" },
  { href: "/dashboard", label: "Oversikt", icon: "🏠" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 inset-x-0 z-50 border-t border-border bg-background/95 backdrop-blur pb-[env(safe-area-inset-bottom)]">
      <div className="mx-auto flex max-w-lg items-stretch justify-around px-2 py-2">
        {links.map((link) => {
          const active = pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex min-h-11 min-w-16 flex-col items-center justify-center rounded-xl px-3 py-2 text-xs ${
                active ? "text-accent" : "text-muted"
              }`}
            >
              <span className="text-lg">{link.icon}</span>
              <span>{link.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
