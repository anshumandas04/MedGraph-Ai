from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.event import HealthEvent, EventRelationship
import uuid

async def get_by_id(db: AsyncSession, event_id: uuid.UUID):
    stmt = select(HealthEvent).where(HealthEvent.id == event_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_for_patient(db: AsyncSession, patient_id: uuid.UUID, event_type=None, start_date=None, end_date=None):
    stmt = select(HealthEvent).where(HealthEvent.patient_id == patient_id)
    if event_type:
        stmt = stmt.where(HealthEvent.event_type == event_type)
    if start_date:
        stmt = stmt.where(HealthEvent.event_date >= start_date)
    if end_date:
        stmt = stmt.where(HealthEvent.event_date <= end_date)
    res = await db.execute(stmt)
    return res.scalars().all()

async def create(db: AsyncSession, event_data: dict):
    event = HealthEvent(**event_data)
    db.add(event)
    await db.flush()
    return event

async def create_relationship(db: AsyncSession, rel_data: dict):
    rel = EventRelationship(**rel_data)
    db.add(rel)
    await db.flush()
    return rel

async def get_relationships(db: AsyncSession, event_id: uuid.UUID):
    stmt = select(EventRelationship).where(
        (EventRelationship.source_event_id == event_id) | (EventRelationship.target_event_id == event_id)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_timeline(db: AsyncSession, patient_id: uuid.UUID):
    stmt = select(HealthEvent).where(HealthEvent.patient_id == patient_id).order_by(HealthEvent.event_date.asc())
    res = await db.execute(stmt)
    return res.scalars().all()
