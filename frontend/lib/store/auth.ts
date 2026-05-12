"use client";

import * as React from "react";
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { Role, User } from "@/lib/types";

export interface AuthSession {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setSession: (access: string, refresh: string, user: User) => void;
  clearSession: () => void;
  setUser: (user: User) => void;
  setTokens: (access: string, refresh: string) => void;
}

export const useAuthStore = create<AuthSession>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setSession: (access, refresh, user) =>
        set({
          accessToken: access,
          refreshToken: refresh,
          user,
        }),
      clearSession: () =>
        set({ accessToken: null, refreshToken: null, user: null }),
      setUser: (user) => set({ user }),
      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),
    }),
    {
      name: "legal-agent-auth",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    },
  ),
);

export function canAccessApprovals(role: Role | undefined): boolean {
  return (
    role === "SUPER_ADMIN" ||
    role === "GENERAL_COUNSEL" ||
    role === "ADMIN"
  );
}

/** Matches `GET /api/v1/audit` — privileged operators only. */
export function canViewAuditLog(role: Role | undefined): boolean {
  return (
    role === "SUPER_ADMIN" ||
    role === "ADMIN" ||
    role === "GENERAL_COUNSEL"
  );
}

export function canEditPlaybook(role: Role | undefined): boolean {
  return role === "SUPER_ADMIN" || role === "ADMIN";
}

export function useAuthHydrated(): boolean {
  const [hydrated, setHydrated] = React.useState(false);
  React.useEffect(() => {
    let cancelled = false;
    const done = () => {
      if (!cancelled) {
        setHydrated(true);
      }
    };
    const safety = globalThis.setTimeout(done, 500);
    const unsub = useAuthStore.persist.onFinishHydration(() => {
      globalThis.clearTimeout(safety);
      done();
    });
    return () => {
      cancelled = true;
      globalThis.clearTimeout(safety);
      if (typeof unsub === "function") {
        unsub();
      }
    };
  }, []);
  return hydrated;
}
