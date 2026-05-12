"""API v1 aggregation — single import surface for the FastAPI factory."""

from __future__ import annotations

from app.api.v1 import ai_stream, approvals, audit, auth, contracts, playbook
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(ai_stream.router, prefix="/ai", tags=["ai"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(playbook.router, prefix="/playbook", tags=["playbook"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
