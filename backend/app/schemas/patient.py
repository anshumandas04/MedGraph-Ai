from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
import uuid

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    medical_record_number: str

class PatientSelfProfileCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(min_length=1, max_length=40)

    @field_validator("first_name", "last_name", "gender")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required")
        return value

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

