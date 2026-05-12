"""Promote an existing user to `super_admin` by email (JWT must be re-issued — log in again)."""

from __future__ import annotations

import asyncio
import sys

from app.db.session import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.user import User
from sqlalchemy import update


async def main(email: str) -> None:
    email_l = email.strip().lower()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            update(User)
            .where(User.email == email_l)
            .values(role=UserRole.SUPER_ADMIN.value),
        )
        await session.commit()
        rc = getattr(result, "rowcount", None)
        if rc == 0:
            print(f"No user with email {email_l!r}", file=sys.stderr)
            sys.exit(1)
    print(f"Updated {email_l} -> {UserRole.SUPER_ADMIN.value}. Log out and back in to refresh tokens.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: PYTHONPATH=. python scripts/promote_super_admin.py user@example.com",
            file=sys.stderr,
        )
        sys.exit(2)
    asyncio.run(main(sys.argv[1]))
