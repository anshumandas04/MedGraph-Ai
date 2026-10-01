from pydantic import BaseModel
from typing import Optional, List, Any
import uuid

class CitationResponse(BaseModel):
    document_id: uuid.UUID
    document_name: str
    page_number: int
    excerpt: str
    confidence: float

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    answer: str
    citations: List[CitationResponse]
    related_events: List[Any]
