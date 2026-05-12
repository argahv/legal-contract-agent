"""Async engine + session factory — pool tuned for concurrent review workloads."""

from collections.abc import AsyncIterator

from app.core.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def create_engine_and_sessionmaker():
    settings = get_settings()
    engine_kwargs: dict = {
        "pool_size": settings.sqlalchemy_pool_size,
        "max_overflow": settings.sqlalchemy_max_overflow,
        "pool_timeout": settings.sqlalchemy_pool_timeout_seconds,
        "pool_recycle": settings.sqlalchemy_pool_recycle_seconds,
    }
    if settings.database_url.startswith("sqlite"):
        engine_kwargs = {"poolclass": NullPool}

    engine = create_async_engine(settings.database_url, **engine_kwargs)
    session_factory = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)
    return engine, session_factory


engine, AsyncSessionLocal = create_engine_and_sessionmaker()


def rebind_engine_and_session() -> None:
    """Recreate global engine/session after tests toggle DATABASE_URL via settings cache reset."""

    global engine, AsyncSessionLocal
    get_settings.cache_clear()
    engine.sync_engine.dispose()
    engine, AsyncSessionLocal = create_engine_and_sessionmaker()


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI DI provider — yields a transactional unit of work scoped to the request."""
    async with AsyncSessionLocal() as session:
        yield session
