import os

root_dir = r"C:\Users\anshu\.gemini\antigravity\scratch\medgraph"

file_contents = {
    "backend/requirements.txt": """fastapi==0.115.12
uvicorn[standard]==0.34.2
pydantic==2.11.4
pydantic-settings==2.9.1
sqlalchemy[asyncio]==2.0.41
alembic==1.16.2
asyncpg==0.30.0
psycopg2-binary==2.9.10
pgvector==0.3.6
python-jose[cryptography]==3.4.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20
PyMuPDF==1.25.5
Pillow==11.2.1
httpx==0.28.1
pytest==8.4.1
pytest-asyncio==1.0.0
structlog==25.4.0
uuid7==0.1.0
""",
    "backend/app/__init__.py": "",
    "backend/app/core/__init__.py": "",
    "backend/app/core/config.py": """from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    APP_NAME: str = "MedGraph"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://medgraph:medgraph@localhost:5432/medgraph"
    DATABASE_URL_SYNC: str = "postgresql://medgraph:medgraph@localhost:5432/medgraph"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    UPLOAD_DIR: str = "./data/uploads"
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".png", ".jpg", ".jpeg"]
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf", "image/png", "image/jpeg"]
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OCR_PROVIDER: str = "mock"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost"]
    DEMO_MODE: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
""",
    "backend/app/core/security.py": """from datetime import datetime, timedelta, timezone
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.session import get_db
from app.db.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

def require_role(allowed_roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return role_checker
""",
    "backend/app/core/exceptions.py": """from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

class MedGraphException(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}

class DocumentProcessingError(MedGraphException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(500, "DOCUMENT_PROCESSING_ERROR", message, details)

class FileValidationError(MedGraphException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(400, "FILE_VALIDATION_ERROR", message, details)

class AuthorizationError(MedGraphException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(403, "AUTHORIZATION_ERROR", message, details)

class PatientNotFoundError(MedGraphException):
    def __init__(self, message: str = "Patient not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(404, "PATIENT_NOT_FOUND", message, details)

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(MedGraphException)
    async def medgraph_exception_handler(request: Request, exc: MedGraphException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
""",
    "backend/app/core/logging.py": """import structlog
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import uuid

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=logging.INFO)

def get_logger(name: str):
    return structlog.get_logger(name)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        structlog.contextvars.clear_contextvars()
        return response
""",
    "backend/app/db/__init__.py": "",
    "backend/app/db/base.py": """import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
""",
    "backend/app/db/session.py": """from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
""",
    "backend/app/db/models/__init__.py": """from app.db.models.user import User
from app.db.models.patient import Patient, PatientAccess
from app.db.models.document import Document, DocumentPage
from app.db.models.event import HealthEvent, EventAttribute, EventRelationship
from app.db.models.medication import Medication, MedicationEvent
from app.db.models.investigation import Investigation, InvestigationEvent
from app.db.models.signal import Signal, SignalEvidence
from app.db.models.search import SearchChunk
from app.db.models.audit import AuditLog, Feedback, DocumentProcessingJob
""",
    "backend/app/db/models/user.py": """from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean
from app.db.base import Base, UUIDMixin, TimestampMixin

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
""",
    "backend/app/db/models/patient.py": """from datetime import date
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
""",
    "backend/app/db/models/document.py": """from datetime import date
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
""",
    "backend/app/db/models/event.py": """from datetime import date
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
""",
    "backend/app/db/models/medication.py": """from datetime import date
from typing import Optional
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin, TimestampMixin

class Medication(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "medications"
    
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    generic_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    dosage: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    route: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

class MedicationEvent(Base, UUIDMixin):
    __tablename__ = "medication_events"
    
    medication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("medications.id"))
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("health_events.id"))
    action: Mapped[str] = mapped_column(String)
    
    from datetime import datetime, timezone
    from sqlalchemy import DateTime, func
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
""",
    "backend/app/db/models/investigation.py": """from datetime import date
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
""",
    "backend/app/db/models/signal.py": """from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Text, Float, Integer, DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin, TimestampMixin

class Signal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "signals"
    
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    signal_type: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, index=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(SADateTime(timezone=True), nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class SignalEvidence(Base, UUIDMixin):
    __tablename__ = "signal_evidence"
    
    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id"), index=True)
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("health_events.id"), nullable=True)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String)
    
    from sqlalchemy import func
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())
""",
    "backend/app/db/models/search.py": """import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, UUIDMixin

class SearchChunk(Base, UUIDMixin):
    __tablename__ = "search_chunks"
    
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1536), nullable=True)
    
    from datetime import datetime, timezone
    from sqlalchemy import DateTime, func
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
""",
    "backend/app/db/models/audit.py": """from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Text, JSON
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
""",
    "backend/app/schemas/__init__.py": "",
    "backend/app/schemas/auth.py": """from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
""",
    "backend/app/schemas/patient.py": """from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import uuid

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    medical_record_number: str

class PatientResponse(PatientCreate):
    id: uuid.UUID
    created_at: datetime

class PatientSummary(BaseModel):
    id: uuid.UUID
    name: str
    document_count: int
    event_count: int
    open_signals: int
""",
    "backend/app/schemas/document.py": """from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
import uuid

class PageResponse(BaseModel):
    id: uuid.UUID
    page_number: int
    text_content: Optional[str]
    ocr_confidence: Optional[float]

class DocumentResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    original_filename: str
    document_type: str
    document_date: Optional[date]
    processing_status: str
    file_size: int
    created_at: datetime

class DocumentDetail(DocumentResponse):
    pages: List[PageResponse]
""",
    "backend/app/schemas/event.py": """from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
import uuid

class HealthEventResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    event_type: str
    event_date: Optional[date]
    title: str
    description: Optional[str]
    confidence: float
    source_document_id: uuid.UUID
    source_page: Optional[int]
    source_excerpt: Optional[str]
    value: Optional[str]
    unit: Optional[str]
    entity_name: Optional[str]
    status: Optional[str]

class EventRelationshipResponse(BaseModel):
    id: uuid.UUID
    source_event_id: uuid.UUID
    target_event_id: uuid.UUID
    relationship_type: str
    confidence: float

class TimelineEntry(BaseModel):
    date: Optional[date]
    events: List[HealthEventResponse]
""",
    "backend/app/schemas/signal.py": """from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class EvidenceResponse(BaseModel):
    id: uuid.UUID
    signal_id: uuid.UUID
    event_id: Optional[uuid.UUID]
    document_id: Optional[uuid.UUID]
    page_number: Optional[int]
    excerpt: Optional[str]
    role: str
    document_filename: Optional[str] = None
    event_title: Optional[str] = None

class SignalResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    signal_type: str
    title: str
    description: str
    severity: str
    confidence: float
    status: str
    evidence: List[EvidenceResponse]
    created_at: datetime

class SignalReviewRequest(BaseModel):
    decision: str
    comment: Optional[str] = None
""",
    "backend/app/schemas/medication.py": """from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date
import uuid

class MedicationResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    name: str
    generic_name: Optional[str]
    dosage: Optional[str]
    frequency: Optional[str]
    route: Optional[str]
    status: str
    start_date: Optional[date]
    end_date: Optional[date]
    events: List[Any] = []

class MedicationTimelineEntry(BaseModel):
    date: Optional[date]
    action: str
    event_id: uuid.UUID
    document_id: Optional[uuid.UUID]
""",
    "backend/app/schemas/investigation.py": """from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import uuid

class InvestigationResultResponse(BaseModel):
    id: uuid.UUID
    value: Optional[str]
    unit: Optional[str]
    reference_range: Optional[str]
    is_abnormal: Optional[bool]
    test_date: Optional[date]
    event_id: uuid.UUID

class InvestigationResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    name: str
    category: str
    results: List[InvestigationResultResponse]
""",
    "backend/app/schemas/search.py": """from pydantic import BaseModel
from typing import Optional, List, Any
import uuid

class CitationResponse(BaseModel):
    document_id: uuid.UUID
    document_name: str
    page_number: int
    excerpt: str
    confidence: float

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    answer: str
    citations: List[CitationResponse]
    related_events: List[Any]
""",
    "backend/app/schemas/dashboard.py": """from pydantic import BaseModel
from typing import Optional, List, Any

class DashboardResponse(BaseModel):
    total_documents: int
    total_events: int
    open_signals: int
    total_medications: int
    total_investigations: int
    recent_documents: List[Any] = []
    recent_signals: List[Any] = []

class ResearchDashboardResponse(BaseModel):
    documents_processed: int
    events_extracted: int
    signals_generated: int
    signals_verified: int
    signals_dismissed: int
    avg_confidence: float
    signal_distribution: dict
    processing_failures: int

class EvaluationDetail(BaseModel):
    test_case: str
    expected: Any
    predicted: Any
    correct: bool
    evidence: Any
    confidence: float

class EvaluationResult(BaseModel):
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    evidence_accuracy: float
    details: List[EvaluationDetail]
""",
    "backend/app/schemas/common.py": """from pydantic import BaseModel
from typing import Optional, List, Any, Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = {}

class ErrorResponse(BaseModel):
    error: ErrorDetail

class HealthResponse(BaseModel):
    status: str
    database: str
    ai: str
    ocr: str
""",
    "backend/app/repositories/__init__.py": "",
    "backend/app/repositories/user_repository.py": """from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
import uuid

async def get_by_id(db: AsyncSession, user_id: uuid.UUID):
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def get_by_email(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def create(db: AsyncSession, user_data: dict):
    user = User(**user_data)
    db.add(user)
    await db.flush()
    return user

async def list_users(db: AsyncSession):
    stmt = select(User)
    res = await db.execute(stmt)
    return res.scalars().all()
""",
    "backend/app/repositories/patient_repository.py": """from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.patient import Patient, PatientAccess
import uuid

async def get_by_id(db: AsyncSession, patient_id: uuid.UUID):
    stmt = select(Patient).where(Patient.id == patient_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_for_user(db: AsyncSession, user_id: uuid.UUID, role: str):
    if role == "ADMIN":
        stmt = select(Patient)
    else:
        stmt = select(Patient).join(PatientAccess).where(PatientAccess.user_id == user_id)
    res = await db.execute(stmt)
    return res.scalars().all()

async def create(db: AsyncSession, patient_data: dict, user_id: uuid.UUID):
    patient = Patient(**patient_data, created_by=user_id)
    db.add(patient)
    await db.flush()
    access = PatientAccess(patient_id=patient.id, user_id=user_id, access_level="ADMIN", granted_by=user_id)
    db.add(access)
    await db.flush()
    return patient

async def check_access(db: AsyncSession, patient_id: uuid.UUID, user_id: uuid.UUID):
    stmt = select(PatientAccess).where(PatientAccess.patient_id == patient_id, PatientAccess.user_id == user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none() is not None
""",
    "backend/app/repositories/document_repository.py": """from sqlalchemy.ext.asyncio import AsyncSession
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
""",
    "backend/app/repositories/event_repository.py": """from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.event import HealthEvent, EventRelationship
import uuid

async def get_by_id(db: AsyncSession, event_id: uuid.UUID):
    stmt = select(HealthEvent).where(HealthEvent.id == event_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_for_patient(db: AsyncSession, patient_id: uuid.UUID, event_type=None, start_date=None, end_date=None):
    stmt = select(HealthEvent).where(HealthEvent.patient_id == patient_id)
    if event_type:
        stmt = stmt.where(HealthEvent.event_type == event_type)
    if start_date:
        stmt = stmt.where(HealthEvent.event_date >= start_date)
    if end_date:
        stmt = stmt.where(HealthEvent.event_date <= end_date)
    res = await db.execute(stmt)
    return res.scalars().all()

async def create(db: AsyncSession, event_data: dict):
    event = HealthEvent(**event_data)
    db.add(event)
    await db.flush()
    return event

async def create_relationship(db: AsyncSession, rel_data: dict):
    rel = EventRelationship(**rel_data)
    db.add(rel)
    await db.flush()
    return rel

async def get_relationships(db: AsyncSession, event_id: uuid.UUID):
    stmt = select(EventRelationship).where(
        (EventRelationship.source_event_id == event_id) | (EventRelationship.target_event_id == event_id)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_timeline(db: AsyncSession, patient_id: uuid.UUID):
    stmt = select(HealthEvent).where(HealthEvent.patient_id == patient_id).order_by(HealthEvent.event_date.asc())
    res = await db.execute(stmt)
    return res.scalars().all()
""",
    "backend/app/repositories/signal_repository.py": """from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models.signal import Signal, SignalEvidence
import uuid
from datetime import datetime, timezone

async def get_by_id(db: AsyncSession, signal_id: uuid.UUID):
    stmt = select(Signal).where(Signal.id == signal_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_for_patient(db: AsyncSession, patient_id: uuid.UUID, status=None, signal_type=None):
    stmt = select(Signal).where(Signal.patient_id == patient_id)
    if status:
        stmt = stmt.where(Signal.status == status)
    if signal_type:
        stmt = stmt.where(Signal.signal_type == signal_type)
    res = await db.execute(stmt)
    return res.scalars().all()

async def create(db: AsyncSession, signal_data: dict):
    signal = Signal(**signal_data)
    db.add(signal)
    await db.flush()
    return signal

async def create_evidence(db: AsyncSession, evidence_data: dict):
    evidence = SignalEvidence(**evidence_data)
    db.add(evidence)
    await db.flush()
    return evidence

async def review(db: AsyncSession, signal_id: uuid.UUID, user_id: uuid.UUID, decision: str, comment: str):
    stmt = update(Signal).where(Signal.id == signal_id).values(
        status=decision,
        reviewed_by=user_id,
        review_comment=comment,
        reviewed_at=datetime.now(timezone.utc)
    )
    await db.execute(stmt)
    await db.flush()

async def get_evidence(db: AsyncSession, signal_id: uuid.UUID):
    stmt = select(SignalEvidence).where(SignalEvidence.signal_id == signal_id)
    res = await db.execute(stmt)
    return res.scalars().all()
""",
    "backend/app/repositories/medication_repository.py": """from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.medication import Medication, MedicationEvent
import uuid

async def list_for_patient(db: AsyncSession, patient_id: uuid.UUID):
    stmt = select(Medication).where(Medication.patient_id == patient_id)
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_by_name(db: AsyncSession, patient_id: uuid.UUID, name: str):
    stmt = select(Medication).where(Medication.patient_id == patient_id, Medication.name == name)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def create(db: AsyncSession, med_data: dict):
    med = Medication(**med_data)
    db.add(med)
    await db.flush()
    return med

async def create_event(db: AsyncSession, med_event_data: dict):
    evt = MedicationEvent(**med_event_data)
    db.add(evt)
    await db.flush()
    return evt
""",
    "backend/app/repositories/investigation_repository.py": """from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.investigation import Investigation, InvestigationEvent
import uuid

async def list_for_patient(db: AsyncSession, patient_id: uuid.UUID):
    stmt = select(Investigation).where(Investigation.patient_id == patient_id)
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_by_name(db: AsyncSession, patient_id: uuid.UUID, name: str):
    stmt = select(Investigation).where(Investigation.patient_id == patient_id, Investigation.name == name)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def create(db: AsyncSession, inv_data: dict):
    inv = Investigation(**inv_data)
    db.add(inv)
    await db.flush()
    return inv

async def create_event(db: AsyncSession, inv_event_data: dict):
    evt = InvestigationEvent(**inv_event_data)
    db.add(evt)
    await db.flush()
    return evt
""",
    "backend/app/repositories/search_repository.py": """from sqlalchemy.ext.asyncio import AsyncSession
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
""",
    "backend/app/repositories/audit_repository.py": """from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.audit import AuditLog, Feedback
import uuid

async def log(db: AsyncSession, user_id: uuid.UUID, action: str, resource_type: str, resource_id: uuid.UUID, details: dict, ip: str):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip
    )
    db.add(entry)
    await db.flush()
    return entry

async def create_feedback(db: AsyncSession, feedback_data: dict):
    fb = Feedback(**feedback_data)
    db.add(fb)
    await db.flush()
    return fb
""",
    "backend/alembic.ini": """[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://medgraph:medgraph@localhost:5432/medgraph

[post_write_hooks]
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""",
    "backend/alembic/env.py": """import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.db.base import Base
import app.db.models  # imports all models
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""",
    "backend/alembic/script.py.mako": '\"\"\"${message}\n\nRevision ID: ${up_revision}\nRevises: ${down_revision | comma,n}\nCreate Date: ${create_date}\n\n\"\"\"\nfrom typing import Sequence, Union\n\nfrom alembic import op\nimport sqlalchemy as sa\n${imports if imports else ""}\n\n# revision identifiers, used by Alembic.\nrevision: str = ${repr(up_revision)}\ndown_revision: Union[str, None] = ${repr(down_revision)}\nbranch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}\ndepends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}\n\n\ndef upgrade() -> None:\n    ${upgrades if upgrades else "pass"}\n\n\ndef downgrade() -> None:\n    ${downgrades if downgrades else "pass"}\n',
    "backend/alembic/versions/__init__.py": ""
}

for path, content in file_contents.items():
    full_path = os.path.join(root_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Files created successfully.")
