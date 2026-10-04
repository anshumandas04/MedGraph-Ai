"""Medications API routes."""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.medication import Medication, MedicationEvent
from app.db.models.event import HealthEvent
from app.core.security import get_current_user
from app.core.access import assert_patient_access

router = APIRouter()


@router.get("/patients/{patient_id}/medications")
async def list_medications(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List medications for a patient with event history."""
    await assert_patient_access(patient_id, db, current_user)
    result = await db.execute(
        select(Medication)
        .where(Medication.patient_id == patient_id)
        .order_by(Medication.name)
    )
    medications = result.scalars().all()

    response = []
    for med in medications:
        # Get medication events
        me_result = await db.execute(
            select(MedicationEvent)
            .where(MedicationEvent.medication_id == med.id)
        )
        med_events = me_result.scalars().all()

        events_list = []
        for me in med_events:
            he_result = await db.execute(
                select(HealthEvent).where(HealthEvent.id == me.event_id)
            )
            he = he_result.scalar_one_or_none()
            events_list.append({
                "date": str(he.event_date) if he and he.event_date else None,
                "action": me.action,
                "event_id": str(me.event_id),
                "document_id": str(he.source_document_id) if he and he.source_document_id else None,
            })

        response.append({
            "id": str(med.id),
            "patient_id": str(med.patient_id),
            "name": med.name,
            "generic_name": med.generic_name,
            "dosage": med.dosage,
            "frequency": med.frequency,
            "route": med.route,
            "status": med.status,
            "start_date": str(med.start_date) if med.start_date else None,
            "end_date": str(med.end_date) if med.end_date else None,
            "events": sorted(events_list, key=lambda x: x["date"] or ""),
        })

    return response
