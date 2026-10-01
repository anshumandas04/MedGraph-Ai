"""Events API routes."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.event import HealthEvent, EventRelationship
from app.core.security import get_current_user

router = APIRouter()


@router.get("/patients/{patient_id}/events")
async def list_events(
    patient_id: uuid.UUID,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    document_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List events for a patient with optional filters."""
    query = select(HealthEvent).where(HealthEvent.patient_id == patient_id)

    if event_type:
        query = query.where(HealthEvent.event_type == event_type)
    if start_date:
        query = query.where(HealthEvent.event_date >= start_date)
    if end_date:
        query = query.where(HealthEvent.event_date <= end_date)
    if document_id:
        query = query.where(HealthEvent.source_document_id == document_id)

    query = query.order_by(HealthEvent.event_date.desc())
    result = await db.execute(query)
    events = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "patient_id": str(e.patient_id),
            "event_type": e.event_type,
            "event_date": str(e.event_date) if e.event_date else None,
            "title": e.title,
            "description": e.description,
            "confidence": e.confidence,
            "source_document_id": str(e.source_document_id) if e.source_document_id else None,
            "source_page": e.source_page,
            "source_excerpt": e.source_excerpt,
            "value": e.value,
            "unit": e.unit,
            "entity_name": e.entity_name,
            "status": e.status,
        }
        for e in events
    ]


@router.get("/events/{event_id}")
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get event detail with relationships."""
    result = await db.execute(select(HealthEvent).where(HealthEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get relationships
    rel_result = await db.execute(
        select(EventRelationship).where(
            (EventRelationship.source_event_id == event_id) |
            (EventRelationship.target_event_id == event_id)
        )
    )
    relationships = [
        {
            "id": str(r.id),
            "source_event_id": str(r.source_event_id),
            "target_event_id": str(r.target_event_id),
            "relationship_type": r.relationship_type,
            "confidence": r.confidence,
        }
        for r in rel_result.scalars().all()
    ]

    return {
        "id": str(event.id),
        "patient_id": str(event.patient_id),
        "event_type": event.event_type,
        "event_date": str(event.event_date) if event.event_date else None,
        "title": event.title,
        "description": event.description,
        "confidence": event.confidence,
        "source_document_id": str(event.source_document_id) if event.source_document_id else None,
        "source_page": event.source_page,
        "source_excerpt": event.source_excerpt,
        "value": event.value,
        "unit": event.unit,
        "entity_name": event.entity_name,
        "status": event.status,
        "relationships": relationships,
    }


@router.get("/events/{event_id}/relationships")
async def get_event_relationships(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get event relationships."""
    result = await db.execute(
        select(EventRelationship).where(
            (EventRelationship.source_event_id == event_id) |
            (EventRelationship.target_event_id == event_id)
        )
    )
    return [
        {
            "id": str(r.id),
            "source_event_id": str(r.source_event_id),
            "target_event_id": str(r.target_event_id),
            "relationship_type": r.relationship_type,
            "confidence": r.confidence,
        }
        for r in result.scalars().all()
    ]
