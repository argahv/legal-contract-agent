#!/usr/bin/env bash
#
# Idempotent local bootstrap:
#   - ensure .env exists
#   - start Postgres (pgvector) via Compose
#   - run Alembic migrations when configured
#   - seed baseline playbook rows
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE=(docker compose -f "$ROOT/docker-compose.yml")

if [[ ! -f "$ROOT/.env" ]]; then
  echo "→ Creating .env from .env.example"
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "!!  Update secrets (JWT_SECRET_KEY, OPENAI_API_KEY) before sharing this workspace."
fi

set -a
# shellcheck disable=SC1090
source "$ROOT/.env"
set +a

USER_NAME="${POSTGRES_USER:-legal}"
DB_NAME="${POSTGRES_DB:-legal_agent}"

echo "→ Starting database (${COMPOSE[*]} up -d db)"
"${COMPOSE[@]}" up -d db

echo "→ Waiting for Postgres healthcheck"
for _ in $(seq 1 90); do
  if "${COMPOSE[@]}" exec -T db pg_isready -U "$USER_NAME" -d "$DB_NAME" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

migrate() {
  if [[ ! -f "$ROOT/backend/alembic.ini" ]]; then
    echo "⚠ backend/alembic.ini not found — skipping migrations (executor adds Alembic scaffold)."
    return 0
  fi

  if [[ -x "$ROOT/backend/.venv/bin/alembic" ]]; then
    echo "→ alembic upgrade head (local venv)"
    (cd "$ROOT/backend" && .venv/bin/alembic upgrade head) && return 0
  fi

  if command -v docker >/dev/null 2>&1; then
    echo "→ alembic upgrade head (one-shot backend container)"
    "${COMPOSE[@]}" run --rm backend sh -lc 'alembic upgrade head' && return 0
  fi

  echo "⚠ No local alembic and docker unavailable — migrations not applied." >&2
  return 0
}

seed_playbook() {
  if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
    echo "→ scripts.seed_playbook (local venv)"
    (cd "$ROOT/backend" && PYTHONPATH=. .venv/bin/python -m scripts.seed_playbook) && return 0
  fi
  if command -v docker >/dev/null 2>&1; then
    echo "→ scripts.seed_playbook (one-shot backend container)"
    "${COMPOSE[@]}" run --rm backend sh -lc 'PYTHONPATH=. python -m scripts.seed_playbook' && return 0
  fi
  echo "⚠ Could not seed playbook — install backend venv or enable Docker." >&2
}

embed_playbook_vectors() {
  if [[ ! -x "$ROOT/backend/.venv/bin/python" ]]; then
    echo "⚠ Skipping playbook embeddings — run \`make backend.install\` for local venv." >&2
    return 0
  fi
  echo "→ scripts.embed_playbook_vectors (local venv — needs LLM-compatible embedding API)"
  if (cd "$ROOT/backend" && PYTHONPATH=. .venv/bin/python -m scripts.embed_playbook_vectors); then
    return 0
  fi
  echo "⚠ Embedding step failed — check OPENROUTER_* / OPENAI_* keys and OPENAI_EMBEDDING_MODEL (OpenRouter: openai/text-embedding-3-small)." >&2
  return 0
}

migrate
seed_playbook || echo "⚠ Seed step reported an error — check database connectivity and migrations."
embed_playbook_vectors

echo ""
echo "==================================================================="
echo " Legal Agent bootstrap complete"
echo " • Database:  docker compose -f \"$ROOT/docker-compose.yml\" ps db"
echo " • API:       make backend.run   (after app.main exists)"
echo " • Full app:  make up"
echo "==================================================================="
