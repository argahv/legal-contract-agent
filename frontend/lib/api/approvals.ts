import { apiFetch } from "./client";
import type {
  ApprovalRequest,
  ApprovalStatus,
  ContractStatus,
  User,
} from "@/lib/types";

const BASE = "/api/v1/approvals";

/** Backend `ApprovalRead` + optional joined fields from `GET /pending`. */
interface ApprovalApiRow {
  id: string;
  scope: string;
  status: "pending" | "approved" | "rejected";
  document_id: string;
  clause_id: string | null;
  requested_by_id: string | null;
  reviewer_id: string | null;
  notes: string | null;
  created_at: string;
  decided_at: string | null;
  document_filename?: string | null;
  document_status?: string | null;
  document_uploaded_at?: string | null;
  requested_by_email?: string | null;
}

function mapApiStatus(s: ApprovalApiRow["status"]): ApprovalStatus {
  const up = s.toUpperCase();
  if (up === "PENDING" || up === "APPROVED" || up === "REJECTED") {
    return up;
  }
  return "PENDING";
}

function mapDocumentStatus(raw: string | null | undefined): ContractStatus {
  switch (raw) {
    case "uploaded":
      return "UPLOADING";
    case "processing":
      return "PROCESSING";
    case "ready":
      return "REVIEW";
    case "failed":
      return "ERROR";
    default:
      return "REVIEW";
  }
}

function placeholderRequester(
  id: string | null | undefined,
  email: string | null | undefined,
): User {
  const e = email?.trim() || "unknown@example.com";
  return {
    id: id ?? "",
    email: e,
    full_name: e,
    role: "LEGAL_REVIEWER",
    is_active: true,
    created_at: new Date().toISOString(),
  };
}

export function mapApprovalFromApi(row: ApprovalApiRow): ApprovalRequest {
  const uploaded =
    row.document_uploaded_at ?? row.created_at;
  const contract = row.document_filename
    ? {
        id: row.document_id,
        filename: row.document_filename,
        status: mapDocumentStatus(row.document_status ?? undefined),
        uploaded_at: uploaded,
        updated_at: uploaded,
      }
    : undefined;

  return {
    id: row.id,
    contract_id: row.document_id,
    contract,
    status: mapApiStatus(row.status),
    requested_by: placeholderRequester(
      row.requested_by_id,
      row.requested_by_email,
    ),
    comment: row.notes ?? undefined,
    created_at: row.created_at,
    resolved_at: row.decided_at ?? undefined,
  };
}

export async function listApprovals(): Promise<ApprovalRequest[]> {
  const rows = await apiFetch<ApprovalApiRow[]>(`${BASE}/pending`, {
    method: "GET",
  });
  return rows.map(mapApprovalFromApi);
}

export async function resolveApproval(
  id: string,
  input: {
    status: Extract<ApprovalStatus, "APPROVED" | "REJECTED">;
    comment?: string;
  },
): Promise<ApprovalRequest> {
  const decision =
    input.status === "APPROVED" ? "approved" : "rejected";
  const row = await apiFetch<ApprovalApiRow>(`${BASE}/${id}/decision`, {
    method: "POST",
    body: {
      decision,
      comment: input.comment ?? null,
    },
  });
  return mapApprovalFromApi(row);
}
