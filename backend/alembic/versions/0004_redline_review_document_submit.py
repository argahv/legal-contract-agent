"""Redline reviewer workflow + document submit-for-review timestamp."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_redline_submit"
down_revision = "0003_playbook_fts_risk_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "redlines",
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
    )
    op.add_column("redlines", sa.Column("reviewer_comment", sa.Text(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("submitted_for_review_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("redlines", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("documents", "submitted_for_review_at")
    op.drop_column("redlines", "reviewer_comment")
    op.drop_column("redlines", "status")
