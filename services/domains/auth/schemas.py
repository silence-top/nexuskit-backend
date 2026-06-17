# domains/auth/schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class RoleBrief(BaseModel):
    """Minimal role info returned by IdentityService."""
    id: int
    role_name: str
    role_code: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool
    phone: str | None = None
    phone_code: str = "86"
    is_mfa_enabled: bool = False
    dept_id: int | None = None


class TokenPair(BaseModel):
    """Access + Refresh token pair."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class LoginResponse(TokenPair):
    """Login endpoint response: token pair + user info."""

    user: UserRead
