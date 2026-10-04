import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai.base import AIProvider, ExtractionResult, ClassificationResult, AnswerResult

logger = get_logger(__name__)

class OpenAIProvider(AIProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
        self.model = settings.OPENAI_MODEL

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
            logger.error(
                "ai.classification.failed",
                exception_type=type(e).__name__,
                http_status=getattr(e, "status_code", None),
            )
            return ClassificationResult(document_type="OTHER", confidence=0.0)

    async def extract_events(self, text: str, document_type: str = "") -> ExtractionResult:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Extract only explicit healthcare facts from this {document_type} page. "
                            "Return one JSON object with an events array and no prose. Each event may contain "
                            "event_type, event_date, title, description, entity_name, value, unit, source_excerpt, "
                            "and confidence. Use event_type values CONSULTATION, MEDICATION_STARTED, "
                            "MEDICATION_STOPPED, MEDICATION_CONTINUED, MEDICATION_CHANGED, TEST_RECOMMENDED, "
                            "TEST_COMPLETED, TEST_RESULT, TEST_MENTIONED, FOLLOWUP_RECOMMENDED, "
                            "FOLLOWUP_COMPLETED, DIAGNOSIS_DOCUMENTED, SYMPTOM_DOCUMENTED, PROCEDURE, REFERRAL, "
                            "DISCHARGE, ALLERGY_REPORTED, ALLERGY_STATUS_REPORTED, or OTHER. Use an empty events "
                            "array only when no explicit facts can be extracted. Do not invent dates, values, or facts."
                        ),
                    },
                    {"role": "user", "content": text[:6000]}
                ],
                # Prefer interoperable JSON mode for OpenAI-compatible providers,
                # including Gemini; do not rely on the provider's JSON Schema subset.
                response_format={"type": "json_object"},
                temperature=0.1
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
            extracted = data.get("events", [])
            if not isinstance(extracted, list) or any(not isinstance(item, dict) for item in extracted):
                raise ValueError("The model returned an invalid events list")
            return ExtractionResult(events=extracted, confidence=0.8, raw_response=raw)
        except Exception as e:
            logger.error(
                "ai.extraction.failed",
                exception_type=type(e).__name__,
                http_status=getattr(e, "status_code", None),
            )
            raise RuntimeError(f"AI event extraction failed ({type(e).__name__})") from e

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
            logger.error(
                "ai.answer_generation.failed",
                exception_type=type(e).__name__,
                http_status=getattr(e, "status_code", None),
            )
            return AnswerResult(answer="Failed to generate answer.", citations=[], confidence=0.0)

    async def generate_summary(self, text: str) -> str:
        return "Summary"
