#!/usr/bin/env bash
#
# Full local setup: .env, Postgres (Compose), Alembic, playbook seed, vector embeddings.
# Destructive reset: use scripts/reset_db.sh instead.
#
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$ROOT/scripts/dev_bootstrap.sh"
