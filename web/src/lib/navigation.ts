export type NavIconName =
  | "home"
  | "chat"
  | "inbox"
  | "tasks"
  | "assets"
  | "goals"
  | "projects"
  | "decisions"
  | "documents"
  | "timeline"
  | "finance"
  | "health"
  | "integrations"
  | "memory"
  | "settings";

export type NavItem = {
  href: string;
  label: string;
  icon: NavIconName;
};

/** Daily driver — bottom bar + top of sidebar */
export const PRIMARY_NAV: NavItem[] = [
  { href: "/home", label: "Hjem", icon: "home" },
  { href: "/chat", label: "Chat", icon: "chat" },
  { href: "/inbox", label: "Inbox", icon: "inbox" },
  { href: "/tasks", label: "Oppgaver", icon: "tasks" },
];

/** Life modules — goals, home, documents, history */
export const LIFE_NAV: NavItem[] = [
  { href: "/assets", label: "Eiendeler", icon: "assets" },
  { href: "/finance", label: "Økonomi", icon: "finance" },
  { href: "/health", label: "Helse", icon: "health" },
  { href: "/goals", label: "Mål", icon: "goals" },
  { href: "/projects", label: "Prosjekter", icon: "projects" },
  { href: "/decisions", label: "Beslutninger", icon: "decisions" },
  { href: "/documents", label: "Dokumenter", icon: "documents" },
  { href: "/timeline", label: "Historikk", icon: "timeline" },
];

/** Personalization */
export const SYSTEM_NAV: NavItem[] = [
  { href: "/integrations", label: "Integrasjoner", icon: "integrations" },
  { href: "/memory", label: "Minne", icon: "memory" },
  { href: "/settings", label: "Innstillinger", icon: "settings" },
];

/** All items shown under Mer on mobile */
export const MORE_NAV: NavItem[] = [...LIFE_NAV, ...SYSTEM_NAV];

/** Internal dev routes — not linked in UI */
export const DEV_ONLY_ROUTES = ["/self-evolve"];

export function isNavActive(pathname: string, href: string): boolean {
  if (href === "/home") return pathname === "/home";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function isHiddenRoute(pathname: string): boolean {
  return DEV_ONLY_ROUTES.some((route) => isNavActive(pathname, route));
}

export const APP_NAME = "WilliamOS";
