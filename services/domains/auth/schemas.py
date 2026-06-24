# domains/auth/schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """[本人] 修改自己的基本信息。"""
    email: EmailStr | None = None
    phone: str | None      = None
    dept_id: int | None    = None

class PasswordChange(BaseModel):
    """[本人] 修改自己密码，需验证旧密码。"""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


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


class UserListItem(BaseModel):
    """[管理员] 用户列表条目。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    phone: str | None
    is_active: bool
    is_mfa_enabled: bool
    dept_id: int | None


class TokenPair(BaseModel):
    """Access + Refresh token pair."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class LoginResponse(TokenPair):
    """Login endpoint response: token pair + user info."""

    user: UserRead
