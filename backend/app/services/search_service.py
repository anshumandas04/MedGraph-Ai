import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.search import SearchChunk
from app.services.ai.base import AIProvider

def chunk_document(text: str, chunk_size=500, overlap=100) -> list[str]:
    chunks = []
    if not text:
        return chunks
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

async def create_chunks(db: AsyncSession, document_id: str, pages: list[dict]):
    from app.services.ai.openai_provider import OpenAIProvider
    ai = OpenAIProvider()
    
    for page in pages:
        text = page.get("text", "")
        chunks = chunk_document(text)
        
        # Batch create embeddings
        if chunks:
            try:
                response = await ai.client.embeddings.create(
                    input=chunks,
                    model="text-embedding-3-small"
                )
                embeddings = [data.embedding for data in response.data]
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Embedding failed: {e}")
                embeddings = [None] * len(chunks)
        else:
            embeddings = []
            
        for i, c in enumerate(chunks):
            chunk = SearchChunk(
                id=uuid.uuid4(),
                document_id=uuid.UUID(document_id),
                page_number=page.get("page_number", 1),
                chunk_index=i,
                content=c,
                embedding=embeddings[i]
            )
            db.add(chunk)
    await db.commit()

async def search(db: AsyncSession, patient_id: str, query: str, ai_provider: AIProvider):
    # This is handled directly in api/search.py currently
    pass
