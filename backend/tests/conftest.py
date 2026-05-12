import os

os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-change-me-please")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-called")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

if os.environ["DATABASE_URL"].startswith("sqlite"):
    import pgvector.sqlalchemy as pgmod
    from sqlalchemy.dialects.sqlite import JSON

    class SqliteVector:
        def __new__(cls, dimensions: int) -> JSON:  # noqa: ARG003
            return JSON()

    pgmod.Vector = SqliteVector  # type: ignore[misc, assignment]

import pytest_asyncio
from app.db.base import Base
from app.db.session import engine
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture(autouse=True)
async def reset_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
