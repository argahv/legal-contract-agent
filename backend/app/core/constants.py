"""Shared numeric constants decoupled from ORM modules to avoid import cycles."""

# text-embedding-3-small default dimension; must match Alembic vector(...) and OpenAI embedding model.
EMBEDDING_DIMENSIONS: int = 1536
