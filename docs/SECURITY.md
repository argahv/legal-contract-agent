# Security architecture & program notes

Legal Agent processes **highly confidential** documents. Security is a joint effort across infra, app code, and operational process.

## Data classification

| Tier | Examples | Controls |
| --- | --- | --- |
| T0 | Public marketing | N/A |
| T1 | Metadata (company names) | Standard TLS + auth |
| T2 | Full contract PDFs / DOCX | Encryption at rest + tenant isolation + audit |
| T3 | Export-controlled or privileged memos | Customer-managed keys + air-gapped option |

## Encryption at rest

Postgres TDE depends on cloud vendor features:

- **AWS RDS**: enable encryption with KMS CMK; rotate keys annually.
- **GCP Cloud SQL**: customer-managed encryption keys (CMEK).
- **Supabase / Neon**: rely on platform AES-256; verify SOC2 report + optional BYO encryption partner.

Application-level **column encryption** for ultra-sensitive notes can use libsodium sealed boxes — not yet implemented, plan in `docs/EVOLUTION.md`.

## Encryption in transit

- Terminate TLS at the edge (Cloudflare, AWS ALB, Fly.io handlers).
- Internal mesh mTLS optional when microservices multiply.
- WebSockets must use `wss://` in production — set `NEXT_PUBLIC_WS_URL` accordingly.

## PII & document redaction

1. **Ingest**: run PII detectors (emails, bank routing) before logging text excerpts.
2. **Logs**: scrub with structlog processors; ban raw prompts in INFO logs in prod.
3. **Exports**: watermark PDFs for human shares; include download ledger in `Audit`.

## Authentication & JWT hygiene

- `JWT_SECRET_KEY` must be 32+ random bytes (`openssl rand -hex 32`).
- Prefer **asymmetric** signing (RS256) at scale — centralize JWKS endpoint.
- Rotate keys with overlapping `kid` headers; reject tokens signed with retired keys after TTL.
- Refresh tokens stored hashed server-side when persistence layer lands.

## Authorization

- Map organization → tenant → roles; enforce on every repository call (not only routers).
- Admin playbook routes must use elevated scope distinct from reviewer.

## Rate limiting & abuse

`slowapi` integration (`core/rate_limit.py`) slows brute-force attempts. Pair with **WAF** rules for upload floods (large multipart storms).

## OWASP ASVS mapping (selected)

| Risk | Control in Legal Agent |
| --- | --- |
| Injection | Parameterized SQLAlchemy; never string-concatenate queries |
| Broken auth | JWT validation + Argon2 password hashing (`pwdlib`) |
| Sensitive data exposure | TLS + redacted logs + private object storage |
| XXE | Disable external entities in DOCX/PDF parsers |
| Broken access control | Tenant scoping in repositories |
| SSRF | Allowlist OpenAI / LangSmith domains; block metadata IP tricks |
| Misconfig | Harden Docker images (non-root), disable prod stack traces |

## Audit immutability

- `Audit` rows (`models/audit.py`) append-only; DB role for API user lacks `UPDATE`/`DELETE`.
- Ship logs to WORM storage (S3 Object Lock) nightly.

## Secret management

| Environment | Tooling |
| --- | --- |
| Local | `.env` never committed |
| CI | GitHub Encrypted Secrets |
| Prod | AWS Secrets Manager / GCP Secret Manager / Doppler |

## Dependency supply chain

- Pin Python + Node versions in CI (see `.github/workflows/ci.yml`).
- Enable GitHub Dependabot + `pip-audit` in a follow-up workflow.

## Incident response snapshot

1. Revoke API keys (OpenAI, LangSmith).
2. Force logout users (refresh token table purge).
3. Snapshot DB + object storage for forensics.
4. Notify customers per contractual SLA.
