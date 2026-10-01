import pytest

@pytest.fixture
def mock_db():
    return {"users": [], "events": []}

@pytest.fixture
def test_client():
    return None

@pytest.fixture
def auth_tokens():
    return {"admin": "token1", "clinician": "token2"}
