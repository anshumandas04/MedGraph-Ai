from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.medication import Medication, MedicationEvent
import uuid

async def list_for_patient(db: AsyncSession, patient_id: uuid.UUID):
    stmt = select(Medication).where(Medication.patient_id == patient_id)
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_by_name(db: AsyncSession, patient_id: uuid.UUID, name: str):
    stmt = select(Medication).where(Medication.patient_id == patient_id, Medication.name == name)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def create(db: AsyncSession, med_data: dict):
    med = Medication(**med_data)
    db.add(med)
    await db.flush()
    return med

async def create_event(db: AsyncSession, med_event_data: dict):
    evt = MedicationEvent(**med_event_data)
    db.add(evt)
    await db.flush()
    return evt
