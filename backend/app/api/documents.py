"""Documents API routes."""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.patient import Patient
from app.db.models.document import Document, DocumentPage
from app.core.security import get_current_user
from app.core.config import settings
from app.utils.file_utils import sanitize_filename, generate_storage_name, validate_file_extension, validate_mime_type

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
    # Verify patient exists
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")

    # Validate file
    filename = file.filename or "unknown"
    if not validate_file_extension(filename):
        raise HTTPException(status_code=400, detail="File type not allowed. Allowed: PDF, PNG, JPG, JPEG")

    content_type = file.content_type or ""
    if not validate_mime_type(content_type):
        raise HTTPException(status_code=400, detail="MIME type not allowed")

    # Check file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum: {settings.MAX_FILE_SIZE // (1024*1024)}MB")

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
            "file_size": d.file_size,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reprocess a document."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.processing_status = "QUEUED"
    await db.flush()

    return {"message": "Document queued for reprocessing"}
