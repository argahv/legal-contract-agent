export type Role =
  | "SUPER_ADMIN"
  | "ADMIN"
  | "LEGAL_REVIEWER"
  | "GENERAL_COUNSEL";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type ClauseType =
  | "LIMITATION_OF_LIABILITY"
  | "INDEMNITY"
  | "GOVERNING_LAW"
  | "TERMINATION"
  | "AUTO_RENEWAL"
  | "IP_OWNERSHIP"
  | "CONFIDENTIALITY";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export type ContractStatus =
  | "DRAFT"
  | "UPLOADING"
  | "PROCESSING"
  | "REVIEW"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "ERROR";

export interface ContractSummary {
  id: string;
  filename: string;
  status: ContractStatus;
  risk_summary?: Partial<Record<RiskLevel, number>>;
  uploaded_at: string;
  updated_at: string;
  uploaded_by?: Pick<User, "id" | "email" | "full_name">;
  /** ISO timestamp when the reviewer submitted the contract for GC queue (if any). */
  submitted_for_review_at?: string | null;
}

export interface Contract extends ContractSummary {
  content?: string;
  mime_type?: string;
  metadata?: Record<string, string>;
}

export interface Clause {
  id: string;
  contract_id: string;
  clause_type: ClauseType;
  title: string;
  body: string;
  start_offset?: number;
  end_offset?: number;
  sequence: number;
}

export interface RiskAssessment {
  id: string;
  clause_id: string;
  level: RiskLevel;
  rationale: string;
  suggested_action?: string;
}

export type RedlineStatus = "PENDING" | "ACCEPTED" | "REJECTED";

export interface Redline {
  id: string;
  clause_id: string;
  original_text: string;
  proposed_text: string;
  rationale?: string;
  status: RedlineStatus;
  reviewer_comment?: string | null;
}

export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface ApprovalRequest {
  id: string;
  contract_id: string;
  contract?: ContractSummary;
  status: ApprovalStatus;
  requested_by: User;
  assigned_to?: User;
  comment?: string;
  resolution_comment?: string;
  created_at: string;
  resolved_at?: string;
}

export interface PlaybookEntry {
  id: string;
  clause_type: ClauseType;
  title: string;
  guidance: string;
  fallback_language?: string;
  risk_floor: RiskLevel;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user: Pick<User, "id" | "email" | "full_name">;
  action: string;
  resource_type: string;
  resource_id?: string;
  metadata?: Record<string, unknown>;
}

export interface ContractProgressMessage {
  status: string;
  progress_percent: number;
  message?: string;
  step?: string;
}

export interface ApiErrorBody {
  detail: string;
}
