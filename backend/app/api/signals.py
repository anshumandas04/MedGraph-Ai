"""Signal API routes."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.signal import Signal, SignalEvidence
from app.db.models.document import Document
from app.db.models.event import HealthEvent
from app.db.models.audit import Feedback
from app.core.security import get_current_user
from app.core.access import assert_patient_access
from app.services.signal_service import run_signal_engine

router = APIRouter()


class SignalReviewRequest(BaseModel):
    decision: str  # VERIFY, DISMISS, EDIT, NOT_SURE
    comment: Optional[str] = None


@router.get("/patients/{patient_id}/signals")
async def list_signals(
    patient_id: uuid.UUID,
    status: Optional[str] = None,
    signal_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List signals for a patient with optional filters."""
    await assert_patient_access(patient_id, db, current_user)
    query = select(Signal).where(Signal.patient_id == patient_id)
    if status:
        query = query.where(Signal.status == status)
    if signal_type:
        query = query.where(Signal.signal_type == signal_type)
    query = query.order_by(Signal.created_at.desc())

    result = await db.execute(query)
    signals = result.scalars().all()

    # Attach evidence to each signal
    response = []
    for signal in signals:
        ev_result = await db.execute(
            select(SignalEvidence).where(SignalEvidence.signal_id == signal.id)
        )
        evidence_list = ev_result.scalars().all()

        # Enrich evidence with document filenames
        enriched_evidence = []
        for ev in evidence_list:
            ev_dict = {
                "id": str(ev.id),
                "signal_id": str(ev.signal_id),
                "event_id": str(ev.event_id) if ev.event_id else None,
                "document_id": str(ev.document_id) if ev.document_id else None,
                "page_number": ev.page_number,
                "excerpt": ev.excerpt,
                "role": ev.role,
                "document_filename": None,
                "event_title": None,
            }
            if ev.document_id:
                doc = (await db.execute(
                    select(Document).where(Document.id == ev.document_id)
                )).scalar_one_or_none()
                if doc:
                    ev_dict["document_filename"] = doc.original_filename
            if ev.event_id:
                event = (await db.execute(
                    select(HealthEvent).where(HealthEvent.id == ev.event_id)
                )).scalar_one_or_none()
                if event:
                    ev_dict["event_title"] = event.title
            enriched_evidence.append(ev_dict)

        response.append({
            "id": str(signal.id),
            "patient_id": str(signal.patient_id),
            "signal_type": signal.signal_type,
            "title": signal.title,
            "description": signal.description,
            "severity": signal.severity,
            "confidence": signal.confidence,
            "status": signal.status,
            "evidence": enriched_evidence,
            "created_at": signal.created_at.isoformat() if signal.created_at else None,
            "reviewed_by": str(signal.reviewed_by) if signal.reviewed_by else None,
            "reviewed_at": signal.reviewed_at.isoformat() if signal.reviewed_at else None,
            "review_comment": signal.review_comment,
        })

    return response


@router.get("/signals/{signal_id}")
async def get_signal(
    signal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get signal detail with evidence."""
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    await assert_patient_access(signal.patient_id, db, current_user)

    ev_result = await db.execute(
        select(SignalEvidence).where(SignalEvidence.signal_id == signal_id)
    )
    evidence_list = ev_result.scalars().all()

    enriched_evidence = []
    for ev in evidence_list:
        ev_dict = {
            "id": str(ev.id),
            "signal_id": str(ev.signal_id),
            "event_id": str(ev.event_id) if ev.event_id else None,
            "document_id": str(ev.document_id) if ev.document_id else None,
            "page_number": ev.page_number,
            "excerpt": ev.excerpt,
            "role": ev.role,
            "document_filename": None,
            "event_title": None,
        }
        if ev.document_id:
            doc = (await db.execute(
                select(Document).where(Document.id == ev.document_id)
            )).scalar_one_or_none()
            if doc:
                ev_dict["document_filename"] = doc.original_filename
        if ev.event_id:
            event = (await db.execute(
                select(HealthEvent).where(HealthEvent.id == ev.event_id)
            )).scalar_one_or_none()
            if event:
                ev_dict["event_title"] = event.title
        enriched_evidence.append(ev_dict)

    return {
        "id": str(signal.id),
        "patient_id": str(signal.patient_id),
        "signal_type": signal.signal_type,
        "title": signal.title,
        "description": signal.description,
        "severity": signal.severity,
        "confidence": signal.confidence,
        "status": signal.status,
        "evidence": enriched_evidence,
        "created_at": signal.created_at.isoformat() if signal.created_at else None,
        "reviewed_by": str(signal.reviewed_by) if signal.reviewed_by else None,
        "reviewed_at": signal.reviewed_at.isoformat() if signal.reviewed_at else None,
        "review_comment": signal.review_comment,
    }


@router.post("/signals/{signal_id}/review")
async def review_signal(
    signal_id: uuid.UUID,
    review: SignalReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Review a signal (verify, dismiss, edit, not sure)."""
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    await assert_patient_access(signal.patient_id, db, current_user, write=True)

    status_map = {
        "VERIFY": "VERIFIED",
        "DISMISS": "DISMISSED",
        "EDIT": "NEEDS_VERIFICATION",
        "NOT_SURE": "NEEDS_VERIFICATION",
    }
    new_status = status_map.get(review.decision, "NEEDS_VERIFICATION")

    signal.status = new_status
    signal.reviewed_by = current_user.id
    signal.reviewed_at = datetime.now(timezone.utc)
    signal.review_comment = review.comment

    # Create feedback record
    db.add(Feedback(
        id=uuid.uuid4(),
        user_id=current_user.id,
        signal_id=signal_id,
        feedback_type=review.decision,
        comment=review.comment,
    ))

    await db.flush()
    return {"message": "Signal reviewed", "status": new_status}


@router.post("/patients/{patient_id}/signals/detect")
async def detect_signals(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run signal engine for a patient."""
    await assert_patient_access(patient_id, db, current_user, write=True)
    signals = await run_signal_engine(db, patient_id)
    await db.flush()
    return {
        "message": "Signal engine completed",
        "signals_generated": len(signals),
    }
