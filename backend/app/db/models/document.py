from datetime import date
from typing import Optional
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Date, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin, TimestampMixin

class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    filename: Mapped[str] = mapped_column(String)
    original_filename: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    file_size: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String)
    document_type: Mapped[str] = mapped_column(String)
    document_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    processing_status: Mapped[str] = mapped_column(String, index=True)
    processing_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

class DocumentPage(Base, UUIDMixin):
    __tablename__ = "document_pages"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    from datetime import datetime, timezone
    from sqlalchemy import DateTime, func
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
