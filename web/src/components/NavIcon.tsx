import {
  CheckSquare,
  Home,
  Inbox,
  MessageCircle,
  Package,
  Settings,
  type LucideIcon,
} from "lucide-react";

import type { NavIconName } from "@/lib/navigation";

const ICONS: Record<NavIconName, LucideIcon> = {
  home: Home,
  chat: MessageCircle,
  inbox: Inbox,
  tasks: CheckSquare,
  assets: Package,
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
