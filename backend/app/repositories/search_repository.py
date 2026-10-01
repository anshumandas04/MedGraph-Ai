from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.search import SearchChunk
import uuid

async def create_chunk(db: AsyncSession, chunk_data: dict):
    chunk = SearchChunk(**chunk_data)
    db.add(chunk)
    await db.flush()
    return chunk

async def search_semantic(db: AsyncSession, embedding: list, limit: int = 5):
    # Using pgvector l2 distance
    stmt = select(SearchChunk).order_by(SearchChunk.embedding.l2_distance(embedding)).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

async def search_keyword(db: AsyncSession, query: str, patient_id: uuid.UUID, limit: int = 5):
    # Basic ILIKE search
    stmt = select(SearchChunk).where(SearchChunk.content.ilike(f"%{query}%")).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()
