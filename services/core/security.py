# core/security.py — Pure security utility functions (no DI, no HTTP knowledge)
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from core.config import get_auth_settings
from domains.auth.exceptions import TokenInvalidError, TokenMissingError, TokenMisuseError

# --- JWT config — lazy-read via lru_cache getter (no module-level instantiation) ---


def _secret() -> str:
    return get_auth_settings().SECRET_KEY


def _refresh_secret() -> str:
    return get_auth_settings().REFRESH_SECRET_KEY


def _algorithm() -> str:
    return get_auth_settings().ALGORITHM


def _expire_minutes() -> int:
    return get_auth_settings().ACCESS_TOKEN_EXPIRE_MINUTES


# --- Password hashing (OWASP Argon2id) ---

pwd_context = CryptContext(
    schemes=["argon2"], deprecated="auto",
    argon2__memory_cost=65536, argon2__time_cost=3, argon2__parallelism=4,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password. Argon2 natively supports long passwords."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    """Generate Argon2id hash."""
    return pwd_context.hash(password)


# --- Token generation ---


def create_access_token(user_id: int, version: int) -> tuple[str, int, str]:
    """Generate Access Token. Returns (token, expires_in_seconds, jti)."""
    exp_minutes = _expire_minutes()
    expire = datetime.now(UTC) + timedelta(minutes=exp_minutes)
    jti = str(uuid.uuid4())
    to_encode = {
        "exp": expire,
        "sub": str(user_id),
        "ver": version,
        "jti": jti,
        "type": "access",
        "iat": datetime.now(UTC),
    }
    expire_in = exp_minutes * 60
    token = jwt.encode(to_encode, _secret(), algorithm=_algorithm())
    return token, expire_in, jti


def generate_refresh_token_pair(user_id: int) -> tuple[str, str]:
    """Generate Refresh Token and its JTI."""
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + timedelta(days=7)
    payload = {"sub": str(user_id), "jti": jti, "exp": expire, "type": "refresh"}
    token = jwt.encode(payload, _refresh_secret(), algorithm=_algorithm())
    return token, jti


# --- Token decode & validation ---


def decode_token(token: str, is_refresh: bool = False) -> dict:
    """Unified token decode and validation."""
    if not token:
        raise TokenMissingError("未提供认证令牌")

    secret = _refresh_secret() if is_refresh else _secret()
    expected_type = "refresh" if is_refresh else "access"

    try:
        payload = jwt.decode(token, secret, algorithms=[_algorithm()])
        if payload.get("type") != expected_type:
            raise TokenMisuseError("令牌用途非法")
        return payload
    except InvalidTokenError as e:
        raise TokenInvalidError("令牌无效或已过期") from e


# --- Ops utility ---


async def revoke_all_user_tokens(user_id: int, redis):
    """Clear all refresh token records for a user in Redis."""
    pattern = f"auth:rt:{user_id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)

