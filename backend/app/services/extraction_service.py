import re
import uuid
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.event import HealthEvent
from app.services.ai.base import AIProvider

logger = logging.getLogger(__name__)

def normalize_date(date_str: str) -> datetime:
    try:
        from dateutil.parser import parse
        # If it's a relative date like "after 3 months", this parser might fail.
        # But this is a basic fallback.
        parsed = parse(date_str, fuzzy=True)
        return parsed.date()
    except Exception:
        # Avoid creating events on the exact current day when we don't know the date
        return None

def normalize_medication_name(name: str) -> str:
    if not name: return ""
    name = re.sub(r'\b\d+\s*(mg|ml|g|mcg|tablet|capsule|pill)s?\b', '', name, flags=re.IGNORECASE)
    return name.strip().lower()

def merge_duplicate_events(events: list[dict]) -> list[dict]:
    seen = set()
    merged = []
    for e in events:
        key = (e.get('event_type'), e.get('entity_name'), e.get('event_date'))
        if key not in seen:
            seen.add(key)
            merged.append(e)
    return merged

async def extract_events(db: AsyncSession, text: str, document_type: str, patient_id: str, document_id: str, ai_provider: AIProvider):
    logger.info(f"Extracting events for document {document_id}")
    result = await ai_provider.extract_events(text, document_type)
    
    events_data = merge_duplicate_events(result.events)
    
    for e_data in events_data:
        raw_date = e_data.get("event_date")
        normalized_date = normalize_date(raw_date) if raw_date else None

        entity_name = e_data.get("entity_name")
        if e_data.get("event_type", "").startswith("MEDICATION"):
            entity_name = normalize_medication_name(entity_name)
        
        event = HealthEvent(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            source_document_id=uuid.UUID(document_id),
            event_type=e_data.get("event_type", "OTHER"),
            event_date=normalized_date,
            title=e_data.get("title", "Event"),
            description=e_data.get("description"),
            confidence=e_data.get("confidence", 0.5),
            entity_name=entity_name,
            status="ACTIVE",
            is_active=True
        )
        db.add(event)
    
    await db.commit()
