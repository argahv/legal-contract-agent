#!/usr/bin/env bash
#
# Destructive reset: drops the application database inside the Compose volume and recreates it,
# re-applies the pgvector extension, runs Alembic, and reseeds the playbook.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE=(docker compose -f "$ROOT/docker-compose.yml")

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Missing .env — copy from .env.example first." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ROOT/.env"
set +a

USER_NAME="${POSTGRES_USER:-legal}"
DB_NAME="${POSTGRES_DB:-legal_agent}"

echo "→ Ensuring database container is running"
"${COMPOSE[@]}" up -d db

echo "→ Waiting for readiness"
for _ in $(seq 1 60); do
  if "${COMPOSE[@]}" exec -T db pg_isready -U "$USER_NAME" -d "$DB_NAME" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "→ Dropping and recreating database ${DB_NAME} (all data in this volume will be lost)"
"${COMPOSE[@]}" exec -T db psql -U "$USER_NAME" -d postgres <<SQL
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS "${DB_NAME}";
CREATE DATABASE "${DB_NAME}";
SQL

"${COMPOSE[@]}" exec -T db psql -U "$USER_NAME" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"

if [[ -f "$ROOT/backend/alembic.ini" ]]; then
  if [[ -x "$ROOT/backend/.venv/bin/alembic" ]]; then
    echo "→ alembic upgrade head (local)"
    (cd "$ROOT/backend" && .venv/bin/alembic upgrade head)
  else
    echo "→ alembic upgrade head (container)"
    "${COMPOSE[@]}" run --rm backend sh -lc 'alembic upgrade head'
  fi
else
  echo "⚠ Skipping migrations — backend/alembic.ini missing"
fi

if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  echo "→ seed_playbook (local)"
  (cd "$ROOT/backend" && PYTHONPATH=. .venv/bin/python -m scripts.seed_playbook) || true
  echo "→ embed_playbook_vectors (local)"
  (cd "$ROOT/backend" && PYTHONPATH=. .venv/bin/python -m scripts.embed_playbook_vectors) || true
else
  echo "→ seed_playbook (container)"
  "${COMPOSE[@]}" run --rm backend sh -lc 'PYTHONPATH=. python -m scripts.seed_playbook' || true
  echo "→ embed_playbook_vectors (container)"
  "${COMPOSE[@]}" run --rm backend sh -lc 'PYTHONPATH=. python -m scripts.embed_playbook_vectors' || true
fi

echo "Database reset complete."
