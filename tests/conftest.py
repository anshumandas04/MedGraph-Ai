import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

@pytest.fixture
def mock_db():
    return {"users": [], "events": []}

@pytest.fixture
def test_client():
    return None

@pytest.fixture
def auth_tokens():
    return {"admin": "token1", "clinician": "token2"}
