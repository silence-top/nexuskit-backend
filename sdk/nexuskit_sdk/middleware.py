import uuid
from contextvars import ContextVar
from typing import Callable, Awaitable

# 全局 Trace 上下文
trace_ctx: ContextVar[str] = ContextVar("trace_id", default="")

class NexusTraceMiddleware:
    def __init__(self, app: Callable):
        self.app = app

    async def __call__(
        self,
        scope,
        receive,
        send,
    ):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 1️⃣ 读取 Header
        headers = dict(scope.get("headers", []))
        raw_tid = headers.get(b"x-nexuskit-trace-id")

        trace_id = (
            raw_tid.decode()
            if raw_tid
            else f"nk-{uuid.uuid4().hex[:8]}"
        )

        token = trace_ctx.set(trace_id)

        async def send_wrapper(message):
            # 2️⃣ 回写 Trace Header
            if message["type"] == "http.response.start":
                response_headers = message.setdefault(
                    "headers", []
                )
                response_headers.append(
                    (
                        b"x-nexuskit-trace-id",
                        trace_id.encode(),
                    )
                )

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # 3️⃣ 清理上下文，防止泄漏
            trace_ctx.reset(token)
