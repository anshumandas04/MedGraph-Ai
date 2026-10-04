"""Structured application logs and a bounded, redacted diagnostics buffer."""
from __future__ import annotations

import json
import logging
import re
import threading
import time
import uuid
from collections import deque
from typing import Any

import structlog
from fastapi import Request


_MAX_LOG_RECORDS = 2_000
_records: deque[dict[str, Any]] = deque(maxlen=_MAX_LOG_RECORDS)
_records_lock = threading.Lock()
_SECRET_PATTERNS = [
    (re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(api[_-]?key|password|secret|token)(\s*[=:]\s*)[^\s,;]+"), r"\1\2[REDACTED]"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[REDACTED_EMAIL]"),
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"), "[ID]"),
]


def _safe_message(message: str) -> str:
    value = message[:4_000]
    for pattern, replacement in _SECRET_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


class DiagnosticsBufferHandler(logging.Handler):
    """Keep recent logs in process memory for the admin diagnostics endpoint."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
            safe_message = _safe_message(message)
            # structlog's JSON records carry useful context. Restrict fields so
            # arbitrary extras (which may contain patient content) are omitted.
            parsed: dict[str, Any] = {}
            try:
                decoded = json.loads(message)
                if isinstance(decoded, dict):
                    parsed = decoded
            except (json.JSONDecodeError, TypeError):
                pass
            item = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
                "level": record.levelname,
                "logger": record.name[:160],
            }
            if parsed:
                # Only expose diagnostic fields with operational value. Never
                # return arbitrary structlog extras (which may contain patient content).
                for key in (
                    "event", "method", "path", "status_code", "duration_ms",
                    "exception_type", "stage", "page_number", "page_count",
                    "source_characters", "candidate_count", "event_count",
                    "event_types", "document_type", "ocr_provider", "ai_provider",
                    "search_chunk_count", "relationship_count", "signal_count", "http_status",
                    "status", "pages_with_text",
                ):
                    value = parsed.get(key)
                    if isinstance(value, (str, int, float, dict)):
                        item[key] = _safe_message(json.dumps(value) if isinstance(value, dict) else str(value))
                item["message"] = str(item.get("event", "Application log"))
            else:
                item["message"] = safe_message
            request_id = parsed.get("request_id")
            if isinstance(request_id, str) and len(request_id) <= 64:
                item["request_id"] = request_id
            record_exception_type = record.__dict__.get("exception_type")
            if isinstance(record_exception_type, str):
                item["exception_type"] = record_exception_type[:160]
            if record.exc_info and record.exc_info[1]:
                item["exception_type"] = type(record.exc_info[1]).__name__
            with _records_lock:
                _records.append(item)
        except Exception:
            self.handleError(record)


class SafeConsoleFormatter(logging.Formatter):
    """Print sanitized messages without raw exception tracebacks or payloads."""

    def format(self, record: logging.LogRecord) -> str:
        return _safe_message(record.getMessage())


def recent_logs(*, limit: int = 100, level: str | None = None) -> list[dict[str, Any]]:
    with _records_lock:
        rows = list(_records)
    if level and level != "ALL":
        rows = [row for row in rows if row["level"] == level]
    return rows[-limit:][::-1]


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Uvicorn may have configured handlers before the app module loads.
    for handler in list(root.handlers):
        if not isinstance(handler, DiagnosticsBufferHandler) and not getattr(handler, "_medgraph_safe_console", False):
            root.removeHandler(handler)
    if not any(isinstance(handler, DiagnosticsBufferHandler) for handler in root.handlers):
        root.addHandler(DiagnosticsBufferHandler())
    if not any(getattr(handler, "_medgraph_safe_console", False) for handler in root.handlers):
        console = logging.StreamHandler()
        console.setFormatter(SafeConsoleFormatter())
        console._medgraph_safe_console = True  # type: ignore[attr-defined]
        root.addHandler(console)


def get_logger(name: str):
    return structlog.get_logger(name)


async def request_logging_middleware(request: Request, call_next):
    """Attach request IDs and emit privacy-conscious HTTP access diagnostics."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    structlog.contextvars.bind_contextvars(request_id=request_id)
    started = time.perf_counter()
    status_code = 500
    path = request.url.path
    # IDs in URL segments can identify patients/documents. Log route shape only.
    path = re.sub(r"/[0-9a-fA-F-]{32,36}(?=/|$)", "/{id}", path)
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = round((time.perf_counter() - started) * 1_000, 2)
        logging.getLogger("medgraph.http").info(json.dumps({
            "event": "request.completed",
            "request_id": request_id,
            "method": request.method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }))
        # Context vars are task-local; clear them to avoid reusing IDs on the
        # server's async worker task after this request completes.
        structlog.contextvars.clear_contextvars()
