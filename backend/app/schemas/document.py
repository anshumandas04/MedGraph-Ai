from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
import uuid

class PageResponse(BaseModel):
    id: uuid.UUID
    page_number: int
    text_content: Optional[str]
    ocr_confidence: Optional[float]

class DocumentResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    original_filename: str
    document_type: str
    document_date: Optional[date]
    processing_status: str
    file_size: int
    created_at: datetime

class DocumentDetail(DocumentResponse):
    pages: List[PageResponse]
