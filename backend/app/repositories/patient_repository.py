from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.patient import Patient, PatientAccess
import uuid

async def get_by_id(db: AsyncSession, patient_id: uuid.UUID):
    stmt = select(Patient).where(Patient.id == patient_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_for_user(db: AsyncSession, user_id: uuid.UUID, role: str):
    if role == "ADMIN":
        stmt = select(Patient)
    else:
        stmt = select(Patient).join(PatientAccess).where(PatientAccess.user_id == user_id)
    res = await db.execute(stmt)
    return res.scalars().all()

async def create(db: AsyncSession, patient_data: dict, user_id: uuid.UUID):
    patient = Patient(**patient_data, created_by=user_id)
    db.add(patient)
    await db.flush()
    access = PatientAccess(patient_id=patient.id, user_id=user_id, access_level="ADMIN", granted_by=user_id)
    db.add(access)
    await db.flush()
    return patient

async def check_access(db: AsyncSession, patient_id: uuid.UUID, user_id: uuid.UUID):
    stmt = select(PatientAccess).where(PatientAccess.patient_id == patient_id, PatientAccess.user_id == user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none() is not None
