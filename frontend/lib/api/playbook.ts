import { apiFetch } from "./client";
import type { PlaybookEntry } from "@/lib/types";

const BASE = "/api/v1/playbook";

export async function listPlaybook(): Promise<PlaybookEntry[]> {
  return apiFetch<PlaybookEntry[]>(`${BASE}`, { method: "GET" });
}

export async function createPlaybookEntry(
  input: Omit<PlaybookEntry, "id" | "created_at" | "updated_at">,
): Promise<PlaybookEntry> {
  return apiFetch<PlaybookEntry>(`${BASE}`, { method: "POST", body: input });
}

export async function updatePlaybookEntry(
  id: string,
  input: Partial<Omit<PlaybookEntry, "id" | "created_at" | "updated_at">>,
): Promise<PlaybookEntry> {
  return apiFetch<PlaybookEntry>(`${BASE}/${id}`, {
    method: "PATCH",
    body: input,
  });
}

export async function deletePlaybookEntry(id: string): Promise<void> {
  await apiFetch<unknown>(`${BASE}/${id}`, { method: "DELETE" });
}
