import os
import re
import uuid
from app.core.config import settings
from app.core.exceptions import FileValidationError

def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return filename

def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()

def generate_storage_name(extension: str) -> str:
    return f"{uuid.uuid4()}{extension}"

def validate_file_extension(filename: str):
    allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg']
    ext = get_file_extension(filename)
    if ext not in allowed_extensions:
        raise FileValidationError(f"File extension {ext} not allowed.")

def validate_mime_type(content_type: str):
    allowed_mimes = ['application/pdf', 'image/png', 'image/jpeg']
    if content_type not in allowed_mimes:
        raise FileValidationError(f"MIME type {content_type} not allowed.")

def validate_file_size(size: int):
    if size > getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024):
        raise FileValidationError("File too large.")
