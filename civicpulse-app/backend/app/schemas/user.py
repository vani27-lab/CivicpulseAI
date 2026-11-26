from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.department import DepartmentOut

Language = Literal["en", "hi"]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: UserRole
    department: Optional[DepartmentOut] = None
    preferred_language: str
    is_active: bool
    created_at: datetime


class RegisterRequest(BaseModel):
    """Public sign-up. Always creates a CITIZEN account."""

    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=72)
    preferred_language: Language = "en"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    """Used by an admin to create officer or admin accounts."""

    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=72)
    role: UserRole
    department_id: Optional[int] = None
    preferred_language: Language = "en"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
