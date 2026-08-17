import { clearSession, getSession, saveSession, type AuthSession } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

  const response = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: nextHeaders,
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : "Request failed";
    throw new ApiError(detail, response.status);
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
  return request<{ answer: string; sources: unknown[] }>("/chat/", {
    method: "POST",
    body: JSON.stringify({ message, history, use_documents: true }),
  });
}

export async function fetchDashboard() {
  return request<Record<string, unknown>>("/dashboard");
}

export async function fetchInbox() {
  return request<unknown[]>("/inbox/");
}

export async function captureInbox(text: string) {
  return request<unknown>("/inbox/", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}
