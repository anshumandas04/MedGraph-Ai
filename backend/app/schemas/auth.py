from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    # Public registration always creates a least-privileged patient account.
    # The API also ignores any client-supplied role value.
    role: str = "PATIENT"

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
