"""Create missing tables for a fresh research-prototype deployment.

Existing deployments should use Alembic migrations instead of relying on this
create-if-missing bootstrap for schema upgrades.
"""
import asyncio

from sqlalchemy import text

from app.db.base import Base
import app.db.models  # noqa: F401 - register all mapped models
from app.db.session import engine


async def main():
    async with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
