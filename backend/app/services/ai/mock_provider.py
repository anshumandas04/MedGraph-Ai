import re
from typing import Any
from .base import AIProvider, ExtractionResult, ClassificationResult, AnswerResult

class MockAIProvider(AIProvider):
    async def extract_events(self, text: str, document_type: str = "") -> ExtractionResult:
        events = []
        
        # Simple regex matching for dates
        date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|January|February|March|April|May|June|July|August|September|October|November|December)\b'
        dates = re.findall(date_pattern, text)
        default_date = dates[0] if dates else "2023-01-01"

        # Medication patterns
        med_pattern = r'\b(prescribed|started|discontinued)\s+([A-Z][a-z]+)\b'
        med_matches = re.findall(med_pattern, text)
        for action, med in med_matches:
            event_type = "MEDICATION_STARTED" if action in ["prescribed", "started"] else "MEDICATION_STOPPED"
            events.append({
                "event_type": event_type,
                "event_date": default_date,
                "title": f"Medication {action}: {med}",
                "description": f"Patient was {action} {med}.",
                "confidence": 0.85,
                "entity_name": med,
            })
            
        # Test patterns
        test_pattern = r'\b(MRI|CT|X-ray|blood test|HbA1c|hemoglobin|cholesterol)\s+(recommended|result|completed)\b'
        test_matches = re.findall(test_pattern, text)
        for test, action in test_matches:
            event_type = "TEST_RECOMMENDED" if action == "recommended" else "TEST_COMPLETED"
            events.append({
                "event_type": event_type,
                "event_date": default_date,
                "title": f"{test} {action}",
                "description": f"{test} was {action}.",
                "confidence": 0.9,
                "entity_name": test,
            })

        # Consultation
        if re.search(r'\b(consultation|appointment|visit)\b', text, re.IGNORECASE):
            events.append({
                "event_type": "CONSULTATION",
                "event_date": default_date,
                "title": "Clinical Consultation",
                "description": "Patient had a clinical consultation.",
                "confidence": 0.95,
                "entity_name": "Consultation",
            })
            
        return ExtractionResult(events=events, confidence=0.8, raw_response="Mock extraction complete.")
    
    async def classify_document(self, text: str) -> ClassificationResult:
        if "discharge" in text.lower():
            return ClassificationResult(document_type="DISCHARGE_SUMMARY", confidence=0.9)
        if "prescription" in text.lower() or "mg" in text.lower():
            return ClassificationResult(document_type="PRESCRIPTION", confidence=0.85)
        if "result" in text.lower() or "lab" in text.lower():
            return ClassificationResult(document_type="LAB_REPORT", confidence=0.9)
        
        return ClassificationResult(document_type="CLINICAL_NOTE", confidence=0.7)
    
    async def generate_answer(self, question: str, context: str, events: list[dict]) -> AnswerResult:
        if not context:
            return AnswerResult(answer="I could not find evidence for this in the available records.", citations=[], confidence=0.0)
            
        return AnswerResult(
            answer="Based on the context, here is the answer derived from available records.",
            citations=[{"document_id": "doc_1", "page": 1, "excerpt": "Sample excerpt from context."}],
            confidence=0.8
        )
    
    async def generate_summary(self, text: str) -> str:
        sentences = text.split(".")
        summary = ". ".join(sentences[:3]) + "." if len(sentences) > 3 else text
        return f"Document Summary: {summary}"
