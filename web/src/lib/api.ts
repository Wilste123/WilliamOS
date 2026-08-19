import { clearSession, getSession, saveSession, type AuthSession, type UserPreferences } from "./auth";

// Default /api uses Next.js proxy → FastAPI (works on iPhone via ngrok).
// Override only if you expose FastAPI on its own public URL.
const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "/api").replace(/\/$/, "");

function hasApiErrorDetail(payload: unknown): boolean {
  if (!payload || typeof payload !== "object") return false;
  if ("detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) return true;
    if (Array.isArray(detail) && detail.length > 0) return true;
  }
  if ("message" in payload && typeof (payload as { message: unknown }).message === "string") {
    return Boolean((payload as { message: string }).message.trim());
  }
  return false;
}

function parseErrorDetail(payload: unknown, status: number): string {
  if (payload && typeof payload === "object") {
    if ("detail" in payload) {
      const detail = (payload as { detail: unknown }).detail;
      if (typeof detail === "string" && detail.trim()) return detail;
      if (Array.isArray(detail) && detail.length > 0) {
        return detail
          .map((item) =>
            typeof item === "object" && item && "msg" in item ? String(item.msg) : "Ugyldig input"
          )
          .join(", ");
      }
    }
    if ("message" in payload && typeof (payload as { message: unknown }).message === "string") {
      const message = (payload as { message: string }).message;
      if (message.trim()) return message;
    }
  }
  if (status === 401) return "Du må logge inn på nytt.";
  if (status === 403) return "Du har ikke tilgang til denne handlingen.";
  if (status >= 500 && !hasApiErrorDetail(payload)) {
    return "FastAPI kjører ikke på port 8000. Start: uvicorn app.api.main:app --reload --port 8000";
  }
  if (status >= 500) return "Backend-feil. Sjekk at migrasjoner er kjørt og at FastAPI kjører.";
  return `Forespørselen feilet (${status})`;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

type RequestOptions = RequestInit & { auth?: boolean };

function syncSessionFromResponse(response: Response): void {
  const accessToken = response.headers.get("X-Access-Token");
  const refreshToken = response.headers.get("X-Refresh-Token");
  if (!accessToken || !refreshToken) return;
  const session = getSession();
  if (!session) return;
  saveSession({ ...session, access_token: accessToken, refresh_token: refreshToken });
}

function isSessionExpiredMessage(message: string): boolean {
  const lower = message.toLowerCase();
  return (
    lower.includes("jwt expired") ||
    lower.includes("pgrst303") ||
    lower.includes("sesjonen er utløpt") ||
    lower.includes("logg inn på nytt") ||
    lower.includes("du må logge inn")
  );
}

function handleAuthFailure(status: number, message: string, auth: boolean): void {
  if (!auth) return;
  // Only clear session on explicit auth failures — not generic 403 permission errors.
  if (status === 401 || isSessionExpiredMessage(message)) {
    logout();
  }
}

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
    throw new ApiError(parseErrorDetail(payload, response.status), 202);
  }

  if (!response.ok) {
    const message = parseErrorDetail(payload, response.status);
    handleAuthFailure(response.status, message, auth);
    throw new ApiError(message, response.status);
  }

  syncSessionFromResponse(response);
  return payload as T;
}

async function fetchAuthedBlob(path: string): Promise<Blob> {
  const session = getSession();
  if (!session) {
    throw new ApiError("Not authenticated", 401);
  }

  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      "X-Refresh-Token": session.refresh_token,
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message = parseErrorDetail(payload, response.status);
    handleAuthFailure(response.status, message, true);
    throw new ApiError(message, response.status);
  }

  syncSessionFromResponse(response);
  return response.blob();
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

export type ChatStreamEvent =
  | { type: "status"; phase: string }
  | { type: "token"; text: string }
  | { type: "done"; sources: unknown[]; actions?: ChatAction[] }
  | { type: "error"; message: string };

export type ChatAction = {
  id: string;
  type: string;
  label: string;
  title: string;
  status: "completed" | "proposed";
  payload?: Record<string, unknown>;
  result_id?: string;
};

export async function streamChat(
  message: string,
  history: { role: string; content: string }[],
  onEvent: (event: ChatStreamEvent) => void,
  options: { documentId?: string } = {}
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
      body: JSON.stringify({
        message,
        history,
        use_documents: true,
        document_id: options.documentId ?? null,
      }),
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
    const message = parseErrorDetail(payload, response.status);
    handleAuthFailure(response.status, message, true);
    throw new ApiError(message, response.status);
  }
  syncSessionFromResponse(response);
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

export async function deleteRecord(path: string) {
  return request<{ deleted: boolean; id: string }>(path, { method: "DELETE" });
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

export async function dismissInboxItem(inboxId: string) {
  return request<{ inbox_status: string }>(`/inbox/${inboxId}/dismiss`, {
    method: "POST",
  });
}

export async function fetchWeeklyBrief() {
  return request<WeeklyBrief>("/weekly-brief");
}

export type WeeklyBrief = {
  summary_text: string;
  priorities?: Record<string, unknown>[];
  focus_items?: PriorityFocusItem[];
  active_projects?: Record<string, unknown>[];
  open_decisions?: Record<string, unknown>[];
  upcoming_events?: Record<string, unknown>[];
  metrics?: Record<string, number>;
};

export type PriorityFocusItem = {
  source_type: string;
  title: string;
  score: number;
  reason: string;
  record?: Record<string, unknown>;
  meta?: Record<string, unknown>;
};

export async function fetchTimeline() {
  return request<Record<string, unknown>[]>("/timeline");
}

export async function createEvent(body: Record<string, unknown>) {
  return createRecord("/events", body);
}

export async function deleteEvent(eventId: string) {
  return deleteRecord(`/events/${eventId}`);
}

export type CalendarEvent = Record<string, unknown> & {
  id?: string;
  title?: string;
  start_at?: string;
  end_at?: string;
  all_day?: boolean;
  source?: string;
  location?: string;
  description?: string;
};

export async function fetchCalendar(options: { days?: number } = {}) {
  const query = options.days ? `?days=${options.days}` : "";
  return request<CalendarEvent[]>(`/calendar${query}`);
}

export async function createCalendarEvent(body: Record<string, unknown>) {
  return createRecord("/calendar", body);
}

export async function updateCalendarEvent(eventId: string, body: Record<string, unknown>) {
  return request<CalendarEvent>(`/calendar/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deleteCalendarEvent(eventId: string) {
  return deleteRecord(`/calendar/${eventId}`);
}

export async function syncGoogleCalendar() {
  return request<{ synced_events?: number; created?: number; updated?: number }>(
    "/calendar/sync/google",
    { method: "POST" }
  );
}

export async function deleteTask(taskId: string) {
  return deleteRecord(`/tasks/${taskId}`);
}

export async function deleteAsset(assetId: string) {
  return deleteRecord(`/assets/${assetId}`);
}

export async function deleteDocument(documentId: string) {
  return deleteRecord(`/documents/${documentId}`);
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
  const result = await updateProfile({ assistant_name: name });
  return { assistant_name: String(result.assistant_name ?? name) };
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
  return request<DocumentUploadResult>("/documents/upload", {
    method: "POST",
    body: form,
  });
}

export type DocumentSuggestion = {
  id: string;
  type: string;
  label: string;
  message: string;
  payload?: Record<string, unknown>;
};

export type DocumentUploadResult = Record<string, unknown> & {
  intelligence?: {
    doc_type: string;
    suggested_asset_id?: string | null;
    suggestions?: DocumentSuggestion[];
  };
};

export async function applyDocumentSuggestion(
  documentId: string,
  suggestionId: string,
  payload: Record<string, unknown> = {}
) {
  return request<{ applied: boolean }>(`/documents/${documentId}/apply-suggestion`, {
    method: "POST",
    body: JSON.stringify({ suggestion_id: suggestionId, payload }),
  });
}

export async function fetchDocumentPreviewBlob(documentId: string) {
  return fetchAuthedBlob(`/documents/${documentId}/preview`);
}

export async function downloadDocumentFile(documentId: string, filename: string) {
  const blob = await fetchAuthedBlob(`/documents/${documentId}/download`);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function analyzeDocument(documentId: string) {
  return request<DocumentUploadResult>(`/documents/${documentId}/analyze`, {
    method: "POST",
  });
}

export async function fetchGoals() {
  return request<Record<string, unknown>[]>("/goals");
}

export async function createGoal(body: Record<string, unknown>) {
  return createRecord("/goals", body);
}

export async function updateGoal(goalId: string, body: Record<string, unknown>) {
  return patchRecord(`/goals/${goalId}`, body);
}

export type GoalDetail = {
  goal: Record<string, unknown>;
  linked_record: Record<string, unknown> | null;
};

export async function fetchGoalDetail(goalId: string) {
  return request<GoalDetail>(`/goals/${goalId}`);
}

export type ProjectDetail = {
  project: Record<string, unknown>;
  links: Record<string, unknown>[];
  tasks: Record<string, unknown>[];
  open_tasks: Record<string, unknown>[];
  documents: Record<string, unknown>[];
  goals: Record<string, unknown>[];
  finance_accounts: Record<string, unknown>[];
  assets: Record<string, unknown>[];
  decisions: Record<string, unknown>[];
  events: Record<string, unknown>[];
};

export async function fetchProjectDetail(projectId: string) {
  return request<ProjectDetail>(`/projects/${projectId}`);
}

export async function linkProjectEntity(
  projectId: string,
  entityType: string,
  entityId: string
) {
  return request<Record<string, unknown>>(`/projects/${projectId}/links`, {
    method: "POST",
    body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
  });
}

export async function unlinkProjectLink(projectId: string, linkId: string) {
  return deleteRecord(`/projects/${projectId}/links/${linkId}`);
}

export async function updateProfile(body: {
  display_name?: string;
  assistant_name?: string;
  preferences?: Partial<UserPreferences>;
}) {
  return request<Record<string, unknown>>("/auth/profile", {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function exportUserData() {
  const paths = [
    "/assets",
    "/tasks",
    "/projects",
    "/goals",
    "/documents",
    "/decisions",
    "/calendar",
    "/timeline",
    "/memory",
  ];
  const entries = await Promise.all(
    paths.map(async (path) => {
      const data = path === "/memory" ? await fetchMemory() : await fetchCollection(path);
      return [path.replace(/^\//, ""), data] as const;
    })
  );
  return Object.fromEntries(entries);
}

export async function executeChatAction(action: ChatAction) {
  if (action.type === "create_task") {
    return createRecord("/tasks", action.payload ?? { title: action.title, priority: 2, status: "open" });
  }
  if (action.type === "create_asset") {
    return createRecord("/assets", action.payload ?? { name: action.title, status: "active" });
  }
  if (action.type === "create_project") {
    return createRecord("/projects", action.payload ?? { name: action.title, status: "active" });
  }
  if (action.type === "create_decision") {
    return createRecord("/decisions", action.payload ?? { title: action.title, status: "open" });
  }
  throw new ApiError(`Ukjent handling: ${action.type}`, 400);
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

export type FinanceSummary = {
  net_worth_nok: number;
  net_worth_formatted: string;
  physical_assets_nok: number;
  finance_assets_nok: number;
  liquidity_nok: number;
  debt_nok: number;
  change_12m_nok: number | null;
  change_12m_formatted: string | null;
  accounts: Record<string, unknown>[];
};

export async function fetchFinanceSummary() {
  return request<FinanceSummary>("/finance/summary");
}

export type HealthSummary = {
  latest_weight_kg: number | null;
  latest_weight_at: string | null;
  avg_sleep_hours_7d: number | null;
  avg_activity_minutes_7d: number | null;
  avg_steps_7d: number | null;
  weight_goal: Record<string, unknown> | null;
  recent_metrics: Record<string, unknown>[];
  sources: string[];
};

export async function fetchHealthSummary() {
  return request<HealthSummary>("/health-data/summary");
}

export type IntegrationStatus = {
  provider: string;
  label: string;
  description: string;
  connect_type: string;
  status: string;
  last_sync_at: string | null;
  configured: boolean;
  needs_reconnect?: boolean;
};

export async function fetchIntegrations() {
  return request<IntegrationStatus[]>("/integrations");
}

export async function connectIntegration(provider: string) {
  return request<{ auth_url?: string; configured?: boolean } & Record<string, unknown>>(
    `/integrations/${provider}/connect`,
    { method: "POST" }
  );
}

export async function completeGoogleIntegration(code: string, state: string) {
  return request<Record<string, unknown>>("/integrations/google/complete", {
    method: "POST",
    body: JSON.stringify({ code, state }),
  });
}

export async function disconnectIntegration(provider: string) {
  return request<Record<string, unknown>>(`/integrations/${provider}/disconnect`, { method: "POST" });
}

export async function syncIntegration(provider: string) {
  return request<{ synced_signals?: number; synced_events?: number; message?: string }>(
    `/integrations/${provider}/sync`,
    { method: "POST" }
  );
}
