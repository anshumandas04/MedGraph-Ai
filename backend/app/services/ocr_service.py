"""Local document text extraction.

Text-based PDFs are read with PyMuPDF. Scanned PDFs and images use the locally
installed Tesseract executable through pytesseract; no document contents leave
the machine. Missing OCR dependencies produce a visible processing error.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    text: str
    confidence: float
    pages: list[dict[str, Any]]


class OCRConfigurationError(RuntimeError):
    """Raised when the requested local OCR provider is not installed/configured."""


class OCRProvider(ABC):
    @abstractmethod
    async def extract_text(self, file_path: str) -> OCRResult:
        raise NotImplementedError


class LocalDocumentOCR(OCRProvider):
    """Extract embedded PDF text first; OCR only pages that need it."""

    def __init__(self) -> None:
        self._pytesseract = None

    def _load_tesseract(self):
        if self._pytesseract is not None:
            return self._pytesseract
        try:
            import pytesseract
        except ImportError as exc:
            raise OCRConfigurationError(
                "Scanned pages require pytesseract and the Tesseract OCR executable. "
                "Install both locally, or use text-based PDFs with an embedded text layer."
            ) from exc
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        try:
            pytesseract.get_tesseract_version()
        except Exception as exc:
            raise OCRConfigurationError(
                "Tesseract executable was not found. Install Tesseract OCR and make it "
                "available on PATH, or set TESSERACT_CMD."
            ) from exc
        self._pytesseract = pytesseract
        return pytesseract

    def _ocr_image(self, image) -> tuple[str, float, list[dict[str, Any]]]:
        pytesseract = self._load_tesseract()
        try:
            from pytesseract import Output
            data = pytesseract.image_to_data(
                image,
                lang=settings.OCR_LANGUAGE,
                output_type=Output.DICT,
                config="--psm 6",
            )
        except Exception as exc:
            raise OCRConfigurationError(f"Tesseract could not process this page: {exc}") from exc

        blocks: list[dict[str, Any]] = []
        words: list[str] = []
        confidences: list[float] = []
        for i, raw_text in enumerate(data.get("text", [])):
            word = str(raw_text).strip()
            if not word:
                continue
            words.append(word)
            try:
                confidence = max(0.0, min(1.0, float(data["conf"][i]) / 100.0))
            except (ValueError, TypeError, KeyError):
                confidence = 0.0
            if confidence:
                confidences.append(confidence)
            blocks.append({
                "block_id": len(blocks),
                "text": word,
                "confidence": confidence,
                "bbox": {
                    "left": data["left"][i], "top": data["top"][i],
                    "width": data["width"][i], "height": data["height"][i],
                },
            })
        return " ".join(words), (sum(confidences) / len(confidences) if confidences else 0.0), blocks

    async def extract_text(self, file_path: str) -> OCRResult:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError("The uploaded document file could not be found.")

        ext = path.suffix.lower()
        if ext == ".pdf":
            return self._extract_pdf(path)
        if ext in {".png", ".jpg", ".jpeg"}:
            return self._extract_image(path)
        raise ValueError("Unsupported document type. Upload PDF, PNG, JPG, or JPEG.")

    def _extract_pdf(self, path: Path) -> OCRResult:
        import fitz
        from PIL import Image

        try:
            document = fitz.open(path)
        except Exception as exc:
            raise ValueError("The uploaded PDF could not be opened.") from exc
        if document.page_count < 1 or document.page_count > settings.OCR_MAX_PAGES:
            document.close()
            raise ValueError(f"PDF page count must be between 1 and {settings.OCR_MAX_PAGES}.")

        pages: list[dict[str, Any]] = []
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            native_text = page.get_text("text").strip()
            if len(native_text) >= settings.OCR_MIN_TEXT_CHARS:
                page_text, confidence, blocks = native_text, 1.0, []
                method = "pdf_text_layer"
            else:
                scale = settings.OCR_RENDER_DPI / 72.0
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                if pix.width * pix.height > 25_000_000:
                    raise ValueError("Rendered page exceeds the safe OCR pixel limit.")
                image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                ocr_text, confidence, blocks = self._ocr_image(image)
                page_text = ocr_text if ocr_text else native_text
                method = "tesseract" if ocr_text else "pdf_text_layer"
            pages.append({
                "page_number": page_index + 1,
                "text": page_text,
                "confidence": confidence,
                "blocks": blocks,
                "extraction_method": method,
            })
        document.close()
        confidences = [p["confidence"] for p in pages if p["text"].strip()]
        return OCRResult(
            text="\n\n".join(p["text"] for p in pages if p["text"].strip()),
            confidence=sum(confidences) / len(confidences) if confidences else 0.0,
            pages=pages,
        )

    def _extract_image(self, path: Path) -> OCRResult:
        from PIL import Image, ImageOps, UnidentifiedImageError
        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                if image.width * image.height > 25_000_000:
                    raise ValueError("Image exceeds the safe OCR pixel limit.")
                text, confidence, blocks = self._ocr_image(image)
        except UnidentifiedImageError as exc:
            raise ValueError("The uploaded image is invalid or unsupported.") from exc
        return OCRResult(
            text=text,
            confidence=confidence,
            pages=[{
                "page_number": 1, "text": text, "confidence": confidence,
                "blocks": blocks, "extraction_method": "tesseract",
            }],
        )


class MockOCRProvider(OCRProvider):
    """Deprecated compatibility name; mock OCR no longer fabricates document text."""
    async def extract_text(self, file_path: str) -> OCRResult:
        raise OCRConfigurationError(
            "Mock OCR was removed because it returned fabricated text. Configure "
            "OCR_PROVIDER=auto to extract real document contents locally."
        )


def get_ocr_provider() -> OCRProvider:
    provider = settings.OCR_PROVIDER.lower()
    if provider in {"auto", "tesseract"}:
        return LocalDocumentOCR()
    if provider == "mock":
        return MockOCRProvider()
    raise OCRConfigurationError(f"Unsupported OCR_PROVIDER: {provider}")
