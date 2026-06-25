# domains/auth/router.py — Auth HTTP endpoints (thin router layer)
from fastapi import APIRouter, Body, Header, status

from common.responses import success
from domains.auth.dependencies import AuthServiceDep, CurrentUserDep
from domains.auth.schemas import PasswordChange, UserCreate, UserLogin, UserUpdate

router = APIRouter()


# ─────────────────────────────────────────────────────────
# 认证（公开接口）
# ─────────────────────────────────────────────────────────
@router.post("/register", status_code=status.HTTP_201_CREATED, summary="用户注册")
async def register(user_in: UserCreate, service: AuthServiceDep):
    user_data = await service.register(user_in)
    return success(data=user_data.model_dump(), message="注册成功")


@router.post("/login", summary="用户登录")
async def login(
    user_in: UserLogin,
    service: AuthServiceDep,
    x_app_code: str = Header(..., description="应用代码"),
):
    result = await service.login(user_in, x_app_code)
    return success(data=result.model_dump(), message="登录成功")


@router.post("/refresh", summary="刷新令牌")
async def refresh_token_endpoint(
    service: AuthServiceDep,
    refresh_token: str = Body(..., embed=True),
):
    result = await service.refresh_from_token(refresh_token)
    return success(data=result.model_dump(), message="令牌刷新成功")


@router.post("/logout", summary="登出")
async def logout(service: AuthServiceDep, current_user: CurrentUserDep):
    await service.force_logout(current_user.id)
    return success(message="已登出")


# ─────────────────────────────────────────────────────────
# 个人中心（登录用户自己的操作）
# ─────────────────────────────────────────────────────────
@router.get("/me", summary="获取个人信息")
async def get_me(current_user: CurrentUserDep):
    from domains.auth.schemas import UserRead
    return success(data=UserRead.model_validate(current_user).model_dump())


@router.put("/me", summary="更新个人信息")
async def update_me(data: UserUpdate, service: AuthServiceDep, current_user: CurrentUserDep):
    user = await service.update_user(current_user.id, data.email, data.phone, data.dept_id)
    return success(data=user.model_dump(), message="更新成功")


@router.put("/me/password", summary="修改密码")
async def change_my_password(data: PasswordChange, service: AuthServiceDep, current_user: CurrentUserDep):
    await service.change_password(current_user.id, data)
    return success(message="密码修改成功，请重新登录")
