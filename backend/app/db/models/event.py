from datetime import date
from typing import Optional
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Date, ForeignKey, Text, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin, TimestampMixin

class HealthEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "health_events"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    event_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    source_document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"))
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    entity_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class EventAttribute(Base, UUIDMixin):
    __tablename__ = "event_attributes"
    
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("health_events.id"))
    key: Mapped[str] = mapped_column(String)
    value: Mapped[str] = mapped_column(String)
    
    from datetime import datetime, timezone
    from sqlalchemy import DateTime, func
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class EventRelationship(Base, UUIDMixin):
    __tablename__ = "event_relationships"
    
    source_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("health_events.id"), index=True)
    target_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("health_events.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    
    from datetime import datetime, timezone
    from sqlalchemy import DateTime, func
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
