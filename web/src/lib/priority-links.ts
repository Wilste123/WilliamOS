import type { PriorityFocusItem } from "./api";

function chatPrompt(title: string): string {
  return `/chat?prompt=${encodeURIComponent(`Hjelp meg med: ${title}`)}&send=1`;
}

export function priorityItemHref(item: PriorityFocusItem): string {
  const record = item.record;
  const id = record?.id ? String(record.id) : undefined;

  switch (item.source_type) {
    case "task":
      if (record?.asset_id) return `/assets/${String(record.asset_id)}`;
      return id ? chatPrompt(item.title) : "/tasks";
    case "goal":
      return "/goals";
    case "project":
      return "/projects";
    case "inbox":
      return "/inbox";
    case "decision":
      return "/decisions";
    default:
      return chatPrompt(item.title);
  }
}

export function priorityItemActionLabel(item: PriorityFocusItem): string | null {
  switch (item.source_type) {
    case "inbox":
      return "Gå til inbox";
    case "goal":
      return "Se mål";
    case "task":
      return item.record?.asset_id ? "Se eiendel" : "Snakk med PA";
    default:
      return null;
  }
}
