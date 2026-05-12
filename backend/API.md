# Backend HTTP API reference

**Authoritative route list** for the Legal Agent FastAPI service. The repository-level `[docs/API.md](../docs/API.md)` defers here for method-level detail.

## Conventions

- **Base URL**: configurable; local default `http://localhost:8000`.
- **Version prefix**: `/api/v1` (see `Settings.api_v1_prefix`).
- **Auth**: Unless noted, endpoints require `Authorization: Bearer <access_token>`.
- **JSON**: `Content-Type: application/json` for bodies.
- **Errors**: JSON `{"detail": "<message>", "request_id": "<correlation id>"}` for most failures. Validation errors follow FastAPI/Pydantic shape (`422`). Rate limits return `429`.
- **Roles**: `ADMIN`, `LEGAL_REVIEWER`, `GENERAL_COUNSEL` (see `app.models.enums.UserRole`).

## Public probes (no auth)


| Method | Path       | Description                        | Response                                                                                                                  |
| ------ | ---------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `GET`  | `/healthz` | Liveness                           | `200` `{"status":"ok"}`                                                                                                   |
| `GET`  | `/readyz`  | Readiness (DB ping + config flags) | `200` JSON: `ready`, `dependencies.database`, `dependencies.openai_configured`, `dependencies.pgvector_expected`, `error` |


`readyz` treats the app as ready when the database query succeeds **and** `OPENAI_API_KEY` is non-empty (deployment expectation).

## Auth (`/api/v1/auth`)


| Method | Path                    | Auth   | Request body                                               | Response           | Notes                  |
| ------ | ----------------------- | ------ | ---------------------------------------------------------- | ------------------ | ---------------------- |
| `POST` | `/api/v1/auth/register` | No     | `UserCreate`: `email`, `password` (8–128), optional `role` | `201` `AuthBundle` | Rate limit `20/min` IP |
| `POST` | `/api/v1/auth/login`    | No     | `UserLogin`: `email`, `password`                           | `200` `AuthBundle` | Rate limit `30/min`    |
| `POST` | `/api/v1/auth/refresh`  | No     | `RefreshRequest`: `refresh_token`                          | `200` `TokenPair`  | Rate limit `60/min`    |
| `GET`  | `/api/v1/auth/me`       | Bearer | —                                                          | `200` `UserMe`     |                        |


`**AuthBundle`**: `{ "user": UserRead, "tokens": TokenPair }`  
`**TokenPair**`: `{ "access_token", "refresh_token", "token_type": "bearer" }`  
`**UserRead` / `UserMe**`: `{ "id", "email", "role" }`

**Typical errors**: `409` conflict (duplicate email), `401` invalid credentials, `422` validation.

## Contracts (`/api/v1/contracts`)

All routes require a **logged-in** user; documents are scoped to **owner**.


| Method | Path                                       | Request                                                                   | Response                                                                    |
| ------ | ------------------------------------------ | ------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `POST` | `/api/v1/contracts/upload`                 | `multipart/form-data` field `file`; MIME must be PDF, DOCX, or plain text | `202` `ContractUploadResponse`: `document_id`, `status`                     |
| `GET`  | `/api/v1/contracts`                        | —                                                                         | `200` `ContractRead[]`                                                      |
| `GET`  | `/api/v1/contracts/{document_id}`          | —                                                                         | `200` `ContractRead`                                                        |
| `GET`  | `/api/v1/contracts/{document_id}/status`   | —                                                                         | `200` `ContractStatusRead`                                                  |
| `GET`  | `/api/v1/contracts/{document_id}/clauses`  | —                                                                         | `200` `ClauseRead[]`                                                        |
| `GET`  | `/api/v1/contracts/{document_id}/risks`    | —                                                                         | `200` `RiskRead[]`                                                          |
| `GET`  | `/api/v1/contracts/{document_id}/redlines` | —                                                                         | `200` `RedlineRead[]` (includes `original_text` from clause when available) |


**Upload**: schedules `run_contract_pipeline` as a background task after commit.

**Typical errors**: `422` `ValidationAppError` unsupported MIME; `404` document not owned / missing; `401` missing/invalid JWT.

## Approvals (`/api/v1/approvals`)

Requires role `**GENERAL_COUNSEL`**.


| Method | Path                                       | Request                                                                    | Response               |
| ------ | ------------------------------------------ | -------------------------------------------------------------------------- | ---------------------- |
| `GET`  | `/api/v1/approvals/pending`                | —                                                                          | `200` `ApprovalRead[]` |
| `POST` | `/api/v1/approvals/{approval_id}/decision` | JSON `ApprovalDecision`: `decision` (`ApprovalStatus`), optional `comment` | `200` `ApprovalRead`   |


**Typical errors**: `403` wrong role; `404` unknown approval; domain validation as `422`/`400` via `AppError`.

## Playbook admin (`/api/v1/playbook`)

Requires role `**ADMIN`**.


| Method   | Path                          | Request                         | Response               |
| -------- | ----------------------------- | ------------------------------- | ---------------------- |
| `GET`    | `/api/v1/playbook`            | —                               | `200` `PlaybookRead[]` |
| `POST`   | `/api/v1/playbook`            | JSON `PlaybookCreate`           | `201` `PlaybookRead`   |
| `PATCH`  | `/api/v1/playbook/{entry_id}` | JSON `PlaybookUpdate` (partial) | `200` `PlaybookRead`   |
| `DELETE` | `/api/v1/playbook/{entry_id}` | —                               | `204` empty body       |


Embeddings are refreshed server-side on write paths (service responsibility).

**Typical errors**: `403` non-admin; `404` entry missing.

## Audit (`/api/v1/audit`)

Requires `**ADMIN` OR `GENERAL_COUNSEL`**.


| Method | Path            | Query parameters                                                                                                                    | Response               |
| ------ | --------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| `GET`  | `/api/v1/audit` | `actor_id` (UUID), `action`, `entity_type`, `created_after`, `created_before` (ISO datetime), `limit` (≤500, default 100), `offset` | `200` `AuditLogRead[]` |


**Typical errors**: `403` insufficient role.

## WebSocket (realtime progress)


| Method    | Path                                                        | Auth                                     | Protocol                                                                                                      |
| --------- | ----------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| WebSocket | `/ws/contracts/{document_id}/progress?token=<access_token>` | JWT **query param** `token` (not header) | Server accepts, validates token, subscribes client to progress hub; invalid token → close `1008` Unauthorized |


Client may send ping text; server primarily **pushes** progress events from the worker implementation.

## Status code summary


| Code  | Source                                        |
| ----- | --------------------------------------------- |
| `200` | Success (read/decision/update)                |
| `201` | Created (register, playbook create)           |
| `202` | Accepted (async upload handoff)               |
| `204` | No content (playbook delete)                  |
| `400` | `BadRequestError`                             |
| `401` | `UnauthorizedError` / bad JWT                 |
| `403` | `ForbiddenError` / role mismatch              |
| `404` | `NotFoundError`                               |
| `409` | `ConflictError`                               |
| `422` | Validation (`ValidationAppError` or Pydantic) |
| `429` | SlowAPI / `RateLimitAppError`                 |
| `502` | `ExternalServiceError`                        |
| `503` | `ServiceUnavailableError`                     |


## Related

- Backend module layout: `[backend/ARCHITECTURE.md](./ARCHITECTURE.md)`
- System-level API narrative: `[docs/API.md](../docs/API.md)` (should link to this file)