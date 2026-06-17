# domains/auth/router.py — Auth HTTP endpoints (thin router layer)
from fastapi import APIRouter, Body, Header, status

from common.responses import success
from domains.auth.dependencies import AuthServiceDep
from domains.auth.schemas import UserCreate, UserLogin

router = APIRouter()


# --- 1. Register ---
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账号",
)
async def register(user_in: UserCreate, service: AuthServiceDep):
    user_data = await service.register(user_in)
    return success(data=user_data.model_dump(), message="注册成功")


# --- 2. Login ---
@router.post(
    "/login",
    summary="用户登录",
    description="验证账号密码并签发双令牌",
)
async def login(
    user_in: UserLogin,
    service: AuthServiceDep,
    x_app_code: str = Header(..., description="应用代码"),
):
    result = await service.login(user_in, x_app_code)
    return success(data=result.model_dump(), message="登录成功")


# --- 3. Refresh ---
@router.post(
    "/refresh",
    summary="刷新令牌",
    description="使用 Refresh Token 旋转签发新的令牌对",
)
async def refresh_token_endpoint(
    service: AuthServiceDep,
    refresh_token: str = Body(..., embed=True),
):
    result = await service.refresh_from_token(refresh_token)
    return success(data=result.model_dump(), message="令牌刷新成功")
