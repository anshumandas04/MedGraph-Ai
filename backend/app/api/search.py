"""Search / Ask MedGraph API routes."""
import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy import select, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.search import SearchChunk
from app.db.models.document import Document
from app.db.models.event import HealthEvent
from app.core.security import get_current_user
from app.core.config import settings
from app.services.ai.openai_provider import OpenAIProvider

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
    """Search patient records using RAG pipeline."""
    query = body.query.strip()
    if not query:
        return {"answer": "Please enter a question.", "citations": [], "related_events": []}

    # Step 1: Embed query and search using pgvector
    from app.services.ai.openai_provider import OpenAIProvider
    ai = OpenAIProvider()
    
    try:
        embed_resp = await ai.client.embeddings.create(input=[query], model="text-embedding-3-small")
        query_embedding = embed_resp.data[0].embedding
    except Exception:
        query_embedding = None

    import os
    if query_embedding and "postgresql" in os.getenv("DATABASE_URL", ""):
        try:
            # Vector search using pgvector cosine distance (<=>)
            chunk_result = await db.execute(
                select(SearchChunk, SearchChunk.embedding.cosine_distance(query_embedding).label('distance'))
                .join(Document)
                .where(Document.patient_id == patient_id)
                .order_by('distance')
                .limit(5)
            )
            # SQLAlchemy returns rows as (SearchChunk, distance)
            top_chunks = [(row[0], 1.0 - row[1]) for row in chunk_result.all()]
        except Exception as e:
            # Fallback if DB doesn't support vector ops
            query_embedding = None
            
    if not query_embedding or "postgresql" not in os.getenv("DATABASE_URL", ""):
        # Fallback to simple keyword search if embedding fails or using SQLite
        keywords = query.lower().split()
        chunk_result = await db.execute(
            select(SearchChunk)
            .join(Document)
            .where(Document.patient_id == patient_id)
            .limit(50)
        )
        all_chunks = chunk_result.scalars().all()
        scored = []
        for chunk in all_chunks:
            content_lower = (chunk.content or "").lower()
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scored.append((chunk, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        top_chunks = scored[:5]

    # Step 2: Get related events
    event_result = await db.execute(
        select(HealthEvent)
        .where(HealthEvent.patient_id == patient_id)
        .order_by(HealthEvent.event_date)
    )
    all_events = event_result.scalars().all()

    # Filter events relevant to query
    relevant_events = []
    for event in all_events:
        text = f"{event.title} {event.description or ''} {event.entity_name or ''}".lower()
        if any(kw in text for kw in keywords):
            relevant_events.append(event)

    # Step 3: Build context and generate answer
    context_parts = [chunk.content for chunk, _ in top_chunks]
    context = "\n---\n".join(context_parts)

    events_context = [
        {
            "type": e.event_type,
            "date": str(e.event_date) if e.event_date else "unknown",
            "title": e.title,
            "description": e.description or "",
        }
        for e in relevant_events[:10]
    ]

    # Use AI provider
    ai_provider = OpenAIProvider()
    answer_result = await ai_provider.generate_answer(query, context, events_context)

    # Step 4: Build citations
    citations = []
    seen_docs = set()
    for chunk, score in top_chunks:
        if chunk.document_id not in seen_docs:
            doc_result = await db.execute(
                select(Document).where(Document.id == chunk.document_id)
            )
            doc = doc_result.scalar_one_or_none()
            if doc:
                citations.append({
                    "document_id": str(doc.id),
                    "document_name": doc.original_filename,
                    "page_number": chunk.page_number,
                    "excerpt": chunk.content[:200] if chunk.content else "",
                    "confidence": min(0.95, 0.5 + score * 0.1),
                })
                seen_docs.add(chunk.document_id)

    # Step 5: Format related events
    related = [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "event_date": str(e.event_date) if e.event_date else None,
            "title": e.title,
            "description": e.description,
            "source_document_id": str(e.source_document_id) if e.source_document_id else None,
        }
        for e in relevant_events[:10]
    ]

    return {
        "answer": answer_result.answer,
        "citations": citations,
        "related_events": related,
    }
