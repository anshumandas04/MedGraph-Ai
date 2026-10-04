"""Patient API routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.patient import Patient, PatientAccess
from app.db.models.document import Document
from app.db.models.event import HealthEvent
from app.db.models.signal import Signal
from app.db.models.medication import Medication
from app.db.models.investigation import Investigation
from app.core.security import get_current_user, require_role
from app.core.access import assert_patient_access
from app.schemas.patient import (
    PatientCreate,
    PatientResponse,
    PatientSelfProfileCreate,
    PatientSummary,
)

router = APIRouter()


@router.get("/patients", response_model=list[PatientResponse])
async def list_patients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List patients accessible to the current user."""
    if current_user.role == "ADMIN":
        result = await db.execute(select(Patient).order_by(Patient.last_name))
    else:
        access_filters = [PatientAccess.user_id == current_user.id]
        if current_user.role == "PATIENT":
            access_filters.append(PatientAccess.access_level == "OWNER")
        result = await db.execute(
            select(Patient)
            .join(PatientAccess, PatientAccess.patient_id == Patient.id)
            .where(*access_filters)
            .order_by(Patient.last_name)
        )
    return result.scalars().all()


@router.post("/patients/me/profile", response_model=PatientResponse, status_code=201)
async def create_my_patient_profile(
    data: PatientSelfProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PATIENT"])),
):
    """Create and link the authenticated patient's own record."""
    existing = await db.execute(
        select(Patient.id)
        .join(PatientAccess, PatientAccess.patient_id == Patient.id)
        .where(
            PatientAccess.user_id == current_user.id,
            PatientAccess.access_level == "OWNER",
        )
        .limit(1)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A patient profile is already linked to this account")

    patient = Patient(
        id=uuid.uuid4(),
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        medical_record_number=f"MG-{uuid.uuid4().hex[:12].upper()}",
        created_by=current_user.id,
    )
    db.add(patient)
    db.add(PatientAccess(
        id=uuid.uuid4(),
        patient_id=patient.id,
        user_id=current_user.id,
        access_level="OWNER",
        granted_by=current_user.id,
    ))
    await db.flush()
    return patient


@router.post("/patients", response_model=PatientResponse, status_code=201)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "CLINICIAN"])),
):
    """Create a new patient."""
    patient = Patient(
        id=uuid.uuid4(),
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        medical_record_number=data.medical_record_number,
        created_by=current_user.id,
    )
    db.add(patient)
    # Grant creator access
    db.add(PatientAccess(
        id=uuid.uuid4(),
        patient_id=patient.id,
        user_id=current_user.id,
        access_level="ADMIN",
        granted_by=current_user.id,
    ))
    await db.flush()
    return patient


@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get patient details."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    await assert_patient_access(patient_id, db, current_user)
    return patient


@router.get("/patients/{patient_id}/summary", response_model=PatientSummary)
async def get_patient_summary(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get patient summary with counts."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    await assert_patient_access(patient_id, db, current_user)

    doc_count = (await db.execute(
        select(func.count(Document.id)).where(Document.patient_id == patient_id)
    )).scalar() or 0

    event_count = (await db.execute(
        select(func.count(HealthEvent.id)).where(HealthEvent.patient_id == patient_id)
    )).scalar() or 0

    open_signals = (await db.execute(
        select(func.count(Signal.id)).where(
            Signal.patient_id == patient_id,
            Signal.status == "OPEN",
        )
    )).scalar() or 0

    medication_count = (await db.execute(
        select(func.count(Medication.id)).where(Medication.patient_id == patient_id)
    )).scalar() or 0

    investigation_count = (await db.execute(
        select(func.count(Investigation.id)).where(Investigation.patient_id == patient_id)
    )).scalar() or 0

    return PatientSummary(
        id=patient.id,
        name=f"{patient.first_name} {patient.last_name}",
        document_count=doc_count,
        event_count=event_count,
        open_signals=open_signals,
        medication_count=medication_count,
        investigation_count=investigation_count,
    )
