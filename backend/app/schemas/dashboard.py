from pydantic import BaseModel
from typing import Optional, List, Any

class DashboardResponse(BaseModel):
    total_documents: int
    total_events: int
    open_signals: int
    total_medications: int
    total_investigations: int
    recent_documents: List[Any] = []
    recent_signals: List[Any] = []

class ResearchDashboardResponse(BaseModel):
    documents_processed: int
    events_extracted: int
    signals_generated: int
    signals_verified: int
    signals_dismissed: int
    avg_confidence: float
    signal_distribution: dict
    processing_failures: int

class EvaluationDetail(BaseModel):
    test_case: str
    expected: Any
    predicted: Any
    correct: bool
    evidence: Any
    confidence: float

class EvaluationResult(BaseModel):
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    evidence_accuracy: float
    details: List[EvaluationDetail]
