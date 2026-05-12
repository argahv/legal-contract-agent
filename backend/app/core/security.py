"""Password hashing and JWT utilities — cryptographic primitives isolated from HTTP layer."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from app.core.config import Settings
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pydantic import BaseModel

password_hasher = PasswordHash((Argon2Hasher(),))

JWT_ACCESS_TYP = "access"
JWT_REFRESH_TYP = "refresh"


class TokenClaims(BaseModel):
    sub: str
    role: str


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(*, settings: Settings, subject: UUID, role: str) -> str:
    expire = datetime.now(tz=UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, str | datetime] = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "typ": JWT_ACCESS_TYP,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(settings: Settings, token: str) -> TokenClaims:
    raw = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if raw.get("typ") not in (JWT_ACCESS_TYP, None):
        raise jwt.InvalidTokenError("Not an access token")
    return TokenClaims(sub=str(raw["sub"]), role=str(raw["role"]))


def create_refresh_token(*, settings: Settings, subject: UUID, role: str) -> str:
    expire = datetime.now(tz=UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload: dict[str, str | datetime] = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "typ": JWT_REFRESH_TYP,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_refresh_token(settings: Settings, token: str) -> TokenClaims:
    raw = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if raw.get("typ") != JWT_REFRESH_TYP:
        raise jwt.InvalidTokenError("Not a refresh token")
    return TokenClaims(sub=str(raw["sub"]), role=str(raw["role"]))
