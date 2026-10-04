"""Local, patient-scoped text indexing and retrieval."""
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import Document
from app.db.models.search import SearchChunk


def chunk_document(text: str, chunk_size: int = 700, overlap: int = 100) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")
    chunks: list[str] = []
    start = 0
    source = (text or "").strip()
    while start < len(source):
        end = min(start + chunk_size, len(source))
        piece = source[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == len(source):
            break
        start = end - overlap
    return chunks


async def create_chunks(db: AsyncSession, document_id: str, pages: list[dict]):
    doc_uuid = uuid.UUID(document_id)
    await db.execute(delete(SearchChunk).where(SearchChunk.document_id == doc_uuid))
    for page in pages:
        chunks = chunk_document(page.get("text", ""))
        for index, content in enumerate(chunks):
            db.add(SearchChunk(
                id=uuid.uuid4(),
                document_id=doc_uuid,
                page_number=page.get("page_number", 1),
                chunk_index=index,
                content=content,
                embedding=None,
            ))
    await db.flush()


async def search_patient_chunks(db: AsyncSession, patient_id: uuid.UUID, query: str, limit: int = 5):
    """Simple deterministic retrieval. Documents are scoped before text is ranked."""
    terms = {t.casefold() for t in query.split() if len(t) > 1}
    if not terms:
        return []
    result = await db.execute(
        select(SearchChunk, Document)
        .join(Document, SearchChunk.document_id == Document.id)
        .where(Document.patient_id == patient_id)
    )
    scored = []
    for chunk, document in result.all():
        normalized = (chunk.content or "").casefold()
        score = sum(normalized.count(term) for term in terms)
        if score:
            scored.append((score, chunk, document))
    scored.sort(key=lambda item: (-item[0], item[1].page_number, item[1].chunk_index))
    return scored[:limit]
