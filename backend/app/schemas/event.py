from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
import uuid

class HealthEventResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    event_type: str
    event_date: Optional[date]
    title: str
    description: Optional[str]
    confidence: float
    source_document_id: uuid.UUID
    source_page: Optional[int]
    source_excerpt: Optional[str]
    value: Optional[str]
    unit: Optional[str]
    entity_name: Optional[str]
    status: Optional[str]

class EventRelationshipResponse(BaseModel):
    id: uuid.UUID
    source_event_id: uuid.UUID
    target_event_id: uuid.UUID
    relationship_type: str
    confidence: float

class TimelineEntry(BaseModel):
    date: Optional[date]
    events: List[HealthEventResponse]
