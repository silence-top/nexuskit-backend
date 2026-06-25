# middleware/trace.py — Trace ID full-chain injection
import uuid
from collections.abc import Callable
from contextvars import ContextVar

# Global trace context
trace_ctx: ContextVar[str] = ContextVar("trace_id", default="")


class TraceMiddleware:
    """Inject X-NexusKit-Trace-Id header into request/response cycle."""

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        raw_tid = headers.get(b"x-nexuskit-trace-id")

        trace_id = raw_tid.decode() if raw_tid else f"nk-{uuid.uuid4().hex[:8]}"
        token = trace_ctx.set(trace_id)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append(
                    (b"x-nexuskit-trace-id", trace_id.encode())
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            trace_ctx.reset(token)
