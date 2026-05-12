"""Authentication routes — JWT issuance stays thin; services own password policy + auditing."""

from app.api.deps import get_current_user, get_db, settings_dep
from app.core.config import Settings
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.auth import (
    AuthBundle,
    RefreshRequest,
    TokenPair,
    UserCreate,
    UserLogin,
    UserMe,
    UserRead,
)
from app.services.auth_service import AuthService
from fastapi import APIRouter, Body, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/register", response_model=AuthBundle, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def register(
    request: Request,
    registration: UserCreate = Body(...),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> AuthBundle:
    _ = request
    service = AuthService(session, settings)
    user = await service.register(payload=registration)
    tokens = service.issue_tokens(user=user)
    await session.commit()
    return AuthBundle(user=UserRead.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthBundle)
@limiter.limit("30/minute")
async def login(
    request: Request,
    credentials: UserLogin = Body(...),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> AuthBundle:
    _ = request
    service = AuthService(session, settings)
    user = await service.authenticate(email=str(credentials.email), password=credentials.password)
    tokens = service.issue_tokens(user=user)
    await session.commit()
    return AuthBundle(user=UserRead.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("60/minute")
async def refresh(
    request: Request,
    body: RefreshRequest = Body(...),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> TokenPair:
    _ = request
    service = AuthService(session, settings)
    tokens = await service.refresh_tokens(refresh_token=body.refresh_token)
    await session.commit()
    return tokens


@router.get("/me", response_model=UserMe)
async def me(current_user: User = Depends(get_current_user)) -> UserMe:
    return UserMe.model_validate(current_user)
