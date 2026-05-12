import { apiFetch } from "./client";
import type {
  Clause,
  Contract,
  ContractProgressMessage,
  ContractStatus,
  ContractSummary,
  Redline,
  RedlineStatus,
  RiskAssessment,
} from "@/lib/types";

const BASE = "/api/v1/contracts";

/** Backend `DocumentStatus` (StrEnum) → UI contract status. */
export function documentStatusToContractStatus(raw: string): ContractStatus {
  const s = raw.toLowerCase();
  if (s === "uploaded" || s === "processing") return "PROCESSING";
  if (s === "ready") return "REVIEW";
  if (s === "failed") return "ERROR";
  return "PROCESSING";
}

type ContractWire = {
  id: string;
  owner_id: string;
  filename: string;
  mime_type?: string | null;
  status: string;
  progress_percent: number;
  failure_reason?: string | null;
  submitted_for_review_at?: string | null;
  created_at: string;
  updated_at: string;
  extracted_text?: string | null;
  content?: string | null;
};

type RedlineWire = {
  id: string;
  clause_id: string;
  source?: string;
  proposed_text: string;
  rationale: string;
  status?: string;
  reviewer_comment?: string | null;
  playbook_entry_id?: string | null;
  original_text?: string | null;
  created_at?: string;
};

function mapContractWire(w: ContractWire): Contract {
  const text =
    w.extracted_text != null && String(w.extracted_text).length > 0
      ? String(w.extracted_text)
      : w.content != null && String(w.content).length > 0
        ? String(w.content)
        : undefined;
  return {
    id: String(w.id),
    filename: String(w.filename),
    status: documentStatusToContractStatus(String(w.status)),
    uploaded_at: String(w.created_at),
    updated_at: String(w.updated_at),
    submitted_for_review_at:
      w.submitted_for_review_at != null
        ? String(w.submitted_for_review_at)
        : undefined,
    content: text,
    mime_type: w.mime_type != null ? String(w.mime_type) : undefined,
  };
}

function mapRedlineStatus(raw: string | undefined): RedlineStatus {
  const st = (raw ?? "pending").toUpperCase();
  if (st === "ACCEPTED" || st === "REJECTED" || st === "PENDING") {
    return st;
  }
  return "PENDING";
}

function mapRedlineWire(r: RedlineWire): Redline {
  return {
    id: String(r.id),
    clause_id: String(r.clause_id),
    original_text: String(r.original_text ?? ""),
    proposed_text: String(r.proposed_text),
    rationale: r.rationale != null ? String(r.rationale) : undefined,
    status: mapRedlineStatus(r.status),
    reviewer_comment:
      r.reviewer_comment != null ? String(r.reviewer_comment) : undefined,
  };
}

type ContractUploadResponseWire = {
  document_id: string;
  status: string;
  message?: string;
};

export async function listContracts(): Promise<ContractSummary[]> {
  const rows = await apiFetch<ContractWire[]>(`${BASE}`, { method: "GET" });
  return rows.map((w) => {
    const c = mapContractWire(w);
    return {
      id: c.id,
      filename: c.filename,
      status: c.status,
      uploaded_at: c.uploaded_at,
      updated_at: c.updated_at,
      submitted_for_review_at: c.submitted_for_review_at,
    };
  });
}

export async function getContract(id: string): Promise<Contract> {
  const w = await apiFetch<ContractWire>(`${BASE}/${id}`, { method: "GET" });
  return mapContractWire(w);
}

export async function getContractStatus(
  id: string,
): Promise<ContractProgressMessage> {
  return apiFetch<ContractProgressMessage>(`${BASE}/${id}/status`, {
    method: "GET",
  });
}

export async function uploadContractFile(
  file: File,
): Promise<ContractSummary> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await apiFetch<ContractUploadResponseWire>(`${BASE}/upload`, {
    method: "POST",
    body: fd,
  });
  const now = new Date().toISOString();
  return {
    id: res.document_id,
    filename: file.name,
    status: documentStatusToContractStatus(res.status),
    uploaded_at: now,
    updated_at: now,
  };
}

export async function getClauses(contractId: string): Promise<Clause[]> {
  return apiFetch<Clause[]>(`${BASE}/${contractId}/clauses`, {
    method: "GET",
  });
}

export async function getRisks(contractId: string): Promise<RiskAssessment[]> {
  return apiFetch<RiskAssessment[]>(`${BASE}/${contractId}/risks`, {
    method: "GET",
  });
}

export async function getRedlines(contractId: string): Promise<Redline[]> {
  const rows = await apiFetch<RedlineWire[]>(
    `${BASE}/${contractId}/redlines`,
    { method: "GET" },
  );
  return rows.map(mapRedlineWire);
}

export async function updateRedline(
  contractId: string,
  redlineId: string,
  body: {
    proposed_text?: string;
    status?: "pending" | "accepted" | "rejected";
    reviewer_comment?: string | null;
  },
): Promise<Redline> {
  const w = await apiFetch<RedlineWire>(
    `${BASE}/${contractId}/redlines/${redlineId}`,
    { method: "PATCH", body },
  );
  return mapRedlineWire(w);
}

export async function submitContractForReview(
  contractId: string,
): Promise<Contract> {
  const w = await apiFetch<ContractWire>(
    `${BASE}/${contractId}/submit-review`,
    { method: "POST" },
  );
  return mapContractWire(w);
}
