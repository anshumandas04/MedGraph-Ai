import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    text: str
    confidence: float
    pages: List[Dict[str, Any]]  # [{page_number, text, confidence, blocks: []}]

class OCRProvider(ABC):
    @abstractmethod
    async def extract_text(self, file_path: str) -> OCRResult:
        pass

class MockOCRProvider(OCRProvider):
    """Returns pre-configured text for testing/demo fallback."""
    async def extract_text(self, file_path: str) -> OCRResult:
        logger.info(f"MockOCR: Processing {file_path}")
        text = "Mock OCR text containing consultation and medication information. Patient prescribed Amoxicillin 500mg on 2023-10-15."
        return OCRResult(
            text=text,
            confidence=0.9,
            pages=[{"page_number": 1, "text": text, "confidence": 0.9, "blocks": []}]
        )

class PaddleOCRProvider(OCRProvider):
    """Uses PaddleOCR to extract text and bounding boxes from documents."""
    def __init__(self):
        # We initialize paddleocr lazily to save startup time
        self._ocr = None
    
    def _get_ocr(self):
        if self._ocr is None:
            logger.info("Initializing PaddleOCR...")
            from paddleocr import PaddleOCR
            # Using angle classifier and english language
            self._ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        return self._ocr

    async def extract_text(self, file_path: str) -> OCRResult:
        import fitz  # PyMuPDF
        import numpy as np
        from PIL import Image
        import io

        logger.info(f"PaddleOCR processing: {file_path}")
        ocr = self._get_ocr()
        
        ext = os.path.splitext(file_path)[1].lower()
        pages_data = []
        full_text = []
        overall_confidence = 0.0
        total_blocks = 0
        
        try:
            if ext == '.pdf':
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    # Get image of page (resolution 300 DPI for good OCR)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img_array = np.array(img)
                    
                    # Run OCR
                    result = ocr.ocr(img_array, cls=True)
                    
                    page_text = []
                    page_blocks = []
                    page_conf = 0.0
                    
                    if result and result[0]:
                        for idx, line in enumerate(result[0]):
                            bbox, (text, conf) = line
                            page_text.append(text)
                            page_blocks.append({
                                "block_id": idx,
                                "text": text,
                                "confidence": float(conf),
                                "bbox": bbox
                            })
                            page_conf += float(conf)
                            
                        if len(result[0]) > 0:
                            page_conf /= len(result[0])
                            
                    full_page_text = "\n".join(page_text)
                    pages_data.append({
                        "page_number": page_num + 1,
                        "text": full_page_text,
                        "confidence": page_conf,
                        "blocks": page_blocks
                    })
                    
                    full_text.append(full_page_text)
                    overall_confidence += page_conf
                    total_blocks += 1
                doc.close()
            else:
                # Direct image
                result = ocr.ocr(file_path, cls=True)
                page_text = []
                page_blocks = []
                page_conf = 0.0
                
                if result and result[0]:
                    for idx, line in enumerate(result[0]):
                        bbox, (text, conf) = line
                        page_text.append(text)
                        page_blocks.append({
                            "block_id": idx,
                            "text": text,
                            "confidence": float(conf),
                            "bbox": bbox
                        })
                        page_conf += float(conf)
                        
                    if len(result[0]) > 0:
                        page_conf /= len(result[0])
                        
                full_page_text = "\n".join(page_text)
                pages_data.append({
                    "page_number": 1,
                    "text": full_page_text,
                    "confidence": page_conf,
                    "blocks": page_blocks
                })
                
                full_text.append(full_page_text)
                overall_confidence += page_conf
                total_blocks += 1
                
        except Exception as e:
            logger.error(f"OCR Error: {e}")
            raise

        avg_conf = overall_confidence / max(total_blocks, 1)
        return OCRResult(
            text="\n\n".join(full_text),
            confidence=avg_conf,
            pages=pages_data
        )

def get_ocr_provider() -> OCRProvider:
    provider = getattr(settings, 'OCR_PROVIDER', 'paddle').lower()
    if provider == 'paddle':
        try:
            return PaddleOCRProvider()
        except ImportError:
            logger.warning("PaddleOCR not installed, falling back to MockOCRProvider")
            return MockOCRProvider()
    return MockOCRProvider()
