import os
import uuid
import shutil
import logging
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError, FileValidationError
from app.db.models.document import Document, DocumentPage
from app.db.session import async_session_factory
from app.services.ocr_service import get_ocr_provider
from app.services.extraction_service import extract_events
from app.services.search_service import create_chunks
from app.services.ai.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

async def process_document(document_id: str):
    """Background task to process a document."""
    async with async_session_factory() as db:
        try:
            # Fetch document
            result = await db.execute(select(Document).where(Document.id == uuid.UUID(document_id)))
            doc = result.scalar_one_or_none()
            if not doc:
                logger.error(f"Document {document_id} not found for processing.")
                return
                
            logger.info(f"Starting processing for document {document_id}")
            doc.processing_status = "PROCESSING"
            await db.commit()
            
            # Extract text
            ocr = get_ocr_provider()
            ocr_result = await ocr.extract_text(doc.file_path)
            
            # Save pages
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
            ai = OpenAIProvider()
            classification = await ai.classify_document(ocr_result.text)
            doc.document_type = classification.document_type
            await db.commit()
            
            # Extract events
            await extract_events(db, ocr_result.text, doc.document_type, str(doc.patient_id), str(doc.id), ai)
            
            # Create search chunks
            await create_chunks(db, str(doc.id), pages_saved)
            
            # TODO: trigger relationship and signal updates...
            from app.services.relationship_service import detect_relationships
            await detect_relationships(db, str(doc.patient_id))
            
            from app.services.signal_service import run_signal_engine
            await run_signal_engine(db, doc.patient_id)

            doc.processing_status = "COMPLETED"
            await db.commit()
            logger.info(f"Finished processing document {document_id}")
            
        except Exception as e:
            logger.exception(f"Failed to process document {document_id}")
            # Try to save error status
            try:
                result = await db.execute(select(Document).where(Document.id == uuid.UUID(document_id)))
                doc = result.scalar_one_or_none()
                if doc:
                    doc.processing_status = "FAILED"
                    doc.processing_error = str(e)
                    await db.commit()
            except Exception as e2:
                logger.error(f"Failed to save error status: {e2}")
