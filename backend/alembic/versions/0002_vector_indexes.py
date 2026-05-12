"""ivfflat indexes — accelerates cosine retrieval at scale (Postgres-only)."""

from __future__ import annotations

from alembic import op

revision = "0002_vector_indexes"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS playbook_entries_embedding_ivfflat
        ON playbook_entries
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS clauses_embedding_ivfflat
        ON clauses
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS playbook_entries_embedding_ivfflat")
    op.execute("DROP INDEX IF EXISTS clauses_embedding_ivfflat")
