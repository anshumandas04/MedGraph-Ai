"""Local record search with citations from stored OCR pages."""
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access import assert_patient_access
from app.core.security import get_current_user
from app.db.models.event import HealthEvent
from app.db.models.user import User
from app.db.session import get_db
from app.services.search_service import search_patient_chunks

router = APIRouter()


class SearchRequest(BaseModel):
    query: str


@router.post("/patients/{patient_id}/search")
async def search_records(
    patient_id: uuid.UUID,
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await assert_patient_access(patient_id, db, current_user)
    query = body.query.strip()
    if not query:
        return {"answer": "Enter a question or search term.", "citations": [], "related_events": []}

    matches = await search_patient_chunks(db, patient_id, query, limit=5)
    citations = []
    seen_documents = set()
    for score, chunk, document in matches:
        key = (document.id, chunk.page_number)
        if key in seen_documents:
            continue
        seen_documents.add(key)
        citations.append({
            "document_id": str(document.id),
            "document_name": document.original_filename,
            "page_number": chunk.page_number,
            "excerpt": chunk.content[:500],
            "confidence": min(0.95, 0.5 + score * 0.05),
        })

    terms = {word.casefold() for word in query.split() if len(word) > 1}
    event_result = await db.execute(
        select(HealthEvent)
        .where(HealthEvent.patient_id == patient_id)
        .order_by(HealthEvent.event_date)
    )
    related = []
    for event in event_result.scalars().all():
        evidence = " ".join([event.title or "", event.description or "", event.entity_name or "", event.source_excerpt or ""]).casefold()
        if terms and any(term in evidence for term in terms):
            related.append({
                "id": str(event.id), "event_type": event.event_type,
                "event_date": str(event.event_date) if event.event_date else None,
                "title": event.title, "description": event.description,
                "source_document_id": str(event.source_document_id) if event.source_document_id else None,
            })
    excerpts = [item["excerpt"] for item in citations]
    answer = (
        "Matching passages from the available records:\n\n" + "\n\n".join(excerpts)
        if excerpts else "No matching evidence was found in the available records."
    )
    return {"answer": answer, "citations": citations, "related_events": related}
