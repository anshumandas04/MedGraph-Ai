"""Investigations API routes."""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.investigation import Investigation, InvestigationEvent
from app.core.security import get_current_user
from app.core.access import assert_patient_access

router = APIRouter()


@router.get("/patients/{patient_id}/investigations")
async def list_investigations(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List investigations with results over time."""
    await assert_patient_access(patient_id, db, current_user)
    result = await db.execute(
        select(Investigation)
        .where(Investigation.patient_id == patient_id)
        .order_by(Investigation.name)
    )
    investigations = result.scalars().all()

    response = []
    for inv in investigations:
        ie_result = await db.execute(
            select(InvestigationEvent)
            .where(InvestigationEvent.investigation_id == inv.id)
            .order_by(InvestigationEvent.test_date)
        )
        inv_events = ie_result.scalars().all()

        results = [
            {
                "id": str(ie.id),
                "value": ie.value,
                "unit": ie.unit,
                "reference_range": ie.reference_range,
                "is_abnormal": ie.is_abnormal,
                "test_date": str(ie.test_date) if ie.test_date else None,
                "event_id": str(ie.event_id),
            }
            for ie in inv_events
        ]

        response.append({
            "id": str(inv.id),
            "patient_id": str(inv.patient_id),
            "name": inv.name,
            "category": inv.category,
            "results": results,
        })

    return response
