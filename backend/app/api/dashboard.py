"""Dashboard API routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.document import Document
from app.db.models.event import HealthEvent
from app.db.models.signal import Signal, SignalEvidence
from app.db.models.medication import Medication
from app.db.models.investigation import Investigation
from app.core.security import get_current_user, require_role
from app.core.access import assert_patient_access
from app.core.logging import recent_logs

router = APIRouter()


@router.get("/admin/logs")
async def get_application_logs(
    limit: int = Query(default=100, ge=1, le=500),
    level: str = Query(default="ALL", pattern="^(ALL|DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    current_user: User = Depends(require_role(["ADMIN"])),
):
    """Return recent redacted backend logs to administrators only."""
    return {
        "storage": "in-memory",
        "retained_limit": 2000,
        "returned": len(recent_logs(limit=limit, level=level)),
        "logs": recent_logs(limit=limit, level=level),
        "note": "Logs are held in memory and reset when the backend restarts. Request and application messages omit request bodies and query strings.",
    }


@router.get("/patients/{patient_id}/dashboard")
async def get_dashboard(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get patient dashboard data."""
    await assert_patient_access(patient_id, db, current_user)
    total_docs = (await db.execute(
        select(func.count(Document.id)).where(Document.patient_id == patient_id)
    )).scalar() or 0

    total_events = (await db.execute(
        select(func.count(HealthEvent.id)).where(HealthEvent.patient_id == patient_id)
    )).scalar() or 0

    open_signals = (await db.execute(
        select(func.count(Signal.id)).where(
            Signal.patient_id == patient_id, Signal.status == "OPEN"
        )
    )).scalar() or 0

    total_meds = (await db.execute(
        select(func.count(Medication.id)).where(Medication.patient_id == patient_id)
    )).scalar() or 0

    total_inv = (await db.execute(
        select(func.count(Investigation.id)).where(Investigation.patient_id == patient_id)
    )).scalar() or 0

    # Recent documents
    recent_docs_result = await db.execute(
        select(Document)
        .where(Document.patient_id == patient_id)
        .order_by(Document.created_at.desc())
        .limit(5)
    )
    recent_docs = [
        {
            "id": str(d.id), "original_filename": d.original_filename,
            "document_type": d.document_type, "document_date": str(d.document_date) if d.document_date else None,
            "processing_status": d.processing_status, "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in recent_docs_result.scalars().all()
    ]

    # Recent signals
    recent_sigs_result = await db.execute(
        select(Signal, func.count(SignalEvidence.id).label("evidence_count"))
        .outerjoin(SignalEvidence, SignalEvidence.signal_id == Signal.id)
        .where(Signal.patient_id == patient_id, Signal.status == "OPEN")
        .group_by(Signal.id)
        .order_by(Signal.created_at.desc())
        .limit(5)
    )
    recent_signals = [
        {
            "id": str(s.id), "signal_type": s.signal_type, "title": s.title,
            "severity": s.severity, "confidence": s.confidence, "status": s.status,
            "evidence_count": evidence_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s, evidence_count in recent_sigs_result.all()
    ]

    return {
        "total_documents": total_docs,
        "total_events": total_events,
        "open_signals": open_signals,
        "total_medications": total_meds,
        "total_investigations": total_inv,
        "recent_documents": recent_docs,
        "recent_signals": recent_signals,
    }


@router.get("/admin/dashboard")
async def get_research_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"])),
):
    """Admin/research dashboard metrics."""
    docs_processed = (await db.execute(
        select(func.count(Document.id)).where(Document.processing_status == "COMPLETED")
    )).scalar() or 0

    events_extracted = (await db.execute(
        select(func.count(HealthEvent.id))
    )).scalar() or 0

    signals_generated = (await db.execute(
        select(func.count(Signal.id))
    )).scalar() or 0

    signals_verified = (await db.execute(
        select(func.count(Signal.id)).where(Signal.status == "VERIFIED")
    )).scalar() or 0

    signals_dismissed = (await db.execute(
        select(func.count(Signal.id)).where(Signal.status == "DISMISSED")
    )).scalar() or 0

    avg_conf = (await db.execute(
        select(func.avg(HealthEvent.confidence))
    )).scalar() or 0.0

    processing_failures = (await db.execute(
        select(func.count(Document.id)).where(Document.processing_status == "FAILED")
    )).scalar() or 0

    # Signal distribution
    dist_result = await db.execute(
        select(Signal.signal_type, func.count(Signal.id))
        .group_by(Signal.signal_type)
    )
    signal_distribution = {row[0]: row[1] for row in dist_result.all()}

    return {
        "documents_processed": docs_processed,
        "events_extracted": events_extracted,
        "signals_generated": signals_generated,
        "signals_verified": signals_verified,
        "signals_dismissed": signals_dismissed,
        "avg_confidence": round(float(avg_conf), 3),
        "signal_distribution": signal_distribution,
        "processing_failures": processing_failures,
    }


@router.get("/admin/evaluation")
async def get_evaluation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"])),
):
    """Do not report accuracy without human-adjudicated reference labels."""
    return {
        "available": False,
        "precision": None,
        "recall": None,
        "f1": None,
        "false_positive_rate": None,
        "evidence_accuracy": None,
        "details": [],
        "note": "Evaluation requires human-adjudicated reference labels; no validated labels are configured.",
    }
