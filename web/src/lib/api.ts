import { clearSession, getSession, saveSession, type AuthSession } from "./auth";

// Default /api uses Next.js proxy → FastAPI (works on iPhone via ngrok).
// Override only if you expose FastAPI on its own public URL.
const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "/api").replace(/\/$/, "");

function parseErrorDetail(payload: unknown): string {
  if (!payload || typeof payload !== "object" || !("detail" in payload)) {
    return "Forespørselen feilet";
  }
  const detail = (payload as { detail: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : "Ugyldig input"))
      .join(", ");
  }
  return "Forespørselen feilet";
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

type RequestOptions = RequestInit & { auth?: boolean };

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const session = getSession();
  const nextHeaders = new Headers(headers);

  if (auth) {
    if (!session) {
      throw new ApiError("Not authenticated", 401);
    }
    nextHeaders.set("Authorization", `Bearer ${session.access_token}`);
    nextHeaders.set("X-Refresh-Token", session.refresh_token);
  }

  if (rest.body && !(rest.body instanceof FormData)) {
    nextHeaders.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...rest,
      headers: nextHeaders,
    });
  } catch {
    throw new ApiError(
      "Kunne ikke nå backend. Sjekk at FastAPI kjører (uvicorn app.api.main:app --reload --port 8000). " +
        "På iPhone via ngrok: bruk kun ngrok på port 3000 — ikke localhost:8000.",
      0
    );
  }

  const payload = await response.json().catch(() => ({}));

  if (response.status === 202) {
    throw new ApiError(parseErrorDetail(payload), 202);
  }

  if (!response.ok) {
    throw new ApiError(parseErrorDetail(payload), response.status);
  }

  return payload as T;
}

export async function login(email: string, password: string): Promise<AuthSession> {
  const session = await request<AuthSession>("/auth/login", {
    auth: false,
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  saveSession(session);
  return session;
}

export async function signup(input: {
  email: string;
  password: string;
  display_name: string;
  household_name: string;
}): Promise<AuthSession> {
  const session = await request<AuthSession>("/auth/signup", {
    auth: false,
    method: "POST",
    body: JSON.stringify(input),
  });
  saveSession(session);
  return session;
}

export async function fetchMe(): Promise<AuthSession> {
  const me = await request<Omit<AuthSession, "access_token" | "refresh_token">>("/auth/me");
  const session = getSession();
  if (!session) {
    throw new ApiError("Not authenticated", 401);
  }
  const updated = { ...session, ...me };
  saveSession(updated);
  return updated;
}

export function logout(): void {
  clearSession();
}

export async function sendChat(message: string, history: { role: string; content: string }[] = []) {
  return request<{ answer: string; sources: unknown[] }>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, history, use_documents: true }),
  });
}

export type ChatStreamEvent =
  | { type: "status"; phase: string }
  | { type: "token"; text: string }
  | { type: "done"; sources: unknown[] }
  | { type: "error"; message: string };

export async function streamChat(
  message: string,
  history: { role: string; content: string }[],
  onEvent: (event: ChatStreamEvent) => void
): Promise<void> {
  const session = getSession();
  if (!session) {
    throw new ApiError("Not authenticated", 401);
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}/chat/stream`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "X-Refresh-Token": session.refresh_token,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message, history, use_documents: true }),
    });
  } catch {
    throw new ApiError(
      "Kunne ikke nå backend. Sjekk at FastAPI kjører (uvicorn app.api.main:app --reload --port 8000). " +
        "På iPhone via ngrok: bruk kun ngrok på port 3000 — ikke localhost:8000.",
      0
    );
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new ApiError(parseErrorDetail(payload), response.status);
  }
  if (!response.body) {
    throw new ApiError("Ingen strøm fra serveren.", 0);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      emitSseLines(part, onEvent);
    }
  }
  emitSseLines(buffer, onEvent);
}

function emitSseLines(block: string, onEvent: (event: ChatStreamEvent) => void) {
  for (const line of block.split("\n")) {
    if (!line.startsWith("data: ")) continue;
    try {
      onEvent(JSON.parse(line.slice(6)) as ChatStreamEvent);
    } catch {
      // ignore malformed chunks
    }
  }
}

export async function fetchCollection(path: string) {
  return request<Record<string, unknown>[]>(path);
}

export async function createRecord(path: string, body: Record<string, unknown>) {
  return request<Record<string, unknown>>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function patchRecord(path: string, body: Record<string, unknown>) {
  return request<Record<string, unknown>>(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function completeTask(taskId: string) {
  return patchRecord(`/tasks/${taskId}`, { completed: true, status: "completed" });
}

export async function updateTask(taskId: string, body: Record<string, unknown>) {
  return patchRecord(`/tasks/${taskId}`, body);
}

export async function updateAsset(assetId: string, body: Record<string, unknown>) {
  return patchRecord(`/assets/${assetId}`, body);
}

export async function applyInboxSuggestion(inboxId: string, suggestionIndex: number) {
  return request<{ object_type: string; created: Record<string, unknown>; inbox_status: string }>(
    `/inbox/${inboxId}/apply`,
    {
      method: "POST",
      body: JSON.stringify({ suggestion_index: suggestionIndex }),
    }
  );
}

export async function fetchDashboard() {
  return request<DashboardSummary>("/dashboard");
}

export type DashboardSummary = {
  metrics: {
    assets: number;
    open_tasks: number;
    projects: number;
    documents: number;
    open_decisions: number;
  };
  priorities: Record<string, unknown>[];
  upcoming_events: Record<string, unknown>[];
  active_projects: Record<string, unknown>[];
  new_documents: Record<string, unknown>[];
  recent_activity: Record<string, unknown>[];
};

export async function fetchWeeklyBrief() {
  return request<WeeklyBrief>("/weekly-brief");
}

export type WeeklyBrief = {
  summary_text: string;
  priorities?: Record<string, unknown>[];
  active_projects?: Record<string, unknown>[];
  open_decisions?: Record<string, unknown>[];
  upcoming_events?: Record<string, unknown>[];
  metrics?: Record<string, number>;
};

export async function fetchTimeline() {
  return request<Record<string, unknown>[]>("/timeline");
}

export async function fetchMemory() {
  return request<{ items: Record<string, unknown>[]; text: string }>("/memory");
}

export async function saveMemory(value: string, key?: string, category?: string) {
  return request<{ saved: boolean }>("/chat/memory", {
    method: "POST",
    body: JSON.stringify({ value, key, category }),
  });
}

export async function fetchSelfEvolve() {
  return request<{ count: number; top_signals: [string, number][] }>("/chat/self-evolve");
}

export async function updateAssistantName(name: string) {
  return request<{ assistant_name: string }>("/auth/profile", {
    method: "PATCH",
    body: JSON.stringify({ assistant_name: name }),
  });
}

export async function fetchHome() {
  return request<import("./home").HomeSummary>("/home");
}

export async function fetchInbox() {
  return request<unknown[]>("/inbox");
}

export async function captureInbox(text: string) {
  return request<unknown>("/inbox", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export type AssetDetail = {
  asset: Record<string, unknown>;
  tasks: Record<string, unknown>[];
  open_tasks: Record<string, unknown>[];
  projects: Record<string, unknown>[];
  documents: Record<string, unknown>[];
  decisions: Record<string, unknown>[];
  events: Record<string, unknown>[];
};

export async function fetchAssetDetail(assetId: string) {
  return request<AssetDetail>(`/assets/${assetId}`);
}

export async function uploadDocument(
  file: File,
  options: { assetId?: string; projectId?: string; sourceModule?: string } = {}
) {
  const form = new FormData();
  form.append("file", file);
  if (options.assetId) form.append("asset_id", options.assetId);
  if (options.projectId) form.append("project_id", options.projectId);
  if (options.sourceModule) form.append("source_module", options.sourceModule);
  return request<Record<string, unknown>>("/documents/upload", {
    method: "POST",
    body: form,
  });
}

export type ChatHistoryMessage = {
  id?: string;
  role: string;
  content: string;
  created_at?: string;
};

export async function fetchChatHistory(limit = 40) {
  return request<{ messages: ChatHistoryMessage[] }>(`/chat/history?limit=${limit}`);
}

export async function appendChatHistory(messages: { role: string; content: string }[]) {
  return request<{ saved: number }>("/chat/history", {
    method: "POST",
    body: JSON.stringify({ messages }),
  });
}

export async function clearChatHistory() {
  return request<{ cleared: boolean }>("/chat/history", { method: "DELETE" });
}

export type UsageStats = {
  days_opened_this_week: number;
  total_opens: number;
  streak_days: number;
  last_opened_at: string | null;
  seven_day_goal_met: boolean;
};

export async function recordAppOpen() {
  return request<UsageStats>("/usage/open", { method: "POST" });
}

export async function fetchUsageStats() {
  return request<UsageStats>("/usage");
}
