from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

@dataclass
class ExtractionResult:
    events: list[dict]  # list of extracted event dicts
    confidence: float
    raw_response: str = ""

@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    
@dataclass
class AnswerResult:
    answer: str
    citations: list[dict]  # [{document_id, page, excerpt}]
    confidence: float

class AIProvider(ABC):
    @abstractmethod
    async def extract_events(self, text: str, document_type: str = "") -> ExtractionResult:
        """Extract healthcare events from document text."""
        pass
    
    @abstractmethod
    async def classify_document(self, text: str) -> ClassificationResult:
        """Classify document type."""
        pass
    
    @abstractmethod
    async def generate_answer(self, question: str, context: str, events: list[dict]) -> AnswerResult:
        """Generate answer from context with citations."""
        pass
    
    @abstractmethod
    async def generate_summary(self, text: str) -> str:
        """Generate document summary."""
        pass
