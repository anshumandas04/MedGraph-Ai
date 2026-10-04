from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
import logging
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
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                },
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logging.getLogger("medgraph.errors").error(
            "Unhandled request exception",
            extra={"exception_type": type(exc).__name__},
        )
        headers = {"X-Request-ID": request_id} if request_id else None
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "The server could not complete this request.",
                    "details": {},
                },
                "request_id": request_id,
            },
            headers=headers,
        )
