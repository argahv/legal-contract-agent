"""Playbook full-text search (Postgres) + risk judgment cache (all backends)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_playbook_fts_risk_cache"
down_revision = "0002_vector_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    op.create_table(
        "risk_judgment_cache",
        sa.Column("key_hash", sa.String(64), primary_key=True),
        sa.Column("model_name", sa.String(256), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("level", sa.String(32), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    if bind.dialect.name != "postgresql":
        return

    op.execute(
        """
        ALTER TABLE playbook_entries
        ADD COLUMN IF NOT EXISTS search_vector tsvector
        """
    )
    op.execute(
        """
        UPDATE playbook_entries SET search_vector =
          setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
          setweight(to_tsvector('english', coalesce(guideline, '')), 'B')
        WHERE search_vector IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS playbook_entries_search_vector_idx
        ON playbook_entries USING gin (search_vector)
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION playbook_entries_tsvector_update()
        RETURNS trigger AS $$
        BEGIN
          NEW.search_vector :=
            setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(NEW.guideline, '')), 'B');
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute("DROP TRIGGER IF EXISTS playbook_entries_tsvector_trigger ON playbook_entries")
    op.execute(
        """
        CREATE TRIGGER playbook_entries_tsvector_trigger
        BEFORE INSERT OR UPDATE OF title, guideline ON playbook_entries
        FOR EACH ROW EXECUTE PROCEDURE playbook_entries_tsvector_update()
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS playbook_entries_tsvector_trigger ON playbook_entries")
        op.execute("DROP FUNCTION IF EXISTS playbook_entries_tsvector_update()")
        op.execute("DROP INDEX IF EXISTS playbook_entries_search_vector_idx")
        op.execute("ALTER TABLE playbook_entries DROP COLUMN IF EXISTS search_vector")

    op.drop_table("risk_judgment_cache")
