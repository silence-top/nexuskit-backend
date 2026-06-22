import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from nexuskit_sdk import init_app as setup_sdk_exception_handlers
from nexuskit_sdk import response

from common.exceptions.base import DomainError
from core.lifespan import lifespan
from domains.auth.router import router as auth_router
from domains.identity.router import router as identity_router
from middleware.trace import TraceMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nexuskit")

app = FastAPI(title="NexusKit Auth Service", lifespan=lifespan)

# Middleware: Trace ID injection
app.add_middleware(TraceMiddleware)

# SDK exception handlers (422 / 500 fallback)
setup_sdk_exception_handlers(app)

# Domain error → unified JSON response (no HTTP knowledge in exceptions)
# biz_code 优先使用子类显式绑定的业务码；未设置时回退到 status_code * 100
@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    biz_code = exc.biz_code if exc.biz_code is not None else exc.status_code * 100
    return JSONResponse(
        status_code=exc.status_code,
        content=response.fail(code=biz_code, message=exc.message),
    )

# Routes — version prefix controlled at mount point, not in domain routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证鉴权"])
app.include_router(identity_router, prefix="/api/v1/identity", tags=["身份管理"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
