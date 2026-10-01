import os
import json
import logging
from openai import AsyncOpenAI
from app.services.ai.base import AIProvider, ExtractionResult, ClassificationResult, AnswerResult

logger = logging.getLogger(__name__)

class OpenAIProvider(AIProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy-key"))
        self.model = os.getenv("LLM_MODEL", "gpt-4o")

    async def classify_document(self, text: str) -> ClassificationResult:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a clinical document classifier. Output JSON with fields 'document_type' (e.g. CONSULTATION_NOTE, PRESCRIPTION, LAB_REPORT, RADIOLOGY_REPORT, DISCHARGE_SUMMARY, FOLLOWUP_NOTE, OTHER) and 'confidence'."},
                    {"role": "user", "content": text[:4000]}
                ],
                response_format={ "type": "json_object" },
                temperature=0.1
            )
            data = json.loads(response.choices[0].message.content)
            return ClassificationResult(
                document_type=data.get("document_type", "OTHER"),
                confidence=data.get("confidence", 0.5)
            )
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return ClassificationResult(document_type="OTHER", confidence=0.0)

    async def extract_events(self, text: str, document_type: str = "") -> ExtractionResult:
        schema = {
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "event_type": {"type": "string", "enum": ["CONSULTATION", "MEDICATION_STARTED", "MEDICATION_STOPPED", "MEDICATION_CONTINUED", "MEDICATION_CHANGED", "TEST_RECOMMENDED", "TEST_COMPLETED", "TEST_RESULT", "FOLLOWUP_RECOMMENDED", "FOLLOWUP_COMPLETED", "DIAGNOSIS_DOCUMENTED", "SYMPTOM_DOCUMENTED", "PROCEDURE", "REFERRAL", "DISCHARGE", "OTHER"]},
                            "event_date": {"type": "string", "description": "YYYY-MM-DD or relative like 'after 3 months'"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "entity_name": {"type": "string"},
                            "confidence": {"type": "number"}
                        },
                        "required": ["event_type", "title"]
                    }
                }
            },
            "required": ["events"]
        }
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"Extract healthcare events from the {document_type} text. Return JSON matching the schema."},
                    {"role": "user", "content": text[:6000]}
                ],
                response_format={"type": "json_schema", "json_schema": {"name": "events", "schema": schema}},
                temperature=0.1
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
            return ExtractionResult(events=data.get("events", []), confidence=0.8, raw_response=raw)
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return ExtractionResult(events=[], confidence=0.0)

    async def generate_answer(self, question: str, context: str, events: list[dict]) -> AnswerResult:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Answer based ONLY on context. Include citations as JSON. Schema: { 'answer': str, 'citations': [{ 'document_id': str, 'page': int, 'excerpt': str }] }"},
                    {"role": "user", "content": f"Context:\n{context}\n\nEvents:\n{json.dumps(events)}\n\nQuestion: {question}"}
                ],
                response_format={ "type": "json_object" },
                temperature=0.1
            )
            data = json.loads(response.choices[0].message.content)
            return AnswerResult(
                answer=data.get("answer", "I could not find an answer."),
                citations=data.get("citations", []),
                confidence=0.9
            )
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return AnswerResult(answer="Failed to generate answer.", citations=[], confidence=0.0)

    async def generate_summary(self, text: str) -> str:
        return "Summary"
