from fastapi import Request, FastAPI
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
