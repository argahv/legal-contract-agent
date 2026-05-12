# Legal Agent — developer CLI shortcuts.
# Requires Docker Compose v2 (`docker compose`) for compose-backed targets.

SHELL := /bin/bash
ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
COMPOSE ?= docker compose

BACKEND_DIR := $(ROOT)backend
FRONTEND_DIR := $(ROOT)frontend
BACKEND_PY := $(BACKEND_DIR)/.venv/bin/python
BACKEND_PIP := $(BACKEND_DIR)/.venv/bin/pip
BACKEND_RUN := cd $(BACKEND_DIR) && PYTHONPATH=. $(BACKEND_PY)

export PYTHONPATH := $(BACKEND_DIR)

.PHONY: help setup up down logs ps restart \
	backend.install backend.stop backend.run backend.test backend.lint backend.migrate backend.seed backend.embed \
	frontend.install frontend.dev frontend.build frontend.test frontend.lint frontend.typecheck \
	db.shell db.reset vector.index langsmith.open fmt check

help: ## Show available targets (default)
	@echo "Legal Agent — make targets"
	@echo ""
	@grep -hE '^[a-zA-Z0-9][a-zA-Z0-9._-]*:.*?##' "$(ROOT)Makefile" \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

setup: ## DB (Compose), migrations, playbook seed + embeddings (see scripts/dev_bootstrap.sh)
	@bash "$(ROOT)scripts/full_setup.sh"

up: ## Start db + backend + frontend via Docker Compose (background)
	$(COMPOSE) -f "$(ROOT)docker-compose.yml" up -d

down: ## Stop Compose stack (keeps named volumes unless you add -v)
	$(COMPOSE) -f "$(ROOT)docker-compose.yml" down

logs: ## Tail Compose logs
	$(COMPOSE) -f "$(ROOT)docker-compose.yml" logs -f

ps: ## Compose service status
	$(COMPOSE) -f "$(ROOT)docker-compose.yml" ps

restart: down up ## `down` then `up`

# --- Backend (local venv — no global pip installs) --------------------------------

backend.install: ## Create backend/.venv and install runtime + dev deps
	@test -d "$(BACKEND_DIR)" || (echo "missing backend/" && exit 1)
	@test -f "$(BACKEND_DIR)/requirements.txt" || (echo "missing $(BACKEND_DIR)/requirements.txt — run from repo root" && exit 1)
	@test -f "$(BACKEND_DIR)/requirements-dev.txt" || (echo "missing $(BACKEND_DIR)/requirements-dev.txt" && exit 1)
	cd "$(BACKEND_DIR)" && python3 -m venv .venv && \
		"$(BACKEND_PIP)" install -U pip && \
		"$(BACKEND_PIP)" install -r "$(BACKEND_DIR)/requirements.txt" && \
		"$(BACKEND_PIP)" install -r "$(BACKEND_DIR)/requirements-dev.txt"

backend.stop: ## Kill process listening on port 8000 (fixes "Address already in use" for backend.run)
	@PIDS=$$(lsof -t -iTCP:8000 -sTCP:LISTEN 2>/dev/null || true); \
	if [ -n "$$PIDS" ]; then echo "Stopping PID(s): $$PIDS"; kill $$PIDS 2>/dev/null || true; sleep 1; \
	else echo "Nothing listening on TCP 8000"; fi

backend.run: ## Run API locally with reload (expects configured .env)
	@test -x "$(BACKEND_PY)" || (echo "run: make backend.install" && exit 1)
	cd "$(BACKEND_DIR)" && PYTHONPATH=. "$(BACKEND_PY)" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend.test: ## Run pytest in backend/.venv
	@test -x "$(BACKEND_PY)" || (echo "run: make backend.install" && exit 1)
	cd "$(BACKEND_DIR)" && "$(BACKEND_DIR)/.venv/bin/pytest"

backend.lint: ## Ruff check + format verification on scripts + tests (app/ owned by API executor)
	@test -x "$(BACKEND_DIR)/.venv/bin/ruff" || (echo "run: make backend.install (needs requirements-dev.txt)" && exit 1)
	cd "$(BACKEND_DIR)" && .venv/bin/ruff check scripts tests
	cd "$(BACKEND_DIR)" && .venv/bin/ruff format --check scripts tests

backend.migrate: ## Alembic upgrade (requires backend/alembic.ini)
	@test -x "$(BACKEND_DIR)/.venv/bin/alembic" || (echo "run: make backend.install" && exit 1)
	@test -f "$(BACKEND_DIR)/alembic.ini" || (echo "missing backend/alembic.ini — add migrations first" && exit 1)
	cd "$(BACKEND_DIR)" && .venv/bin/alembic upgrade head

backend.seed: ## Insert starter playbook rows (idempotent)
	@test -x "$(BACKEND_PY)" || (echo "run: make backend.install" && exit 1)
	$(BACKEND_RUN) -m scripts.seed_playbook

backend.embed: ## Populate playbook pgvector embeddings (needs embedding API access)
	@test -x "$(BACKEND_PY)" || (echo "run: make backend.install" && exit 1)
	$(BACKEND_RUN) -m scripts.embed_playbook_vectors

# --- Frontend ---------------------------------------------------------------------

frontend.install: ## npm ci in frontend/
	cd "$(FRONTEND_DIR)" && npm ci

frontend.dev: ## Next.js dev server ( Turbopack per package.json )
	cd "$(FRONTEND_DIR)" && npm run dev

frontend.build: ## Production build
	cd "$(FRONTEND_DIR)" && npm run build

frontend.test: ## npm test when declared; otherwise prints a skip message
	cd "$(FRONTEND_DIR)" && node -e "const p=require('./package.json');process.exit(p.scripts&&p.scripts.test?0:1)" && npm run test || (echo "frontend.test: no npm test script yet — skipping" && exit 0)

frontend.lint: ## ESLint (Next.js preset)
	cd "$(FRONTEND_DIR)" && npm run lint

frontend.typecheck: ## TypeScript noEmit (no package.json script required)
	cd "$(FRONTEND_DIR)" && npx tsc --noEmit

# --- Data + vectors ---------------------------------------------------------------

db.shell: ## psql into the Compose Postgres role
	@test -f "$(ROOT).env" || (echo "create .env from .env.example first" && exit 1)
	set -a && source "$(ROOT).env" && set +a && \
		$(COMPOSE) -f "$(ROOT)docker-compose.yml" exec db psql -U "$${POSTGRES_USER:-legal}" -d "$${POSTGRES_DB:-legal_agent}"

db.reset: ## Drop/create DB schema volume helpers — see scripts/reset_db.sh
	@bash "$(ROOT)scripts/reset_db.sh"

vector.index: ## Re-embed all playbook rows (force; OpenAI-compatible embeddings API)
	@bash "$(ROOT)scripts/vector_reindex.sh"

langsmith.open: ## Open LangSmith in your default browser
	@command -v open >/dev/null 2>&1 && open "https://smith.langchain.com" || \
		(command -v xdg-open >/dev/null 2>&1 && xdg-open "https://smith.langchain.com") || \
		echo "Open https://smith.langchain.com manually"

# --- Repo-wide format / verify ----------------------------------------------------

fmt: ## Ruff format (backend scripts/tests) + Prettier (markdown & workflow YAML)
	@test -x "$(BACKEND_DIR)/.venv/bin/ruff" || (echo "run: make backend.install" && exit 1)
	cd "$(BACKEND_DIR)" && .venv/bin/ruff format scripts tests
	cd "$(ROOT)" && npx --yes prettier@3 --write "README.md" "docs/**/*.md" ".github/**/*.yml" 2>/dev/null || \
		echo "fmt: prettier skipped (network or npx unavailable)"

check: backend.lint frontend.lint frontend.typecheck backend.test frontend.test ## Lint + typecheck + tests both tiers
