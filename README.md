# Legal Agent

**Legal Agent** is an AI-assisted contract review platform aimed at high-stakes **Master Service Agreements (MSAs)** and similar vendor paper. Teams upload agreements, extract structured clauses, score legal and operational risk, and align suggestions with an enterprise **playbook** backed by **pgvector** retrieval. Human reviewers stay in the loop for approvals, redlines, and immutable audit history.

This repository is split across parallel engineering tracks:


| Track                          | Scope                                                                  |
| ------------------------------ | ---------------------------------------------------------------------- |
| Backend executor               | `backend/app/` — FastAPI entrypoint, routers, service layer wiring     |
| Frontend executor              | `frontend/app/`, `frontend/components/`, `frontend/lib/` — reviewer UX |
| Infra & docs (this PR surface) | Root `Makefile`, Docker, Compose, `docs/`, CI, helper scripts          |


> **Current scaffold note:** `backend/app/main.py` and Alembic migrations are expected from the API track. Tooling (`Makefile`, Compose, Dockerfiles) already targets `uvicorn app.main:app` so the stack lights up as soon as those files land.

---

## Product vision

Legal teams drown in **repetitive first-pass review** — scanning the same vendor tricks (microscopic liability caps, sneaky auto-renewals, one-sided indemnity) across hundreds of pages per quarter. Junior counsel loses velocity; senior counsel loses patience.

Legal Agent compresses that workflow to:

1. **Ingest** — DOCX/PDF upload with resilient text extraction (`backend/app/ai/document_text.py`).
2. **Understand** — LLM-powered extraction to typed clauses (`backend/app/ai/chains/extraction.py`).
3. **Check** — deterministic guardrails (`backend/app/ai/chains/rule_engine.py`).
4. **Score & narrate** — risk storytelling that cites playbook language (`backend/app/ai/chains/risk.py`).
5. **Recommend** — RAG-ranked redlines tied to `PlaybookEntry` rows (`backend/app/models/playbook.py`).
6. **Decide** — human approvals + audit trail (`backend/app/models/approval.py`, `audit.py`).

Non-goals for the MVP: autonomous signing, definitive legal advice without counsel, or uncited model claims.

---

## Screenshots (placeholders)

Drop real UI captures here once the frontend track publishes pages:

```
docs/assets/screenshots/
  01-dashboard.png     # Contract queue + risk heatmap
  02-clause-detail.png # Extracted clause + playbook comparison
  03-redline-diff.png  # Suggested replacement + reviewer actions
  04-approvals.png     # Approval routing + SLA timestamps
```

Until then, use `make frontend.dev` locally and capture after branding pass.

---

## Quickstart

### Prerequisites

- Docker Compose v2 (`docker compose version`)
- Python **3.12** (for local venv workflows)
- Node **22** + npm (for local Next.js)
- `make`

### One-time setup (DB + migrations + playbook seed + vector embeddings)

Requires **Docker Desktop running** (for Compose Postgres). Then either:

```bash
cp .env.example .env
# Edit: JWT_SECRET_KEY, OPENROUTER_* or OPENAI_* (chat + embedding model ids), DATABASE_URL if not using Compose defaults

make backend.install   # local Python venv (needed for Alembic + seeds + embeddings from the host)
make setup             # same as: bash scripts/full_setup.sh → dev_bootstrap.sh (db up, alembic upgrade head, seed_playbook, embed_playbook_vectors)
```

Or run the shell script directly:

```bash
./scripts/dev_bootstrap.sh
```

Use `**make vector.index**` (or `bash scripts/vector_reindex.sh`) to **force** re-embed all playbook rows after you change wording or models.

Destructive DB reset (drop database, migrate, seed, embed): `bash scripts/reset_db.sh`

### Run everything (Docker)

```bash
make up
```

Services (see `docker-compose.yml`):


| Service    | Port | Purpose                         |
| ---------- | ---- | ------------------------------- |
| `db`       | 5432 | Postgres 16 + pgvector          |
| `backend`  | 8000 | FastAPI (hot reload in Compose) |
| `frontend` | 3000 | Next.js production image        |


### Run locally (hybrid)

```bash
make backend.install   # backend/.venv
make frontend.install
docker compose up -d db
make backend.stop        # optional: if port 8000 is already in use (Errno 48)
make backend.run         # needs app.main for uvicorn import
make frontend.dev
```

OpenAPI (once routers exist): `http://localhost:8000/docs`

---

## Architecture (ASCII)

```
┌──────────────┐   HTTPS/WSS    ┌──────────────────────┐
│   Browser    │◀──────────────▶│  Next.js 15 (React)   │
│  (reviewers) │                │  frontend/*           │
└──────────────┘                └─────────┬────────────┘
                                          │ REST + WS
                                          ▼
┌──────────────────────────────────────────────────────┐
│ FastAPI (async) — backend/app                        │
│  • JWT auth / rate limiting                          │
│  • Upload + ingestion                                │
│  • LangChain extraction + risk chains                │
│  • WebSocket hub (`app/ws/hub.py`)                   │
└─────────┬───────────────────────────────┬────────────┘
          │ SQLAlchemy async                     │
          ▼                                       ▼
┌──────────────────────┐                 ┌─────────────────┐
│ Postgres + pgvector   │                 │ OpenAI APIs     │
│  • contracts/clauses  │                 │ chat + embed    │
│  • playbook embeddings│                 └─────────────────┘
│  • audit / approval   │
└──────────────────────┘
```

Mermaid counterparts live in `docs/ARCHITECTURE.md` for zoomable diagrams.

---

## Tech stack rationale


| Layer   | Choice                         | Why                                                |
| ------- | ------------------------------ | -------------------------------------------------- |
| API     | FastAPI                        | Native async, OpenAPI, excellent typing            |
| ORM     | SQLAlchemy 2 + asyncpg         | Mature migrations story, aligns with FastAPI DI    |
| Vectors | pgvector in Postgres           | Fewer moving parts than split vector DB for MVP    |
| AI      | LangChain + LangSmith          | Traceability + composable LCEL-style chains        |
| UI      | Next.js 15 + Tailwind + shadcn | App Router, rapid iteration, accessible primitives |
| Tooling | Make + Compose                 | Lowest-common-denominator DX for mixed teams       |


---

## Environment variables

Authoritative template: `.env.example` (every variable commented). Highlights:


| Variable                                     | Role                                                 |
| -------------------------------------------- | ---------------------------------------------------- |
| `DATABASE_URL`                               | Async SQLAlchemy DSN (`postgresql+asyncpg://...`)    |
| `POSTGRES_*`                                 | Compose `db` service credentials                     |
| `JWT_SECRET_KEY`                             | Signing material for access/refresh tokens           |
| `OPENAI_API_KEY` / `OPENAI_MODEL`            | Chat + default model tier                            |
| `OPENAI_EMBEDDING_MODEL` / `VECTOR_DIM`      | Embeddings + pgvector width                          |
| `LANGSMITH_*` + `LANGCHAIN_TRACING_V2`       | Observability switches                               |
| `CORS_ORIGINS`                               | Browser origins allowed to call API with credentials |
| `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL` | Frontend discovery                                   |


**Naming nuance:** `backend/app/core/config.py` validates `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` — the example file mirrors both `JWT_`* and canonical names to reduce onboarding friction.

---

## Common workflows


| Task                    | Command                                         |
| ----------------------- | ----------------------------------------------- |
| Full stack up/down      | `make up` / `make down`                         |
| Tail logs               | `make logs`                                     |
| Backend shell tests     | `make backend.test`                             |
| Frontend lint/typecheck | `make frontend.lint`, `make frontend.typecheck` |
| Repo-wide gate          | `make check`                                    |
| DB console              | `make db.shell`                                 |
| Reset database          | `make db.reset` (destructive)                   |
| Playbook re-embed guide | `make vector.index`                             |
| LangSmith UI            | `make langsmith.open`                           |


### Bootstrap playbook seed

`./scripts/dev_bootstrap.sh` and `make backend.seed` load rows via `backend/scripts/seed_playbook.py` (idempotent).

---

## Makefile reference (compact)

Targets are self-documented via `make help`. Notable implementations:

- **backend.lint** currently enforces Ruff on `backend/scripts` + `backend/tests` because `backend/app/` is mid-flight in a parallel executor (see `docs/CONTRIBUTING.md`).
- **frontend.test** skips gracefully until a `test` script lands in `frontend/package.json`.

---

## Docker notes

- **Backend image:** multi-stage wheel build, `python:3.12-slim`, `tini` PID1, non-root `appuser`. See `backend/Dockerfile`.
- **Frontend image:** Node 22, multi-stage; entrypoint tries `.next/standalone/server.js` then `npm run start`. Enable `output: "standalone"` in `next.config.ts` when the frontend track opts in (Dockerfile comment documents this — **do not edit** `next.config.ts` from infra PRs unless you own that track).
- **Compose** layers optional `env_file` entries (`.env.example` then `.env`) so `docker compose config -q` works on fresh clones.

---

## Documentation suite


| Doc                              | Contents                                          |
| -------------------------------- | ------------------------------------------------- |
| `docs/ARCHITECTURE.md`           | Context diagrams, ER-style model chart, lifecycle |
| `docs/AI_PIPELINE.md`            | Chains, retrieval, LangSmith walkthrough          |
| `docs/DEBUGGING_AI.md`           | Logging, traces, eval harness sketch              |
| `docs/COST_OPTIMIZATION.md`      | Model tiering, caching, batching                  |
| `docs/SECURITY.md`               | Encryption, PII, OWASP mapping                    |
| `docs/DEPLOYMENT.md`             | Managed Postgres, Fly/Render/ECS thoughts         |
| `docs/SCALING.md`                | RLS vs schema isolation, queues                   |
| `docs/API.md`                    | Endpoint intent + `/docs` pointer                 |
| `docs/PROMPTS.md`                | Example prompt templates per clause               |
| `docs/PLAYBOOK_SAMPLES.md`       | Worked legal examples + mapping                   |
| `docs/AI_ENGINEERING_ROADMAP.md` | Senior → staff AI engineering curriculum          |
| `docs/EVOLUTION.md`              | Product phases + integration roadmap              |
| `docs/CONTRIBUTING.md`           | Branching, commits, PR checklist                  |


---

## Testing & CI

GitHub Actions (`.github/workflows/ci.yml`) runs:

1. **backend** — Ruff on `scripts`/`tests`, pytest with Postgres + pgvector service
2. **frontend** — ESLint, `tsc --noEmit`, `next build`
3. **docker-build** — verifies backend + frontend Dockerfiles

---

## Troubleshooting

### `uvicorn` cannot import `app.main`

The API track has not merged `backend/app/main.py` yet — expected. Run domain modules (`pytest`, seeds) or stub `main.py` locally if you need Compose health temporarily.

### Database connection errors inside Compose

Ensure `.env` `DATABASE_URL` uses hostname `db` and matches `POSTGRES_`*. After changing env vars, `docker compose down && make up`.

### Frontend cannot reach API

Check `NEXT_PUBLIC_API_URL` matches published backend port (`8000` by default) and that `CORS_ORIGINS` includes your UI origin.

### pgvector extension missing

Confirm `./docker/postgres/init-pgvector.sql` mounted (see `docker-compose.yml`). For existing volumes created before the init script, run `CREATE EXTENSION vector;` manually via `make db.shell`.

### Rate limiting during dev

Raise `RATE_LIMIT_PER_MINUTE` temporarily in `.env` — never commit secrets.

### Disk pressure on local machines

Heavy `python` / `npm` installs can exhaust space — remove old Docker images (`docker system prune`) or relocate Docker data root.

### LangSmith empty project

Enable tracing: `LANGCHAIN_TRACING_V2=true` + valid `LANGSMITH_API_KEY`. Re-run a chain; traces may take ~30s to appear.

---

## Security notes (abbreviated)

- Rotate `JWT_SECRET_KEY` for every environment; store in a secret manager in production.
- Treat uploads as untrusted — scan/examine binaries before server-side parsing in production.
- Never log raw contract text at INFO in multi-tenant deployments — see `docs/SECURITY.md`.
- Enable TLS everywhere outside local dev; align WebSocket URL scheme (`wss://`).

---

## Deployment recommendations (high level)

1. Choose managed Postgres with pgvector + backups (Supabase, Neon, RDS).
2. Push images via CI to ECR/GCR/Artifact Registry.
3. Run API + worker (future) autoscaling off request queue depth + CPU.
4. Export OpenTelemetry to Honeycomb/Datadog; keep LangSmith for LLM-specific spans.
5. Promote migrations separately from app deploys — see `docs/DEPLOYMENT.md`.

---

## Known caveats

### Nested `frontend/.git`

The `frontend/` directory currently carries its **own** Git history (legacy CNA bootstrap). Root `git init` now exists, but Git will **not** automatically track nested repo contents.

**You should consolidate** by either:

- Removing `frontend/.git` and recommitting the tree into the monorepo, or
- Using `git subtree add` / submodule strategy intentionally.

This infra PR **does not delete** `frontend/.git` per project constraints.

### Lint scope during parallel execution

Ruff runs on scripts/tests only until `backend/app/` import order + unused import debt is cleared by the owning track (see Makefile comment).

---

## Repository layout (selected)

```
.
├── backend/
│   ├── Dockerfile
│   ├── app/                 # domain code — parallel executor
│   ├── scripts/             # seed + ops helpers (infra-owned)
│   ├── tests/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pyproject.toml       # Ruff config
├── frontend/
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   └── ...
├── docker/
│   └── postgres/
│       └── init-pgvector.sql
├── docs/
├── scripts/
│   ├── dev_bootstrap.sh
│   ├── reset_db.sh
│   └── vector_reindex.sh
├── .github/workflows/
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md                # you are here
```

---

## Licensing & contributions

See `docs/CONTRIBUTING.md` for branching + review norms. License file not included in this scaffolding — add one before open-sourcing.

---

## AI feature map (code pointers)


| Capability           | Module                                 |
| -------------------- | -------------------------------------- |
| Clause extraction    | `backend/app/ai/chains/extraction.py`  |
| Deterministic checks | `backend/app/ai/chains/rule_engine.py` |
| Risk narration       | `backend/app/ai/chains/risk.py`        |
| Prompt inventory     | `backend/app/ai/prompts.py`            |
| Playbook ORM         | `backend/app/models/playbook.py`       |
| Settings             | `backend/app/core/config.py`           |


These paths are safe to cite in docs and onboarding decks — they won't change casually.

---

## Operational cadence (suggested)


| Cadence   | Activity                                         |
| --------- | ------------------------------------------------ |
| Daily     | Watch LangSmith error runs + API 5xx             |
| Weekly    | Playbook drift review with counsel               |
| Monthly   | Cost retro (`docs/COST_OPTIMIZATION.md` metrics) |
| Quarterly | DR drill on Postgres restore                     |


---

## Performance expectations

Initial targets (tune with production telemetry):

- Ingest + text extraction < 5s for typical DOCX ≤ 20 MB on dev-grade CPUs
- End-to-end first-pass review JSON < 60s for ~40-page MSA using `gpt-4o-mini` extraction path
- API availability SLO begins at **99.5%** pre-enterprise hardening — tighten as on-call matures

Document deviations with trace + query artifacts in postmortems.

---

## Data governance hooks

- Map each contract to `organization_id` when migrations arrive — never query without tenant filter.
- Record reviewer decisions in `Audit` rows; disallow destructive updates via DB roles.
- Pair deletion policies in object storage with contract retention legal holds.

---

## Extending the playbook

1. Insert rows with admin tooling (future) or temporary SQL.
2. Re-embed vectors — follow `make vector.index` guidance until automation ships.
3. Update `docs/PLAYBOOK_SAMPLES.md` with rationale so future reviewers understand non-obvious positions.

---

## Glossary


| Term     | Definition                                                |
| -------- | --------------------------------------------------------- |
| Playbook | Curated standard positions + acceptable fallback language |
| Redline  | Suggested textual change with playbook linkage            |
| Clause   | Atomic legal segment extracted for analysis               |
| RAG      | Retrieval-augmented generation (pgvector + prompt hints)  |


---

## Community & support

Until a formal support channel exists:

1. Start from `docs/DEBUGGING_AI.md` for AI regressions.
2. Check Compose logs (`make logs`) for connectivity issues.
3. Capture LangSmith traces for model regressions.

---

## Marketing snapshot (internal)

**Elevator pitch:** "Legal Agent gives every reviewer a playbook-aware co-pilot — extraction, risk scoring, and cited redlines in one workflow, grounded in your enterprise standards instead of generic GPT advice."

**Buyer:** VP Legal Ops + Head of Procurement partnering with IT for AI governance.

**Proof points:** Traceable suggestions, audit trail, editable playbook corpus.

---

## Roadmap teaser

Read `docs/EVOLUTION.md` for multi-agent supervision, DocuSign/Slack integrations, and fine-tuned domain models — architecture intents complement MVP scope.

---

## Benchmarks (TODO once eval harness lands)

Populate when `docs/DEBUGGING_AI.md` harness exists:


| Dataset            | Metric   | Baseline | Current |
| ------------------ | -------- | -------- | ------- |
| Clause F1 (sample) | Macro F1 | —        | —       |
| Playbook recall@5  | Recall   | —        | —       |
| Cost / contract    | USD      | —        | —       |


---

## Developer happiness tips

- Use `make help` frequently — targets stay descriptive.
- Prefer `docker compose` over ad-hoc manual container sprawl.
- Keep `.env` out of Git; prefer secret store integration for shared staging clusters.

---

## Legal disclaimer (not legal advice)

This README describes software architecture only. It does not provide legal counsel. All contractual decisions require qualified attorneys.

---

## Acknowledgments

Design inspirations: modern legal ops tooling, LangChain observability best practices, and enterprise security guidance from SOC2 programs.

---

## Appendix — environment matrix


| Environment | Database         | Tracing            | Uploads           |
| ----------- | ---------------- | ------------------ | ----------------- |
| Local dev   | Compose Postgres | Optional LangSmith | Local volume path |
| Staging     | Managed Postgres | On                 | Private bucket    |
| Production  | HA Postgres      | Required           | SSE-KMS bucket    |


---

## Appendix — HTTP status expectations


| Code    | Meaning                           |
| ------- | --------------------------------- |
| 200     | OK / resource returned            |
| 201     | Created (upload / resource spawn) |
| 202     | Accepted async job                |
| 400     | Malformed client request          |
| 401/403 | AuthZ issues                      |
| 409     | Conflict (approval state)         |
| 422     | Validation errors (schema)        |
| 429     | Rate limit (SlowAPI)              |


---

## Appendix — WebSocket events (planned)


| Event                | Payload hints                      |
| -------------------- | ---------------------------------- |
| `ingest.status`      | `{ contract_id, stage, pct }`      |
| `review.update`      | `{ contract_id, summary_version }` |
| `approval.requested` | `{ approval_id, assignee }`        |


Actual schemas arrive with router implementation.

---

## Appendix — Makefile taxonomy


| Prefix          | Meaning              |
| --------------- | -------------------- |
| `backend.`*     | Python service       |
| `frontend.`*    | Next.js app          |
| `db.`*          | Postgres via Compose |
| `*` (top-level) | Meta / orchestration |


---

## Appendix — why Make?

Make is dependency-light, works offline, and reads well in READMEs for polyglot teams. If you prefer `just`, wrap the same scripts.

---

## Appendix — Open questions for PM/LEGAL

1. Which contract types beyond MSA in v1?
2. Mandatory human approval on which clause families?
3. Data residency commitments by customer segment?
4. Maximum permissible automation before ethics review?

Track answers in your private issue tracker — not in this public template if sensitive.

---

## Appendix — changelog placeholder


| Version        | Date | Highlights            |
| -------------- | ---- | --------------------- |
| 0.1.0-scaffold | TBD  | Monorepo infra + docs |


---

## Final notes

Ship small, measure, annotate traces, and keep humans foremost in the loop. Legal Agent is infrastructure for judgment — not a replacement for it.

**Happy reviewing.**

---

## Appendix — sample `.env` sanity checklist

Before opening a PR or sharing your laptop screen:

- `JWT_SECRET_KEY` is random and not the example string
- `OPENAI_API_KEY` belongs to a project with spend alerts
- `DATABASE_URL` matches Compose credentials when using Docker
- `LANGCHAIN_TRACING_V2` is disabled in prod unless SOC2 controls allow it
- `CORS_ORIGINS` lists only trusted UI hosts (no wildcards in prod)

---

## Appendix — local directory permissions

Ensure `backend/` is writable so `.venv` and pytest caches can be created. On macOS with SIP, avoid storing the repo inside cloud-synced folders that strip `+x` bits from helper scripts — re-run `chmod +x scripts/*.sh` if Git checkouts drop execute permission.

---

## Appendix — Compose service naming

Container names (`legal-agent-db`, etc.) are explicit for support threads. If you operate multiple clones, override `COMPOSE_PROJECT_NAME` or adjust `name:` in `docker-compose.yml` to avoid collisions.

---

## Appendix — future worker enablement

Uncomment the `worker` service stub after you add `arq`/`celery` dependencies and a worker entrypoint. Until then, rely on FastAPI `BackgroundTasks` for short jobs only.

---

## Appendix — Postgres extensions

Beyond `vector`, you may eventually require `pg_trgm` for fuzzy text matches or `btree_gin` for composite patterns — document each extension in Alembic revisions with rollback notes.

---

## Appendix — example risk review conversation (fictional)

1. **Reviewer:** "System flagged uncapped consequential damages waiver."
2. **Engineer:** "Rule engine hit keyword triple + playbook similarity 0.91 — trace `abc123` in LangSmith."
3. **Reviewer:** "Accepting redline v2 — please log approval."

Stories like this become training data for better UX copy — capture them anonymized.

---

## Appendix — keyboard shortcuts (TBD)

Frontend executor owns shortcuts — list here once the command palette ships (`/` search, `⌘K`, etc.).

---

## Appendix — color-blind safe UI guidance

Risk heatmaps should not rely solely on red/green hues — pair color with icons, numeric severity, and text labels for accessibility compliance.

---

## Appendix — internationalization (future)

If MSAs arrive bilingual, store `language` metadata on `Document` rows and branch OCR + prompts accordingly. Do not assume English-only regex in `rule_engine.py` long-term.

---

## Appendix — contract hash chain (advanced)

For immutable integrity proofs, consider hashing normalized text + prior audit hash into each new `Audit` row (Merkle-lite). Legal teams occasionally ask for tamper evidence beyond database ACLs.

---

## Appendix — budget guardrails

Set monthly OpenAI budget alerts in the provider console **and** track internal `tokens_out` metrics. Tie breaker: prefer reducing max tokens before swapping to lower-quality models for critical clauses.

---

## Appendix — sample weekly standup template

- Incidents: (none / links)
- AI eval metrics: schema validity %, cost/contract
- Playbook changes merged:
- Customer demos scheduled:
- Blockers:

Paste into your tracker of choice.

---

## Appendix — git hygiene for monorepos

- `git status` at repo root should be the default — nested repos confuse beginners.
- Consider `git config status.showUntrackedFiles normal` if `frontend/.git` remains transiently.

---

## Appendix — naming: Legal Agent vs legal-agent

Use **Legal Agent** in prose, `legal-agent` for package/Compose/docker image slugs, and `legal_agent` for SQL identifiers matching `POSTGRES_DB`.