import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { RiskLevel } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/*
 * Risk level color mapping — flat color blocks, no border dependency.
 *   LOW      → emerald  (chart-2) — safe / standard
 *   MEDIUM   → amber    (chart-3) — attention required
 *   HIGH     → orange   (chart-4) — escalate
 *   CRITICAL → red      (chart-5) — block / immediate action
 */
export const riskLevelTone: Record<
  RiskLevel,
  { label: string; className: string }
> = {
  LOW: {
    label: "Low",
    className:
      "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  },
  MEDIUM: {
    label: "Medium",
    className:
      "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-200",
  },
  HIGH: {
    label: "High",
    className:
      "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300",
  },
  CRITICAL: {
    label: "Critical",
    className:
      "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  },
};

export function formatDateTime(iso: string | null | undefined): string {
  if (iso == null || iso === "") return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(d);
}

export function formatShortDate(iso: string | null | undefined): string {
  if (iso == null || iso === "") return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(d);
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}
