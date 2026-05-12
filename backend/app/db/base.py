"""SQLAlchemy declarative registry — imports side-effect: registers all mapped classes."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Unified metadata root for Alembic autogeneration and runtime ORM mappings."""
