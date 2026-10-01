from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import uuid

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    medical_record_number: str

class PatientResponse(PatientCreate):
    id: uuid.UUID
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class PatientSummary(BaseModel):
    id: uuid.UUID
    name: str
    document_count: int
    event_count: int
    open_signals: int
    medication_count: int = 0
    investigation_count: int = 0

