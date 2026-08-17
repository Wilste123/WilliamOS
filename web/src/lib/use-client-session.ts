"use client";

import { useSyncExternalStore } from "react";

import { getSession, type AuthSession } from "./auth";

function subscribe(onStoreChange: () => void) {
  window.addEventListener("williamos-session-change", onStoreChange);
  window.addEventListener("storage", onStoreChange);
  return () => {
    window.removeEventListener("williamos-session-change", onStoreChange);
    window.removeEventListener("storage", onStoreChange);
  };
}

export function useClientSession(): AuthSession | null {
  return useSyncExternalStore(subscribe, () => getSession(), () => null);
}

export function useIsClient(): boolean {
  return useSyncExternalStore(() => () => {}, () => true, () => false);
}
