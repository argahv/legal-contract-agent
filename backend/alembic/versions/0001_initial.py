"""initial schema — extensions first, then SQLAlchemy metadata for parity with ORM."""

from __future__ import annotations

import app.models  # noqa: F401  - register SQLAlchemy mappers
from alembic import op
from app.db.base import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
