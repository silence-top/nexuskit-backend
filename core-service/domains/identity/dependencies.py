# domains/identity/dependencies.py — Identity DI wiring
import hashlib
import hmac
import time
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import DbDep, RedisDep
from domains.auth.repository import UserRepository
from domains.identity.models import App
from domains.identity.service import IdentityService

# 签名时间窗口（5 分钟，同微信开放平台一致）
_SIGN_WINDOW_SECONDS = 300


def get_identity_service(db: DbDep, redis: RedisDep) -> IdentityService:
    return IdentityService(db, redis, UserRepository(db))


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


async def verify_app_secret(
    db: DbDep,
    redis: RedisDep,
    x_app_code: str = Header(..., alias="X-App-Code", description="应用编码"),
    x_timestamp: str = Header(..., alias="X-Timestamp", description="Unix 秒级时间戳"),
    x_nonce: str = Header(..., alias="X-Nonce", description="随机字符串，长度建议 16-32 位"),
    x_signature: str = Header(..., alias="X-Signature", description="HMAC-SHA256 签名"),
) -> App:
    """服务间调用鉴权依赖（仿微信开放平台签名验证）。

    客户端签名算法：
        string_to_sign = f"{app_code}\\n{timestamp}\\n{nonce}"
        signature = hmac.sha256(string_to_sign, app_secret).hexdigest()

    防护机制：
        1. 时间窗口校验：时间戳必须在 ±{_SIGN_WINDOW_SECONDS}s 窗口内
        2. Nonce 防重放：同一 nonce 在时间窗口内只能使用一次（Redis 记录）
        3. 签名校验：恒定时比较防时序攻击
        4. App 必须已在 Nexuskit 注册且具备有效 app_secret
    """
    # ① 时间窗口校验
    try:
        ts = int(x_timestamp)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="无效的时间戳")
    if abs(time.time() - ts) > _SIGN_WINDOW_SECONDS:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="请求已过期，请同步服务器时钟")

    # ② Nonce 防重放（Redis key: internal:nonce:{app_code}:{nonce})
    nonce_key = f"internal:nonce:{x_app_code}:{x_nonce}"
    if await redis.exists(nonce_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Nonce 已使用，疑似重放攻击")

    # ③ 查询 App 及其 app_secret
    result = await db.execute(select(App).where(App.app_code == x_app_code))
    app: App | None = result.scalar_one_or_none()
    if not app or not app.app_secret:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="应用不存在或未配置密钥")

    # ④ HMAC-SHA256 签名校验
    string_to_sign = f"{x_app_code}\n{x_timestamp}\n{x_nonce}"
    expected_sig = hmac.new(
        app.app_secret.encode(),
        string_to_sign.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_sig, x_signature.lower()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="签名验证失败")

    # ⑤ 签名通过后打标 nonce 已用（TTL = 时间窗口）
    await redis.setex(nonce_key, _SIGN_WINDOW_SECONDS, "1")

    return app


AppSecretDep = Annotated[App, Depends(verify_app_secret)]
