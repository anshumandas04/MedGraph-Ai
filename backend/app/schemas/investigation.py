from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import uuid

class InvestigationResultResponse(BaseModel):
    id: uuid.UUID
    value: Optional[str]
    unit: Optional[str]
    reference_range: Optional[str]
    is_abnormal: Optional[bool]
    test_date: Optional[date]
    event_id: uuid.UUID

class InvestigationResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    name: str
    category: str
    results: List[InvestigationResultResponse]
