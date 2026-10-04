import pytest

from app.core.exceptions import FileValidationError
from app.utils.file_utils import (
    sanitize_filename,
    validate_file_content,
    validate_file_extension,
    validate_file_size,
)


def test_size_limits(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_FILE_SIZE", 4)
    validate_file_size(4)
    with pytest.raises(FileValidationError):
        validate_file_size(5)

def test_type_validation_checks_extension_and_signature():
    assert validate_file_extension("scan.PDF")
    assert validate_file_content("scan.pdf", b"%PDF-1.7\n")
    assert not validate_file_content("scan.pdf", b"not a PDF")
    assert not validate_file_content("scan.png", b"%PDF-1.7\n")

def test_path_traversal_is_removed_from_storage_filename():
    assert sanitize_filename("../../patient record.pdf") == "patient_record.pdf"

def test_sanitization_preserves_safe_extension():
    assert sanitize_filename("report 2025.pdf") == "report_2025.pdf"


def test_synthetic_seed_refuses_when_demo_mode_is_disabled(monkeypatch):
    from app.core.config import settings
    from app.seed import seed_db
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    with pytest.raises(SystemExit, match="DEMO_MODE is false"):
        seed_db()
