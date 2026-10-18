import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.core.enums import UserRole


class LoginRequest(BaseModel):
    """User credentials for authentication."""
    email: EmailStr = Field(..., examples=["admin@institution.edu"])
    password: str = Field(..., min_length=6, max_length=128, examples=["SecurePass123!"])


class TokenOut(BaseModel):
    """JWT Token response payload."""
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: uuid.UUID
    email: str
    full_name: str


class BootstrapAdminRequest(BaseModel):
    """Initial system bootstrap request to seed the first Administrator."""
    email: EmailStr = Field(..., examples=["admin@institution.edu"])
    password: str = Field(..., min_length=8, max_length=128, examples=["AdminStrongPass2026!"])
    full_name: str = Field(..., min_length=2, max_length=150, examples=["System Administrator"])


class UserCreate(BaseModel):
    """Payload for creating a new user (admin-controlled)."""
    email: EmailStr = Field(..., examples=["faculty.john@institution.edu"])
    password: str = Field(..., min_length=8, max_length=128, examples=["FacultyPass2026!"])
    full_name: str = Field(..., min_length=2, max_length=150, examples=["Dr. John Doe"])
    role: UserRole


class UserOut(BaseModel):
    """Public user profile representation."""
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
