from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.investigation import Investigation, InvestigationEvent
import uuid

async def list_for_patient(db: AsyncSession, patient_id: uuid.UUID):
    stmt = select(Investigation).where(Investigation.patient_id == patient_id)
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_by_name(db: AsyncSession, patient_id: uuid.UUID, name: str):
    stmt = select(Investigation).where(Investigation.patient_id == patient_id, Investigation.name == name)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def create(db: AsyncSession, inv_data: dict):
    inv = Investigation(**inv_data)
    db.add(inv)
    await db.flush()
    return inv

async def create_event(db: AsyncSession, inv_event_data: dict):
    evt = InvestigationEvent(**inv_event_data)
    db.add(evt)
    await db.flush()
    return evt
