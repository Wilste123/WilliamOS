"use client";

import { useSyncExternalStore } from "react";

import { getSession, SESSION_STORAGE_KEY, type AuthSession } from "./auth";

let cachedRaw: string | null | undefined;
let cachedSession: AuthSession | null = null;

function getClientSnapshot(): AuthSession | null {
  if (typeof window === "undefined") return null;

  const raw = localStorage.getItem(SESSION_STORAGE_KEY);
  if (raw === cachedRaw) {
    return cachedSession;
  }

  cachedRaw = raw;
  cachedSession = raw ? getSession() : null;
  return cachedSession;
}

function subscribe(onStoreChange: () => void) {
  window.addEventListener("williamos-session-change", onStoreChange);
  window.addEventListener("storage", onStoreChange);
  return () => {
    window.removeEventListener("williamos-session-change", onStoreChange);
    window.removeEventListener("storage", onStoreChange);
  };
}

export function useClientSession(): AuthSession | null {
  return useSyncExternalStore(subscribe, getClientSnapshot, () => null);
}

export function useIsClient(): boolean {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false
  );
}
