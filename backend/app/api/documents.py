"""Documents API routes."""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.patient import Patient
from app.db.models.document import Document, DocumentPage
from app.db.models.event import EventAttribute, EventRelationship, HealthEvent
from app.db.models.investigation import Investigation, InvestigationEvent
from app.db.models.medication import Medication, MedicationEvent
from app.db.models.search import SearchChunk
from app.db.models.signal import Signal, SignalEvidence
from app.db.models.audit import DocumentProcessingJob, Feedback
from app.core.security import get_current_user
from app.core.access import assert_patient_access
from app.core.config import settings
from app.utils.file_utils import sanitize_filename, generate_storage_name, validate_file_extension, validate_mime_type, validate_file_content

router = APIRouter()


@router.post("/patients/{patient_id}/documents")
async def upload_document(
    patient_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document for a patient."""
    await assert_patient_access(patient_id, db, current_user, write=True)

    # Validate file
    filename = file.filename or "unknown"
    if not validate_file_extension(filename):
        raise HTTPException(status_code=400, detail="File type not allowed. Allowed: PDF, PNG, JPG, JPEG")

    content_type = file.content_type or ""
    if not validate_mime_type(content_type):
        raise HTTPException(status_code=400, detail="MIME type not allowed")

    # Check file size
    content = await file.read(settings.MAX_FILE_SIZE + 1)
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum: {settings.MAX_FILE_SIZE // (1024*1024)}MB")
    if not validate_file_content(filename, content):
        raise HTTPException(status_code=400, detail="File contents do not match the declared file type.")

    # Save file
    safe_name = sanitize_filename(filename)
    storage_name = generate_storage_name(os.path.splitext(safe_name)[1])
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(patient_id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, storage_name)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = Document(
        id=uuid.uuid4(),
        patient_id=patient_id,
        filename=storage_name,
        original_filename=safe_name,
        file_path=file_path,
        file_size=len(content),
        mime_type=content_type,
        document_type="OTHER",
        processing_status="UPLOADED",
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    from app.services.document_service import process_document
    background_tasks.add_task(process_document, str(doc.id))

    return {
        "id": str(doc.id),
        "patient_id": str(doc.patient_id),
        "original_filename": doc.original_filename,
        "document_type": doc.document_type,
        "processing_status": doc.processing_status,
        "file_size": doc.file_size,
        "message": "Document uploaded successfully",
    }


@router.get("/patients/{patient_id}/documents")
async def list_documents(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents for a patient."""
    await assert_patient_access(patient_id, db, current_user)
    result = await db.execute(
        select(Document)
        .where(Document.patient_id == patient_id)
        .order_by(Document.document_date.desc())
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "patient_id": str(d.patient_id),
            "original_filename": d.original_filename,
            "document_type": d.document_type,
            "document_date": str(d.document_date) if d.document_date else None,
            "processing_status": d.processing_status,
            "processing_error": d.processing_error,
            "file_size": d.file_size,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently remove a source file and all records derived from it."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await assert_patient_access(doc.patient_id, db, current_user, write=True)

    # Release the read transaction before waiting for OCR to finish. The worker
    # and this endpoint share the same per-document lock in this local service.
    patient_id = doc.patient_id
    actor_id = current_user.id
    await db.rollback()
    from app.services.document_service import document_processing_lock
    async with document_processing_lock(str(document_id)):
        actor_result = await db.execute(select(User).where(User.id == actor_id))
        current_user = actor_result.scalar_one_or_none()
        if not current_user:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        await assert_patient_access(doc.patient_id, db, current_user, write=True)

        upload_root = os.path.realpath(settings.UPLOAD_DIR)
        patient_upload_dir = os.path.realpath(os.path.join(upload_root, str(patient_id)))
        file_path = os.path.realpath(doc.file_path)
        try:
            safe_to_remove = os.path.commonpath([patient_upload_dir, file_path]) == patient_upload_dir
        except ValueError:
            safe_to_remove = False
        if not safe_to_remove or file_path == patient_upload_dir:
            raise HTTPException(status_code=500, detail="Stored document path is outside its patient upload folder")

        event_result = await db.execute(
            select(HealthEvent.id).where(HealthEvent.source_document_id == document_id)
        )
        event_ids = [row[0] for row in event_result.all()]
        signal_result = await db.execute(
            select(SignalEvidence.signal_id).where(
                or_(
                    SignalEvidence.document_id == document_id,
                    SignalEvidence.event_id.in_(event_ids) if event_ids else False,
                )
            ).distinct()
        )
        affected_signal_ids = [row[0] for row in signal_result.all()]
        medication_result = await db.execute(
            select(MedicationEvent.medication_id).where(MedicationEvent.event_id.in_(event_ids)).distinct()
        ) if event_ids else None
        investigation_result = await db.execute(
            select(InvestigationEvent.investigation_id).where(InvestigationEvent.event_id.in_(event_ids)).distinct()
        ) if event_ids else None
        medication_ids = [row[0] for row in medication_result.all()] if medication_result else []
        investigation_ids = [row[0] for row in investigation_result.all()] if investigation_result else []

        # Rename first so the original upload is no longer addressable while the
        # database transaction commits. Restore it if database cleanup fails.
        staged_path = None
        if os.path.exists(file_path):
            staged_path = f"{file_path}.deleting-{uuid.uuid4().hex}"
            try:
                os.replace(file_path, staged_path)
            except OSError as exc:
                raise HTTPException(status_code=500, detail="Could not stage the uploaded file for removal") from exc

        try:
            if event_ids:
                await db.execute(delete(EventRelationship).where(
                    or_(EventRelationship.source_event_id.in_(event_ids), EventRelationship.target_event_id.in_(event_ids))
                ))
                await db.execute(delete(EventAttribute).where(EventAttribute.event_id.in_(event_ids)))
                await db.execute(delete(MedicationEvent).where(MedicationEvent.event_id.in_(event_ids)))
                await db.execute(delete(InvestigationEvent).where(InvestigationEvent.event_id.in_(event_ids)))
                await db.execute(delete(Feedback).where(Feedback.event_id.in_(event_ids)))
            await db.execute(delete(SignalEvidence).where(
                or_(
                    SignalEvidence.document_id == document_id,
                    SignalEvidence.event_id.in_(event_ids) if event_ids else False,
                )
            ))
            if affected_signal_ids:
                await db.execute(delete(Feedback).where(Feedback.signal_id.in_(affected_signal_ids)))
                await db.execute(delete(Signal).where(Signal.id.in_(affected_signal_ids)))
            if event_ids:
                await db.execute(delete(HealthEvent).where(HealthEvent.id.in_(event_ids)))
            await db.execute(delete(DocumentPage).where(DocumentPage.document_id == document_id))
            await db.execute(delete(SearchChunk).where(SearchChunk.document_id == document_id))
            await db.execute(delete(DocumentProcessingJob).where(DocumentProcessingJob.document_id == document_id))

            # Keep patient-level projections supported by other documents; remove
            # only projections that have no remaining source events.
            for medication_id in medication_ids:
                remaining = await db.execute(select(MedicationEvent.id).where(
                    MedicationEvent.medication_id == medication_id
                ).limit(1))
                if remaining.first() is None:
                    await db.execute(delete(Medication).where(Medication.id == medication_id))
            for investigation_id in investigation_ids:
                remaining = await db.execute(select(InvestigationEvent.id).where(
                    InvestigationEvent.investigation_id == investigation_id
                ).limit(1))
                if remaining.first() is None:
                    await db.execute(delete(Investigation).where(Investigation.id == investigation_id))

            await db.delete(doc)
            from app.services.signal_service import run_signal_engine
            await run_signal_engine(db, patient_id)
            await db.commit()
        except Exception:
            await db.rollback()
            if staged_path and os.path.exists(staged_path):
                os.replace(staged_path, file_path)
            raise

        if staged_path:
            try:
                os.remove(staged_path)
            except OSError as exc:
                # The database rows are gone; make an unexpected disk cleanup
                # failure explicit so an operator can remove the staged file.
                raise HTTPException(
                    status_code=500,
                    detail="Document data was removed, but a staged file remains and needs filesystem cleanup",
                ) from exc
        try:
            os.rmdir(patient_upload_dir)
        except OSError:
            pass  # Other documents may still be stored in this folder.

    return {"message": "Document and derived data removed", "removed_event_count": len(event_ids)}


@router.get("/documents/{document_id}")
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document detail with pages."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await assert_patient_access(doc.patient_id, db, current_user)

    # Get pages
    pages_result = await db.execute(
        select(DocumentPage)
        .where(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number)
    )
    pages = [
        {
            "id": str(p.id),
            "page_number": p.page_number,
            "text_content": p.text_content,
            "ocr_confidence": p.ocr_confidence,
        }
        for p in pages_result.scalars().all()
    ]

    return {
        "id": str(doc.id),
        "patient_id": str(doc.patient_id),
        "original_filename": doc.original_filename,
        "document_type": doc.document_type,
        "document_date": str(doc.document_date) if doc.document_date else None,
        "processing_status": doc.processing_status,
        "processing_error": doc.processing_error,
        "file_size": doc.file_size,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "pages": pages,
    }


@router.get("/documents/{document_id}/file")
async def serve_document_file(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download/serve the document file."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await assert_patient_access(doc.patient_id, db, current_user)

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=doc.file_path,
        filename=doc.original_filename,
        media_type=doc.mime_type,
    )


@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reprocess a document."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await assert_patient_access(doc.patient_id, db, current_user, write=True)

    doc.processing_status = "QUEUED"
    doc.processing_error = None
    await db.flush()
    await db.commit()
    from app.services.document_service import process_document
    background_tasks.add_task(process_document, str(doc.id))

    return {"message": "Document queued for reprocessing", "processing_status": "QUEUED"}
