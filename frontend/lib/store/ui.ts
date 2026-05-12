"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type UiThemePreference = "light" | "dark" | "system";

interface UiState {
  sidebarCollapsed: boolean;
  theme: UiThemePreference;
  setSidebarCollapsed: (v: boolean) => void;
  toggleSidebar: () => void;
  setTheme: (theme: UiThemePreference) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set, get) => ({
      sidebarCollapsed: false,
      theme: "light",
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
      toggleSidebar: () =>
        set({ sidebarCollapsed: !get().sidebarCollapsed }),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: "legal-agent-ui",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({
        sidebarCollapsed: s.sidebarCollapsed,
        theme: s.theme,
      }),
    },
  ),
);
