from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date
import uuid

class MedicationResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    name: str
    generic_name: Optional[str]
    dosage: Optional[str]
    frequency: Optional[str]
    route: Optional[str]
    status: str
    start_date: Optional[date]
    end_date: Optional[date]
    events: List[Any] = []

class MedicationTimelineEntry(BaseModel):
    date: Optional[date]
    action: str
    event_id: uuid.UUID
    document_id: Optional[uuid.UUID]
