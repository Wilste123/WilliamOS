export type NavItem = {
  href: string;
  label: string;
  icon?: string;
};

/**
 * MVP test scope — only these appear in navigation.
 * Hidden modules still exist at their routes (for dev) but are not linked in UI.
 */
export const MVP_PRIMARY_NAV: NavItem[] = [
  { href: "/home", label: "Hjem", icon: "🏠" },
  { href: "/chat", label: "Chat", icon: "💬" },
  { href: "/inbox", label: "Inbox", icon: "📥" },
  { href: "/tasks", label: "Oppgaver", icon: "✓" },
];

export const MVP_SECONDARY_NAV: NavItem[] = [
  { href: "/assets", label: "Eiendeler", icon: "📦" },
  { href: "/settings", label: "Innstillinger", icon: "⚙️" },
];

/** Lab / later modules — hidden from nav during MVP testing */
export const MVP_HIDDEN_NAV: NavItem[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Prosjekter" },
  { href: "/decisions", label: "Beslutninger" },
  { href: "/events", label: "Hendelser" },
  { href: "/documents", label: "Dokumenter" },
  { href: "/timeline", label: "Timeline" },
  { href: "/memory", label: "Minne" },
  { href: "/self-evolve", label: "self-evolve" },
];

/** @deprecated Use MVP_PRIMARY_NAV + MVP_SECONDARY_NAV */
export const NAV_ITEMS: NavItem[] = [...MVP_PRIMARY_NAV, ...MVP_SECONDARY_NAV, ...MVP_HIDDEN_NAV];

export function isNavActive(pathname: string, href: string): boolean {
  if (href === "/home") return pathname === "/home";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function isHiddenRoute(pathname: string): boolean {
  return MVP_HIDDEN_NAV.some((item) => isNavActive(pathname, item.href));
}
