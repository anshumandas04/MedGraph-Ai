import os
import uuid
import shutil
import asyncio
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models.document import Document, DocumentPage
from app.db.models.event import HealthEvent
from app.db.models.search import SearchChunk
from app.db.session import async_session_factory
from app.services.ocr_service import get_ocr_provider
from app.services.extraction_service import extract_events
from app.services.search_service import create_chunks
from app.services.ai.factory import get_ai_provider

logger = get_logger(__name__)

# Upload processing runs as an in-process FastAPI background task. A shared lock
# prevents a document from being deleted while OCR/extraction is writing rows.
_document_locks: dict[str, asyncio.Lock] = {}


def document_processing_lock(document_id: str) -> asyncio.Lock:
    return _document_locks.setdefault(document_id, asyncio.Lock())

async def process_document(document_id: str):
    """Background task to process a document."""
    async with document_processing_lock(document_id):
        await _process_document_locked(document_id)


async def _process_document_locked(document_id: str):
    """Run OCR and extraction while holding the document's processing lock."""
    async with async_session_factory() as db:
        try:
            # Fetch document
            result = await db.execute(select(Document).where(Document.id == uuid.UUID(document_id)))
            doc = result.scalar_one_or_none()
            if not doc:
                logger.error("document.processing.document_missing")
                return
                
            logger.info(
                "document.processing.started",
                ocr_provider=settings.OCR_PROVIDER,
                ai_provider=settings.AI_PROVIDER,
            )
            doc.processing_status = "PROCESSING"
            doc.processing_error = None
            await db.commit()
            
            # Extract text
            ocr = get_ocr_provider()
            ocr_result = await ocr.extract_text(doc.file_path)
            logger.info(
                "document.ocr.completed",
                page_count=len(ocr_result.pages),
                source_characters=len(ocr_result.text),
                pages_with_text=sum(1 for page in ocr_result.pages if page.get("text", "").strip()),
                ocr_provider=settings.OCR_PROVIDER,
            )
            
            # Reprocessing replaces this document's prior derived rows first.
            old_event_result = await db.execute(select(HealthEvent).where(HealthEvent.source_document_id == doc.id))
            old_events = old_event_result.scalars().all()
            old_ids = [event.id for event in old_events]
            if old_ids:
                from app.db.models.event import EventRelationship
                from app.db.models.investigation import InvestigationEvent
                from app.db.models.medication import MedicationEvent
                from app.db.models.signal import SignalEvidence
                await db.execute(delete(EventRelationship).where(
                    (EventRelationship.source_event_id.in_(old_ids)) | (EventRelationship.target_event_id.in_(old_ids))
                ))
                await db.execute(delete(MedicationEvent).where(MedicationEvent.event_id.in_(old_ids)))
                await db.execute(delete(InvestigationEvent).where(InvestigationEvent.event_id.in_(old_ids)))
                await db.execute(delete(SignalEvidence).where(SignalEvidence.event_id.in_(old_ids)))
                await db.execute(delete(HealthEvent).where(HealthEvent.id.in_(old_ids)))
            await db.execute(delete(DocumentPage).where(DocumentPage.document_id == doc.id))
            await db.execute(delete(SearchChunk).where(SearchChunk.document_id == doc.id))

            # Save freshly extracted page text.
            pages_saved = []
            for page_data in ocr_result.pages:
                page = DocumentPage(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    page_number=page_data["page_number"],
                    text_content=page_data["text"],
                    ocr_confidence=page_data.get("confidence", 0.0)
                )
                db.add(page)
                pages_saved.append(page_data)
                
            await db.commit()
            
            # Classify and extract
            ai = get_ai_provider()
            classification = await ai.classify_document(ocr_result.text)
            doc.document_type = classification.document_type
            await db.commit()
            logger.info(
                "document.classification.completed",
                document_type=classification.document_type,
                ai_provider=settings.AI_PROVIDER,
            )
            
            # Extract independently per page to keep each fact tied to its source page.
            extracted_count = 0
            for page_data in pages_saved:
                if page_data.get("text", "").strip():
                    events = await extract_events(
                        db, page_data["text"], doc.document_type, str(doc.patient_id),
                        str(doc.id), ai, page_number=page_data["page_number"],
                    )
                    extracted_count += len(events)
            logger.info(
                "document.extraction.completed",
                page_count=len(pages_saved),
                source_characters=len(ocr_result.text),
                event_count=extracted_count,
                ai_provider=settings.AI_PROVIDER,
            )
            
            # Create search chunks
            await create_chunks(db, str(doc.id), pages_saved)
            
            # TODO: trigger relationship and signal updates...
            from app.services.relationship_service import detect_relationships
            await detect_relationships(db, str(doc.patient_id))
            
            from app.services.signal_service import run_signal_engine
            signals = await run_signal_engine(db, doc.patient_id)

            doc.processing_status = "COMPLETED" if ocr_result.text.strip() else "NEEDS_REVIEW"
            if not ocr_result.text.strip():
                doc.processing_error = "No readable text was found. Review the source file and OCR setup."
            await db.commit()
            logger.info(
                "document.processing.completed",
                page_count=len(pages_saved),
                event_count=extracted_count,
                signal_count=len(signals),
                status=doc.processing_status,
            )
            
        except Exception as e:
            logger.error(
                "document.processing.failed",
                exception_type=type(e).__name__,
                ai_provider=settings.AI_PROVIDER,
                ocr_provider=settings.OCR_PROVIDER,
            )
            # Try to save error status
            try:
                await db.rollback()
                result = await db.execute(select(Document).where(Document.id == uuid.UUID(document_id)))
                doc = result.scalar_one_or_none()
                if doc:
                    doc.processing_status = "FAILED"
                    doc.processing_error = f"Processing failed ({type(e).__name__}). Check server logs and provider configuration."
                    await db.commit()
            except Exception as e2:
                logger.error("document.processing.failure_status_save_failed", exception_type=type(e2).__name__)
