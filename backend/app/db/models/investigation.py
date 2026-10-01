from datetime import date
from typing import Optional
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin, TimestampMixin

class Investigation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "investigations"
    
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String)

class InvestigationEvent(Base, UUIDMixin):
    __tablename__ = "investigation_events"
    
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("investigations.id"))
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("health_events.id"))
    value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reference_range: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_abnormal: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    test_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    from datetime import datetime, timezone
    from sqlalchemy import DateTime, func
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
