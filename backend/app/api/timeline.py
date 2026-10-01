"""Timeline API routes."""
import uuid
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.event import HealthEvent, EventRelationship
from app.core.security import get_current_user

router = APIRouter()


@router.get("/patients/{patient_id}/timeline")
async def get_timeline(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chronological timeline of events grouped by date."""
    result = await db.execute(
        select(HealthEvent)
        .where(HealthEvent.patient_id == patient_id)
        .order_by(HealthEvent.event_date.desc())
    )
    events = result.scalars().all()

    # Group by date
    grouped = defaultdict(list)
    for event in events:
        date_key = str(event.event_date) if event.event_date else "Unknown"

        # Get relationships for this event
        rel_result = await db.execute(
            select(EventRelationship).where(
                (EventRelationship.source_event_id == event.id) |
                (EventRelationship.target_event_id == event.id)
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

        grouped[date_key].append({
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
        })

    timeline = [
        {"date": date_key, "events": events_list}
        for date_key, events_list in sorted(grouped.items(), reverse=True)
    ]
    return timeline
