from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models.document import Document, DocumentPage
import uuid

async def get_by_id(db: AsyncSession, doc_id: uuid.UUID):
    stmt = select(Document).where(Document.id == doc_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_for_patient(db: AsyncSession, patient_id: uuid.UUID, page: int = 1, size: int = 50):
    stmt = select(Document).where(Document.patient_id == patient_id).offset((page-1)*size).limit(size)
    res = await db.execute(stmt)
    return res.scalars().all()

async def create(db: AsyncSession, doc_data: dict):
    doc = Document(**doc_data)
    db.add(doc)
    await db.flush()
    return doc

async def update_status(db: AsyncSession, doc_id: uuid.UUID, status: str, error: str = None):
    stmt = update(Document).where(Document.id == doc_id).values(processing_status=status, processing_error=error)
    await db.execute(stmt)
    await db.flush()

async def get_pages(db: AsyncSession, doc_id: uuid.UUID):
    stmt = select(DocumentPage).where(DocumentPage.document_id == doc_id).order_by(DocumentPage.page_number)
    res = await db.execute(stmt)
    return res.scalars().all()
