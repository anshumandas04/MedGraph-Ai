from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class EvidenceResponse(BaseModel):
    id: uuid.UUID
    signal_id: uuid.UUID
    event_id: Optional[uuid.UUID]
    document_id: Optional[uuid.UUID]
    page_number: Optional[int]
    excerpt: Optional[str]
    role: str
    document_filename: Optional[str] = None
    event_title: Optional[str] = None

class SignalResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    signal_type: str
    title: str
    description: str
    severity: str
    confidence: float
    status: str
    evidence: List[EvidenceResponse]
    created_at: datetime

class SignalReviewRequest(BaseModel):
    decision: str
    comment: Optional[str] = None
