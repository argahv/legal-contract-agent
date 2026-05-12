import { apiFetch } from "./client";
import type { AuditLog } from "@/lib/types";

const BASE = "/api/v1/audit";

export type AuditQuery = {
  from?: string;
  to?: string;
  userId?: string;
  action?: string;
};

export async function listAuditLogs(query?: AuditQuery): Promise<AuditLog[]> {
  const params = new URLSearchParams();
  if (query?.from != null && query.from.length > 0) {
    params.set("created_after", query.from);
  }
  if (query?.to != null && query.to.length > 0) {
    params.set("created_before", query.to);
  }
  if (query?.userId != null && query.userId.length > 0) {
    params.set("actor_id", query.userId);
  }
  if (query?.action != null && query.action.length > 0) {
    params.set("action", query.action);
  }
  const qs = params.toString();
  const path = qs.length > 0 ? `${BASE}?${qs}` : BASE;
  return apiFetch<AuditLog[]>(path, { method: "GET" });
}
