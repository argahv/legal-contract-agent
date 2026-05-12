"""Liveness/readiness endpoints — lightweight checks decoupled from authenticated API surface."""

from __future__ import annotations

from typing import Annotated, Any

from app.api.deps import get_db, settings_dep
from app.core.config import Settings
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
) -> dict[str, Any]:
    db_ok = False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        db_ok = False
        db_error = str(exc)
    else:
        db_error = None

    openai_configured = bool(settings.openai_api_key)
    vector_ready = not settings.database_url.startswith("sqlite")

    ready = db_ok and openai_configured
    return {
        "ready": ready,
        "dependencies": {
            "database": db_ok,
            "openai_configured": openai_configured,
            "pgvector_expected": vector_ready,
        },
        "error": db_error,
    }
