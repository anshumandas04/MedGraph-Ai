from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
import uuid

async def get_by_id(db: AsyncSession, user_id: uuid.UUID):
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def get_by_email(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def create(db: AsyncSession, user_data: dict):
    user = User(**user_data)
    db.add(user)
    await db.flush()
    return user

async def list_users(db: AsyncSession):
    stmt = select(User)
    res = await db.execute(stmt)
    return res.scalars().all()
