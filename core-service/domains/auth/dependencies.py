# domains/auth/dependencies.py — Auth DI wiring + authentication dependency
import hmac
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import get_app_settings, get_auth_settings
from core.db import DbDep, RedisDep
from core.security import decode_token
from domains.auth.exceptions import (
    TokenVersionMismatchError,
    UserBannedError,
    UserNotFoundError,
    TokenRevokedError,
)
from domains.auth.models import User
from domains.auth.repository import UserRepository
from domains.auth.service import AuthService
from domains.identity.dependencies import get_identity_service
from domains.identity.service import IdentityService

# --- OAuth2 Bearer scheme ---


class OAuth2Bearer(HTTPBearer):
    """Custom Bearer extractor: no auto-raise, defers to domain exceptions."""

    async def __call__(self, request: Request) -> str | None:
        res: HTTPAuthorizationCredentials | None = await super().__call__(request)
        return res.credentials if res else None


oauth2_scheme = OAuth2Bearer(auto_error=False)


# --- Current user dependency ---


async def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: DbDep,
    redis: RedisDep,
) -> User:
    """
    Core auth dependency:
    1. Identify Gateway passthrough or direct JWT token.
    2. Validate token type and validity.
    3. Check AT JTI blacklist (revoked after refresh / logout).
    4. Check session validity (user has at least one valid RT).
    5. Check user active status in DB.
    6. Verify version (supports force-invalidate after password reset).
    """
    auth_settings = get_auth_settings()
    internal_secret = request.headers.get("X-Internal-Secret")
    x_user_id = request.headers.get("X-User-Id")
    x_user_ver = request.headers.get("X-User-Version")
    x_at_jti = request.headers.get("X-User-Jti")

    # A. Trusted internal mode (Gateway passthrough) — timing-safe comparison
    if internal_secret and x_user_id and hmac.compare_digest(internal_secret, auth_settings.INTERNAL_SECRET):
        user_id = int(x_user_id)
        token_ver = int(x_user_ver) if x_user_ver else None
        # Get AT JTI: prefer Gateway header, fallback to decoding the token
        at_jti = x_at_jti
        if not at_jti and token:
            try:
                payload = decode_token(token)
                at_jti = payload.get("jti")
            except Exception:
                pass  # Token may be expired/invalid — session check will catch it
    else:
        # B. Direct external request (JWT validation) — only allowed in non-production
        environment = get_app_settings().ENVIRONMENT
        if environment == "production":
            raise UserNotFoundError("生产环境禁止直连 Services，请通过网关访问")

        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        token_ver = payload.get("ver")
        at_jti = payload.get("jti")

    # C. AT JTI blacklist check — rejects old ATs after refresh
    if at_jti:
        is_blacklisted = await redis.get(f"auth:at:blacklist:{at_jti}")
        if is_blacklisted:
            raise TokenRevokedError("令牌已刷新，请使用新令牌")

    # D. Session validity check — user must have at least one valid RT
    rt_pattern = f"auth:rt:{user_id}:*"
    rt_keys = await redis.keys(rt_pattern)
    has_valid_session = False
    for key in rt_keys:
        status_val = await redis.get(key)
        # RT value format: "valid:<at_jti>" or "used" or legacy "valid"
        if status_val and (status_val.startswith(b"valid") if isinstance(status_val, bytes) else status_val.startswith("valid")):
            has_valid_session = True
            break
    if not has_valid_session:
        raise TokenRevokedError("会话已失效，请重新登录")

    # E. Real-time DB security check
    user = await db.get(User, user_id)

    if not user:
        raise UserNotFoundError("用户不存在")
    if not user.is_active:
        raise UserBannedError("该账号已被封禁")

    if token_ver is not None and user.version != token_ver:
        raise TokenVersionMismatchError("登录凭证已过期，请重新登录")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


# --- Service DI ---


def get_auth_service(db: DbDep, redis: RedisDep, identity_service: Annotated[IdentityService, Depends(get_identity_service)]) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo, redis, identity_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
