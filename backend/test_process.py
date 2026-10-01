import asyncio
import uuid
import sys
import os
from app.db.session import async_session_factory
from app.services.document_service import process_document
from app.db.models.document import Document
from sqlalchemy import select

async def test_process():
    # Find any uploaded document that is NOT processed
    async with async_session_factory() as db:
        result = await db.execute(select(Document).where(Document.processing_status == "UPLOADED").limit(1))
        doc = result.scalar_one_or_none()
        
        if not doc:
            print("No unprocessed documents found.")
            # Get any document to reprocess
            result = await db.execute(select(Document).limit(1))
            doc = result.scalar_one_or_none()
            if not doc:
                print("No documents found in DB at all.")
                return
            
            doc.processing_status = "UPLOADED"
            await db.commit()
            print(f"Set document {doc.id} to UPLOADED for testing.")
            
        doc_id = str(doc.id)
        
    print(f"Processing document {doc_id}...")
    await process_document(doc_id)
    print("Processing complete!")

if __name__ == "__main__":
    asyncio.run(test_process())
