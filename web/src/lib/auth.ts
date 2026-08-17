export type AuthSession = {
  user_id: string;
  email: string;
  household_id: string;
  display_name: string | null;
  assistant_name: string | null;
  access_token: string;
  refresh_token: string;
};

const STORAGE_KEY = "williamos_session";
const SESSION_CHANGE_EVENT = "williamos-session-change";

function notifySessionChange(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(SESSION_CHANGE_EVENT));
}

export function getSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

export function saveSession(session: AuthSession): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  notifySessionChange();
}

export function clearSession(): void {
  localStorage.removeItem(STORAGE_KEY);
  notifySessionChange();
}

export function logout(): void {
  clearSession();
}

export function isAuthenticated(): boolean {
  return getSession() !== null;
}
