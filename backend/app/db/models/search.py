import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin

from sqlalchemy import JSON

from app.core.config import settings

if "postgresql" in settings.DATABASE_URL:
    from pgvector.sqlalchemy import Vector
    EmbeddingType = Vector(1536)
else:
    from sqlalchemy import JSON
    EmbeddingType = JSON

class SearchChunk(Base, UUIDMixin):
    __tablename__ = "search_chunks"
    
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(EmbeddingType, nullable=True)
    
    from datetime import datetime, timezone
    from sqlalchemy import DateTime, func
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
