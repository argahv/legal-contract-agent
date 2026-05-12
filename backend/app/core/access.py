"""Role-aware access helpers — elevated roles operate across all tenant documents."""

from __future__ import annotations

from uuid import UUID

from app.models.enums import UserRole
from app.models.user import User

_FULL_TENANT_ACCESS_ROLES = frozenset({UserRole.SUPER_ADMIN, UserRole.ADMIN})


def user_has_full_tenant_access(user: User) -> bool:
    """List or open any document (not only those owned by the user)."""
    return UserRole(user.role) in _FULL_TENANT_ACCESS_ROLES


def user_owns_document(*, document_owner_id: UUID, user: User) -> bool:
    return document_owner_id == user.id


def can_access_owned_document(*, document_owner_id: UUID, user: User) -> bool:
    """Owner, admin, or super-admin may read document-bound resources."""
    return user_has_full_tenant_access(user) or user_owns_document(
        document_owner_id=document_owner_id,
        user=user,
    )
