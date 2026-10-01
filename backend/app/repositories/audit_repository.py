from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.audit import AuditLog, Feedback
import uuid

async def log(db: AsyncSession, user_id: uuid.UUID, action: str, resource_type: str, resource_id: uuid.UUID, details: dict, ip: str):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip
    )
    db.add(entry)
    await db.flush()
    return entry

async def create_feedback(db: AsyncSession, feedback_data: dict):
    fb = Feedback(**feedback_data)
    db.add(fb)
    await db.flush()
    return fb
