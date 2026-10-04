"""Create the first admin account from environment variables."""
import asyncio
import os
import uuid

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import async_session_factory, engine


async def main() -> None:
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")
    full_name = os.environ.get("BOOTSTRAP_ADMIN_NAME", "MedGraph Administrator").strip()
    if not email or not password:
        raise SystemExit("Set BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD before running.")
    if len(password) < 14:
        raise SystemExit("Admin password must contain at least 14 characters.")

    try:
        async with async_session_factory() as db:
            admins = await db.execute(select(User.id).where(User.role == "ADMIN").limit(1))
            if admins.scalar_one_or_none():
                raise SystemExit("An admin account already exists; bootstrap is first-admin-only.")
            existing = await db.execute(select(User.id).where(User.email == email))
            if existing.scalar_one_or_none():
                raise SystemExit("That email already belongs to an account; bootstrap made no changes.")
            db.add(User(
                id=uuid.uuid4(), email=email, full_name=full_name,
                hashed_password=hash_password(password), role="ADMIN", is_active=True,
            ))
            await db.commit()
        print(f"Created first admin account for {email}.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
