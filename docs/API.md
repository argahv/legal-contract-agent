# HTTP API guide

## Source of truth

FastAPI will expose **interactive OpenAPI** at:

- Swagger UI: `http://localhost:8000/docs`
- Raw schema: `http://localhost:8000/openapi.json`

Treat those documents as authoritative once `app.main:app` registers routers.  
This page provides **orientation** and a **curated checklist** so reviewers know what to expect before the server skeleton lands fully.

> **Implementation note (current repo state):** HTTP routers are not yet checked into `backend/app/`. The rows below map to **repositories and schemas** that already exist and describe the intended contract.

## Authentication model (planned)

| Concern | Detail |
| --- | --- |
| Mechanism | JWT access + refresh (`backend/app/core/security.py`, `backend/app/schemas/auth.py`) |
| Header | `Authorization: Bearer <access_token>` |
| Roles | Extend `User` model + enum when RBAC hardens (`backend/app/models/user.py`) |

## Error envelope

Align with `backend/app/core/exceptions.py` — HTTP mapping should preserve:

- `401` unauthenticated
- `403` authenticated but unauthorized
- `404` missing contract resources
- `409` conflicting approvals / state transitions
- `422` validation (Pydantic)
- `429` rate limit (`backend/app/core/rate_limit.py`)

## Endpoint catalog (curated)

Legend: **Auth** values are `public`, `user`, `admin` placeholders for the eventual RBAC matrix.

| Method | Path (prefix `/api/v1`) | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | public | Create organization user |
| `POST` | `/auth/login` | public | Issue JWT pair |
| `POST` | `/auth/refresh` | refresh | Rotate tokens safely |
| `GET` | `/users/me` | user | Profile + role claims |
| `POST` | `/contracts` | user | Create contract shell |
| `GET` | `/contracts` | user | List contracts for tenant |
| `GET` | `/contracts/{id}` | user | Contract metadata |
| `POST` | `/contracts/{id}/documents` | user | Upload MS Word / PDF (`multipart/form-data`, size enforced via `MAX_UPLOAD_MB`) |
| `POST` | `/contracts/{id}/ingest` | user | Kick off OCR + text normalization (`backend/app/ai/document_text.py`) |
| `GET` | `/contracts/{id}/clauses` | user | Materialized clause spans |
| `PATCH` | `/clauses/{id}` | user | Reviewer edits to extracted text |
| `POST` | `/contracts/{id}/analyze` | user | Run extraction + risk + rule engine |
| `GET` | `/contracts/{id}/risks` | user | Risk findings (`backend/app/models/risk.py`) |
| `GET` | `/contracts/{id}/redlines` | user | Suggested edits w/ playbook linkage (`backend/app/models/redline.py`) |
| `POST` | `/redlines/{id}/accept` | reviewer | Accept suggestion |
| `POST` | `/redlines/{id}/reject` | reviewer | Reject w/ rationale |
| `GET` | `/playbook` | admin | Administrative CRUD for entries |
| `POST` | `/playbook` | admin | Create playbook embedding row (`backend/app/models/playbook.py`) |
| `POST` | `/playbook/reindex` | admin | Kick vector rebuild (`make vector.index` until automated) |
| `GET` | `/approvals?contract_id=` | reviewer | Queue of pending human gates |
| `POST` | `/approvals/{id}/decide` | reviewer | Approve / deny (`backend/app/models/approval.py`) |
| `GET` | `/audit?contract_id=` | auditor | Immutable history (`backend/app/models/audit.py`) |

## WebSockets

| Topic | Path | Notes |
| --- | --- | --- |
| Reviewer stream | `/ws/reviews/{contract_id}` | Fan-out hub sketched in `backend/app/ws/hub.py` |

Clients should read `NEXT_PUBLIC_WS_URL` from the frontend environment for host placement.

## Pagination & filtering (recommended defaults)

- `limit` default `50`, hard cap `200`.
- `cursor` (opaque) preferred over large `offset` for audit + clause lists.
- Optional `clause_type` filter should mirror `ClauseType` in `backend/app/models/enums.py`.

## Versioning

Prefix everything with `/api/v1`. Breaking changes require `/api/v2` + sunset headers documented in release notes.

## Compliance hooks

- Every mutating route should emit audit rows (`Audit` model + repository) capturing actor, payload hash, timestamps.
- Upload routes must run virus scanning / content inspection in production (see `docs/SECURITY.md`).

## Testing stance

- Contract tests should validate OpenAPI examples once published.
- Integration tests (see `.github/workflows/ci.yml`) assume Postgres + pgvector — mirror UUID + vector types in factories.
