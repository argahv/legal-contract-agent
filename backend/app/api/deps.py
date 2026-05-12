"""FastAPI dependency graph — keeps routers declarative and sessions request-scoped."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Annotated
from uuid import UUID

import jwt
import structlog
from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import TokenClaims, decode_access_token
from app.db.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session


def settings_dep() -> Settings:
    return get_settings()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")
    token = credentials.credentials
    try:
        claims = decode_access_token(settings, token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid access token") from exc

    user = await UserRepository(session).get_by_id(UUID(claims.sub))
    if user is None:
        raise UnauthorizedError("User not found")
    return user


def require_role(*roles: UserRole) -> Callable[..., User]:
    async def _inner(user: User = Depends(get_current_user)) -> User:
        role = UserRole(user.role)
        if role not in roles:
            raise ForbiddenError("Insufficient role")
        return user

    return _inner


def get_request_id() -> str:
    """Reads correlation id bound by `RequestContextMiddleware` for structured logging."""

    ctx = structlog.contextvars.get_contextvars()
    return str(ctx.get("request_id", ""))


def decode_access_claims_optional(
    token: str | None,
    *,
    settings: Settings,
) -> TokenClaims | None:
    if token is None:
        return None
    try:
        return decode_access_token(settings, token)
    except (
        jwt.PyJWTError,
        KeyError,
        TypeError,
        ValueError,
        ValidationError,
    ):
        # decode_access_token uses dict access + Pydantic; failures are not always PyJWT errors.
        return None
