"""Patient-scoped authorization dependencies for API routes."""
import uuid

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.models.document import Document
from app.db.models.event import HealthEvent
from app.db.models.patient import Patient, PatientAccess
from app.db.models.signal import Signal
from app.db.models.user import User
from app.db.session import get_db


async def assert_patient_access(
    patient_id: uuid.UUID,
    db: AsyncSession,
    user: User,
    *,
    write: bool = False,
) -> Patient:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if user.role == "ADMIN":
        return patient

    result = await db.execute(select(PatientAccess).where(
        PatientAccess.patient_id == patient_id,
        PatientAccess.user_id == user.id,
    ))
    access = result.scalar_one_or_none()
    if access is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if user.role == "PATIENT" and access.access_level != "OWNER":
        raise HTTPException(status_code=404, detail="Patient not found")
    if write and user.role not in {"CLINICIAN"} and access.access_level not in {"ADMIN", "WRITE", "OWNER"}:
        raise HTTPException(status_code=403, detail="Write access is required")
    return patient


async def authorized_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Patient:
    return await assert_patient_access(patient_id, db, user)


async def authorized_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Document:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    await assert_patient_access(document.patient_id, db, user)
    return document


async def authorized_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HealthEvent:
    result = await db.execute(select(HealthEvent).where(HealthEvent.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    await assert_patient_access(event.patient_id, db, user)
    return event


async def authorized_signal(
    signal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Signal:
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    await assert_patient_access(signal.patient_id, db, user)
    return signal
