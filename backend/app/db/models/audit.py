from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import DateTime as SADateTime
from app.db.base import Base, UUIDMixin, TimestampMixin

class AuditLog(Base, UUIDMixin):
    __tablename__ = "audit_logs"
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    resource_type: Mapped[str] = mapped_column(String)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    from sqlalchemy import func
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())

class Feedback(Base, UUIDMixin):
    __tablename__ = "feedback"
    
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    signal_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=True)
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("health_events.id"), nullable=True)
    feedback_type: Mapped[str] = mapped_column(String)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    from sqlalchemy import func
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())

class DocumentProcessingJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_processing_jobs"
    
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    status: Mapped[str] = mapped_column(String)
    started_at: Mapped[Optional[datetime]] = mapped_column(SADateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(SADateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    steps_completed: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
