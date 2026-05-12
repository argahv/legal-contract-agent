# Contributing to Legal Agent

Thanks for improving the contract-review platform. This repository intentionally splits ownership:

- **API surface, domain logic, LangChain chains, FastAPI routers** — keep changes coordinated with the backend owner (`backend/app/`).
- **Root infrastructure** — Docker, Compose, Make targets, CI, and `docs/` evolve through focused PRs that do not surprise parallel tracks.

## Branching model

1. Create a short-lived branch from `main` (or your team's default):  
   `feat/playbook-export`, `fix/ws-reconnect`, `chore/ci-node-22`.
2. Prefer **one logical change per PR** — docs + code may ride together when tightly coupled.
3. Rebase before merge if history is noisy; **avoid force-pushing shared branches**.

## Commit style (Conventional Commits)

Use imperative, scoped prefixes:

| Prefix | When |
| --- | --- |
| `feat:` | user-visible capability |
| `fix:` | bug or regression |
| `docs:` | prose only |
| `chore:` | tooling, deps, CI |
| `refactor:` | internal structure, same behavior |
| `test:` | coverage only |

Examples:

```text
feat(api): add redline batch approval endpoint
fix(ai): guard empty clause spans in extraction chain
docs: expand deployment runbook for Fly.io
```

## Local development loop

1. Copy `.env.example` → `.env` and fill secrets (`JWT_SECRET_KEY`, `OPENAI_API_KEY`).
2. Run `./scripts/dev_bootstrap.sh` to start Postgres and (when present) apply migrations + seed the playbook.
3. **Backend**: `make backend.install && make backend.run` (once `app.main:app` ships).
4. **Frontend**: `make frontend.install && make frontend.dev`.
5. Before opening a PR: `make check` (or run `make backend.lint`, `make frontend.lint`, typechecks, and tests individually).

## Pre-commit

Install hooks once per machine:

```bash
pipx install pre-commit
pre-commit install
```

Hooks cover Ruff on `backend/scripts` + `backend/tests`, Prettier on Markdown/TS/YAML, EOF + YAML hygiene.  
*Reason:* `backend/app/` is mid-flight in another workstream; Ruff is enforced there before global CI flips to full-app lint.

## PR checklist

- [ ] Linked issue or short rationale in the description.
- [ ] `make check` (or CI equivalents) is green locally when feasible.
- [ ] New env vars appear in `.env.example` with comments.
- [ ] User-facing behavior documented in `docs/` or `README.md` when behavior changes.
- [ ] Migrations + rollback story captured if the schema changed.
- [ ] No secrets in commits — rotate anything that leaked.

## Code review expectations

- Prefer **small, reviewable diffs** with context in the description.
- Call out **risk areas**: auth, file uploads, AI prompts, concurrency.
- For AI changes, attach **LangSmith run links** (or trace IDs) when possible.
- Surface **observability impact**: new metrics, logs, trace spans.

## Getting help

Open a draft PR early, or leave notes in the issue tracker with `@mentions` for backend vs frontend owners. When in doubt, favor documentation updates and Makefile ergonomics — they compound.
