from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models.signal import Signal, SignalEvidence
import uuid
from datetime import datetime, timezone

async def get_by_id(db: AsyncSession, signal_id: uuid.UUID):
    stmt = select(Signal).where(Signal.id == signal_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_for_patient(db: AsyncSession, patient_id: uuid.UUID, status=None, signal_type=None):
    stmt = select(Signal).where(Signal.patient_id == patient_id)
    if status:
        stmt = stmt.where(Signal.status == status)
    if signal_type:
        stmt = stmt.where(Signal.signal_type == signal_type)
    res = await db.execute(stmt)
    return res.scalars().all()

async def create(db: AsyncSession, signal_data: dict):
    signal = Signal(**signal_data)
    db.add(signal)
    await db.flush()
    return signal

async def create_evidence(db: AsyncSession, evidence_data: dict):
    evidence = SignalEvidence(**evidence_data)
    db.add(evidence)
    await db.flush()
    return evidence

async def review(db: AsyncSession, signal_id: uuid.UUID, user_id: uuid.UUID, decision: str, comment: str):
    stmt = update(Signal).where(Signal.id == signal_id).values(
        status=decision,
        reviewed_by=user_id,
        review_comment=comment,
        reviewed_at=datetime.now(timezone.utc)
    )
    await db.execute(stmt)
    await db.flush()

async def get_evidence(db: AsyncSession, signal_id: uuid.UUID):
    stmt = select(SignalEvidence).where(SignalEvidence.signal_id == signal_id)
    res = await db.execute(stmt)
    return res.scalars().all()
