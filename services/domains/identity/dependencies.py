# domains/identity/dependencies.py — Identity DI wiring
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status

from core.db import DbDep, RedisDep
from domains.identity.service import IdentityService


def get_identity_service(db: DbDep, redis: RedisDep) -> IdentityService:
    return IdentityService(db, redis)


IdentityServiceDep = Annotated[IdentityService, Depends(get_identity_service)]


def resolve_app_code(
    x_app_code: str | None = Header(None, alias="X-App-Code"),
    app_code: str | None = Query(None, description="应用系统标识（可由网关自动注入 X-App-Code 头）"),
) -> str:
    """app_code 解析顺序：X-App-Code 头（网关注入）> ?app_code 查询参数（直调测试）"""
    code = x_app_code or app_code
    if not code:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="app_code 必填，可通过 X-App-Code 请求头或 ?app_code 查询参数传入",
        )
    return code


AppCodeDep = Annotated[str, Depends(resolve_app_code)]
