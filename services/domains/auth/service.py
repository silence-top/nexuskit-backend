# domains/auth/service.py — Auth business logic
from redis.asyncio import Redis

from core.config import get_auth_settings
from core.security import (
    create_access_token,
    decode_token,
    generate_refresh_token_pair,
    get_password_hash,
    revoke_all_user_tokens,
    verify_password,
)
from domains.auth.exceptions import (
    InvalidCredentialsError,
    TokenRefreshConflictError,
    TokenRevokedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from domains.auth.repository import UserRepository
from domains.auth.schemas import LoginResponse, PasswordChange, TokenPair, UserCreate, UserLogin, UserRead
from domains.identity.service import IdentityService


class AuthService:
    def __init__(self, repo: UserRepository, redis: Redis, identity_service: IdentityService) -> None:
        self.repo = repo
        self.redis = redis
        self.identity_service = identity_service

    # --- 修改密码（本人） ---

    async def register(self, user_in: UserCreate) -> UserRead:
        """Guard -> create -> commit -> return schema (ORM never leaves this method)."""
        if await self.repo.get_by_email(user_in.email):
            raise UserAlreadyExistsError("邮笱已存在")
        user = await self.repo.create(
            username=user_in.username,
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
        )
        await self.repo.session.commit()
        await self.repo.session.refresh(user)
        return UserRead.model_validate(user)

    # --- 修改密码（本人） ---

    async def change_password(self, user_id: int, data: PasswordChange) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("用户不存在")
        if not verify_password(data.old_password, user.hashed_password):
            raise InvalidCredentialsError("旧密码错误")
        await self.repo.update(user, hashed_password=get_password_hash(data.new_password), version=user.version + 1)
        await self.repo.session.commit()
        # 密码变更后强制重新登录
        await revoke_all_user_tokens(user_id, self.redis)
    
    # --- 强制下线（本人/公共） ---

    async def force_logout(self, user_id: int) -> None:
        """Revoke all sessions for a user."""
        await revoke_all_user_tokens(user_id, self.redis)

    # --- Login ---

    async def login(self, user_in: UserLogin, app_code: str) -> LoginResponse:
        """Verify credentials, get roles via IdentityService, issue token pair."""
        user = await self.repo.get_by_username(user_in.username)
        if not user or not verify_password(user_in.password, user.hashed_password):
            raise InvalidCredentialsError("账号或密码错误")

        # Cross-domain call: check app access before issuing token
        await self.identity_service.check_user_app_access(user.id, app_code)

        # Invalidate all existing sessions before issuing new token pair
        await self._revoke_all_sessions(user.id)

        token_pair = await self._issue_token_pair(user.id, user.version)
        user_schema = UserRead.model_validate(user)
        return LoginResponse(**token_pair, user=user_schema)

    # --- Token refresh ---

    async def refresh(self, user_id: int, old_jti: str, user_version: int) -> TokenPair:
        """Rotate refresh token with replay-attack protection."""
        rt_key = f"auth:rt:{user_id}:{old_jti}"
        rt_data = await self.redis.get(rt_key)

        if rt_data is None:
            await revoke_all_user_tokens(user_id, self.redis)
            raise TokenRevokedError("令牌风险：已全端强制下线")

        if rt_data == b"used" or rt_data == "used":
            raise TokenRefreshConflictError("刷新并发限制")

        # Extract old AT JTI from RT record (format: "valid:<at_jti>" or just "valid")
        old_at_jti = None
        if rt_data and ":" in (rt_data if isinstance(rt_data, str) else rt_data.decode()):
            old_at_jti = (rt_data if isinstance(rt_data, str) else rt_data.decode()).split(":", 1)[1]

        new_at, new_expire_in, new_at_jti = create_access_token(user_id, user_version)
        new_rt, new_jti = generate_refresh_token_pair(user_id)

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.setex(rt_key, 15, "used")
            # Store RT with associated AT JTI for future blacklist on refresh
            pipe.setex(f"auth:rt:{user_id}:{new_jti}", 7 * 24 * 3600, f"valid:{new_at_jti}")
            # Blacklist the old access token's JTI
            if old_at_jti:
                pipe.setex(f"auth:at:blacklist:{old_at_jti}", new_expire_in, "1")
            await pipe.execute()

        return TokenPair(
            access_token=new_at,
            refresh_token=new_rt,
            expires_in=new_expire_in,
        )

    async def refresh_from_token(self, raw_refresh_token: str) -> TokenPair:
        """Decode raw token then rotate."""
        payload = decode_token(raw_refresh_token, is_refresh=True)
        user_id = int(payload["sub"])
        old_jti = payload["jti"]
        user_version = int(payload.get("ver", 1))
        return await self.refresh(user_id, old_jti, user_version)

    # --- Internal helpers ---

    async def _revoke_all_sessions(self, user_id: int) -> None:
        """Blacklist all active AT JTIs and delete all RT keys for the user."""
        pattern = f"auth:rt:{user_id}:*"
        rt_keys = await self.redis.keys(pattern)
        if not rt_keys:
            return
        at_expire = get_auth_settings().ACCESS_TOKEN_EXPIRE_MINUTES * 60
        async with self.redis.pipeline(transaction=True) as pipe:
            for key in rt_keys:
                rt_data = await self.redis.get(key)
                if rt_data and ":" in (rt_data if isinstance(rt_data, str) else rt_data.decode()):
                    old_at_jti = (rt_data if isinstance(rt_data, str) else rt_data.decode()).split(":", 1)[1]
                    pipe.setex(f"auth:at:blacklist:{old_at_jti}", at_expire, "1")
            pipe.delete(*rt_keys)
            await pipe.execute()

    async def _issue_token_pair(self, user_id: int, version: int) -> dict:
        access_token, expire_in, at_jti = create_access_token(user_id=user_id, version=version)
        refresh_token, jti = generate_refresh_token_pair(user_id)
        rt_key = f"auth:rt:{user_id}:{jti}"
        # Store RT with associated AT JTI: "valid:<at_jti>" — enables auto-blacklist on refresh
        await self.redis.setex(rt_key, 7 * 24 * 3600, f"valid:{at_jti}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expire_in,
            "token_type": "bearer",
        }
