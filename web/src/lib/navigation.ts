export type NavIconName =
  | "home"
  | "dashboard"
  | "chat"
  | "inbox"
  | "tasks"
  | "assets"
  | "goals"
  | "projects"
  | "decisions"
  | "documents"
  | "timeline"
  | "events"
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

/** Overview */
export const OVERVIEW_NAV: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: "dashboard" },
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
  { href: "/timeline", label: "Timeline", icon: "timeline" },
  { href: "/events", label: "Hendelser", icon: "events" },
];

/** Personalization */
export const SYSTEM_NAV: NavItem[] = [
  { href: "/integrations", label: "Integrasjoner", icon: "integrations" },
  { href: "/memory", label: "Minne", icon: "memory" },
  { href: "/settings", label: "Innstillinger", icon: "settings" },
];

/** All items shown under Mer on mobile */
export const MORE_NAV: NavItem[] = [...OVERVIEW_NAV, ...LIFE_NAV, ...SYSTEM_NAV];

/** Internal dev routes — not linked in UI */
export const DEV_ONLY_ROUTES = ["/self-evolve"];

/** @deprecated use PRIMARY_NAV */
export const MVP_PRIMARY_NAV = PRIMARY_NAV;

/** @deprecated use MORE_NAV */
export const MVP_SECONDARY_NAV = MORE_NAV;

/** @deprecated empty — all user-facing modules are now in nav */
export const MVP_HIDDEN_NAV: Omit<NavItem, "icon">[] = [];

export function isNavActive(pathname: string, href: string): boolean {
  if (href === "/home") return pathname === "/home";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function isHiddenRoute(pathname: string): boolean {
  return DEV_ONLY_ROUTES.some((route) => isNavActive(pathname, route));
}

export const APP_NAME = "WilliamOS";
