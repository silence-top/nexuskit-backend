# middleware/gateway_trust.py — 验证请求来自受信任的网关
"""
验证逻辑：
  1. 请求头必须携带 X-Gateway-Token: {timestamp}.{hmac}
  2. HMAC = SHA256(timestamp, INTERNAL_SECRET)，签名必须匹配
  3. 时间戳必须在当前时间 ±30s 窗口内（防重放攻击）

跳过路径：
  - /health         （K8s / Docker 探活）
  - /docs /openapi  （开发阶段 Swagger UI，生产应关闭）
"""
import hashlib
import hmac
import time
from collections.abc import Callable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from core.config import get_auth_settings

# 允许的时间偏差（秒），兼容网关与后端时钟轻微不同步
_WINDOW_SECONDS = 30

# 不校验网关令牌的路径前缀
_SKIP_PREFIXES = ("/health", "/docs", "/openapi", "/redoc")


class GatewayTrustMiddleware:
    """拒绝所有未经网关签名的直连请求。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._secret = get_auth_settings().INTERNAL_SECRET.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        token = headers.get(b"x-gateway-token", b"").decode()

        if not self._verify(token):
            response = JSONResponse(
                status_code=401,
                content={"code": 40100, "message": "Direct access forbidden: missing or invalid gateway token"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _verify(self, token: str) -> bool:
        """验证 {timestamp}.{hmac} 格式的令牌。"""
        try:
            ts_str, sig = token.split(".", 1)
        except ValueError:
            return False

        # 1. 时间窗口校验
        try:
            ts = int(ts_str)
        except ValueError:
            return False
        if abs(time.time() - ts) > _WINDOW_SECONDS:
            return False

        # 2. HMAC 签名校验（使用 hmac.compare_digest 防时序攻击）
        expected = hmac.new(self._secret, ts_str.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)
