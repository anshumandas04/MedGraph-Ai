from datetime import date
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin, TimestampMixin

class Patient(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "patients"

    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    date_of_birth: Mapped[date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String)
    medical_record_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

class PatientAccess(Base, UUIDMixin):
    __tablename__ = "patient_access"
    
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    access_level: Mapped[str] = mapped_column(String)
    granted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    from datetime import datetime, timezone
    from sqlalchemy import DateTime, func
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
