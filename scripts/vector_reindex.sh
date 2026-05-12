#!/usr/bin/env bash
#
# Rebuild playbook_embeddings via OpenAI-compatible API (OpenAI or OpenRouter).
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose -f "$ROOT/docker-compose.yml")

if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  echo "→ embed_playbook_vectors --force (local venv)"
  cd "$ROOT/backend" && PYTHONPATH=. .venv/bin/python -m scripts.embed_playbook_vectors --force
  exit 0
fi

if command -v docker >/dev/null 2>&1; then
  echo "→ embed_playbook_vectors --force (one-shot backend container)"
  "${COMPOSE[@]}" run --rm backend sh -lc 'PYTHONPATH=. python -m scripts.embed_playbook_vectors --force'
  exit 0
fi

echo "No backend/.venv and no docker — install venv (\`make backend.install\`) or start Docker." >&2
exit 1
