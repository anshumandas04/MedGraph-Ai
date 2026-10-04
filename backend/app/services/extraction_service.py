"""Persist locally extracted events and their medication/investigation projections."""
import re
import uuid
from collections import Counter
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.event import HealthEvent
from app.db.models.investigation import Investigation, InvestigationEvent
from app.db.models.medication import Medication, MedicationEvent
from app.services.ai.base import AIProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


def normalize_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    if re.search(r"\b(in|after|within|next)\s+\d+\s+(day|week|month|year)s?\b", date_str, re.I):
        return None
    try:
        if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", date_str.strip()):
            return date.fromisoformat(date_str.strip())
        from dateutil.parser import parse
        return parse(date_str, fuzzy=False, dayfirst=True).date()
    except (ValueError, OverflowError, TypeError):
        return None


def normalize_medication_name(name: str | None) -> str:
    if not name:
        return ""
    name = re.sub(r"\b\d+(?:\.\d+)?\s*(mg|ml|g|mcg|units?|tablet|capsule|pill)s?\b", "", name, flags=re.IGNORECASE)
    return " ".join(name.split()).strip().lower()


def merge_duplicate_events(events: list[dict]) -> list[dict]:
    seen = set()
    merged = []
    for event in events:
        key = (
            event.get("event_type"), event.get("entity_name"), event.get("event_date"),
            event.get("value"), event.get("source_excerpt") or event.get("description"),
        )
        if key not in seen:
            seen.add(key)
            merged.append(event)
    return merged


async def _project_medication(db: AsyncSession, patient_uuid: uuid.UUID, event: HealthEvent, event_data: dict):
    name = normalize_medication_name(event.entity_name)
    if not name:
        return
    query = await db.execute(select(Medication).where(Medication.patient_id == patient_uuid, Medication.name == name))
    medication = query.scalar_one_or_none()
    kind = event.event_type
    if medication is None:
        medication = Medication(
            id=uuid.uuid4(), patient_id=patient_uuid, name=name,
            dosage=event_data.get("value"), status="DISCONTINUED" if kind == "MEDICATION_STOPPED" else "CURRENT",
            start_date=event.event_date if kind != "MEDICATION_STOPPED" else None,
            end_date=event.event_date if kind == "MEDICATION_STOPPED" else None,
        )
        db.add(medication)
        await db.flush()
    else:
        if event_data.get("value"):
            medication.dosage = event_data["value"]
        if kind == "MEDICATION_STOPPED":
            medication.status = "DISCONTINUED"
            medication.end_date = event.event_date
        else:
            medication.status = "CURRENT"
            medication.start_date = medication.start_date or event.event_date
            medication.end_date = None
    db.add(MedicationEvent(
        id=uuid.uuid4(), medication_id=medication.id,
        event_id=event.id, action=kind.removeprefix("MEDICATION_"),
    ))


async def _project_investigation(db: AsyncSession, patient_uuid: uuid.UUID, event: HealthEvent, event_data: dict):
    name = (event.entity_name or "").strip()
    if not name:
        return
    query = await db.execute(select(Investigation).where(Investigation.patient_id == patient_uuid, Investigation.name == name))
    investigation = query.scalar_one_or_none()
    if investigation is None:
        investigation = Investigation(
            id=uuid.uuid4(), patient_id=patient_uuid, name=name,
            category="LAB" if event.event_type == "TEST_RESULT" else "DIAGNOSTIC",
        )
        db.add(investigation)
        await db.flush()
    db.add(InvestigationEvent(
        id=uuid.uuid4(), investigation_id=investigation.id, event_id=event.id,
        value=event_data.get("value"), unit=event_data.get("unit"),
        test_date=event.event_date,
    ))


async def extract_events(
    db: AsyncSession,
    text: str,
    document_type: str,
    patient_id: str,
    document_id: str,
    ai_provider: AIProvider,
    page_number: int = 1,
):
    """Extract only facts grounded in the provided page text; never infer current date."""
    logger.info(
        "document.page_extraction.started",
        page_number=page_number,
        source_characters=len(text),
        document_type=document_type,
    )
    result = await ai_provider.extract_events(text, document_type)
    patient_uuid = uuid.UUID(patient_id)
    document_uuid = uuid.UUID(document_id)
    events_data = merge_duplicate_events(result.events)
    event_types = dict(Counter(
        str(item.get("event_type") or "OTHER").upper()
        for item in events_data
    ))

    for data in events_data:
        kind = str(data.get("event_type") or "OTHER").upper()
        raw_date = data.get("event_date")
        entity_name = data.get("entity_name")
        if kind.startswith("MEDICATION"):
            entity_name = normalize_medication_name(entity_name)
        event = HealthEvent(
            id=uuid.uuid4(),
            patient_id=patient_uuid,
            source_document_id=document_uuid,
            source_page=page_number,
            source_excerpt=(data.get("source_excerpt") or data.get("description") or text)[:500],
            event_type=kind,
            event_date=normalize_date(raw_date),
            title=(data.get("title") or "Event extracted from document")[:255],
            description=data.get("description"),
            confidence=max(0.0, min(1.0, float(data.get("confidence", 0.5) or 0.0))),
            entity_name=entity_name,
            value=str(data["value"]) if data.get("value") is not None else None,
            unit=data.get("unit"),
            status="ACTIVE",
            is_active=True,
        )
        db.add(event)
        await db.flush()
        if kind.startswith("MEDICATION_"):
            await _project_medication(db, patient_uuid, event, data)
        elif kind in {"TEST_RESULT", "TEST_RECOMMENDED", "TEST_COMPLETED", "TEST_MENTIONED"}:
            await _project_investigation(db, patient_uuid, event, data)
    logger.info(
        "document.page_extraction.completed",
        page_number=page_number,
        source_characters=len(text),
        candidate_count=len(events_data),
        event_types=event_types,
        ai_provider=type(ai_provider).__name__,
    )
    return events_data
