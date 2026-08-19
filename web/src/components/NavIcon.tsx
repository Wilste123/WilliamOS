import {
  Brain,
  CheckSquare,
  FileText,
  FolderKanban,
  GitBranch,
  Goal,
  HeartPulse,
  History,
  Home,
  Inbox,
  MessageCircle,
  Package,
  Plug,
  Settings,
  Wallet,
  type LucideIcon,
} from "lucide-react";

import type { NavIconName } from "@/lib/navigation";

const ICONS: Record<NavIconName, LucideIcon> = {
  home: Home,
  chat: MessageCircle,
  inbox: Inbox,
  tasks: CheckSquare,
  assets: Package,
  goals: Goal,
  projects: FolderKanban,
  decisions: GitBranch,
  documents: FileText,
  timeline: History,
  finance: Wallet,
  health: HeartPulse,
  integrations: Plug,
  memory: Brain,
  settings: Settings,
};

export function NavIcon({
  name,
  className = "h-5 w-5",
}: {
  name: NavIconName;
  className?: string;
}) {
  const Icon = ICONS[name];
  return <Icon className={className} aria-hidden="true" />;
}
