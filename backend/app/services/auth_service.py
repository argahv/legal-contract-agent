"""Auth orchestration — isolates password policy + audit side-effects from HTTP routers."""

from __future__ import annotations

from uuid import UUID

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationAppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.enums import AuditAction, UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPair, UserCreate
from app.services.audit_service import AuditService


class AuthService:
    """Application service wrapping repositories for identity workflows."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._users = UserRepository(session)
        self._audit = AuditService(session)

    async def register(self, *, payload: UserCreate) -> User:
        if payload.role == UserRole.SUPER_ADMIN:
            raise ValidationAppError(
                f"Role {UserRole.SUPER_ADMIN.value} cannot be assigned via self-registration",
            )
        if await self._users.email_exists(payload.email):
            raise ConflictError("Email already registered")
        user = User(
            email=str(payload.email).lower(),
            hashed_password=hash_password(payload.password),
            role=payload.role.value,
        )
        await self._users.add(user)
        await self._audit.record(
            actor_id=user.id,
            action=AuditAction.REGISTER,
            entity_type="user",
            entity_id=str(user.id),
            payload={"email": user.email},
        )
        return user

    async def authenticate(self, *, email: str, password: str) -> User:
        user = await self._users.get_by_email(email.lower())
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid credentials")
        await self._audit.record(
            actor_id=user.id,
            action=AuditAction.LOGIN,
            entity_type="user",
            entity_id=str(user.id),
        )
        return user

    def issue_tokens(self, *, user: User) -> TokenPair:
        access = create_access_token(settings=self._settings, subject=user.id, role=user.role)
        refresh = create_refresh_token(settings=self._settings, subject=user.id, role=user.role)
        return TokenPair(access_token=access, refresh_token=refresh)

    async def refresh_tokens(self, *, refresh_token: str) -> TokenPair:
        try:
            claims = decode_refresh_token(self._settings, refresh_token)
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid refresh token") from exc
        user_id = UUID(claims.sub)
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User no longer exists")
        await self._audit.record(
            actor_id=user.id,
            action=AuditAction.TOKEN_REFRESH,
            entity_type="user",
            entity_id=str(user.id),
        )
        return self.issue_tokens(user=user)
