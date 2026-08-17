export type NavItem = {
  href: string;
  label: string;
};

/** Navigation mirrors Streamlit sidebar order, with Hjem as the start screen. */
export const NAV_ITEMS: NavItem[] = [
  { href: "/home", label: "Hjem" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/inbox", label: "Inbox" },
  { href: "/chat", label: "Chat" },
  { href: "/tasks", label: "Oppgaver" },
  { href: "/assets", label: "Eiendeler" },
  { href: "/projects", label: "Prosjekter" },
  { href: "/decisions", label: "Beslutninger" },
  { href: "/events", label: "Hendelser" },
  { href: "/documents", label: "Dokumenter" },
  { href: "/timeline", label: "Timeline" },
  { href: "/memory", label: "Minne" },
  { href: "/settings", label: "Innstillinger" },
  { href: "/self-evolve", label: "self-evolve" },
];

export function isNavActive(pathname: string, href: string): boolean {
  if (href === "/home") return pathname === "/home";
  return pathname === href || pathname.startsWith(`${href}/`);
}
