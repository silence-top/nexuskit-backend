# app/main.py — FastAPI application entry point
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nexuskit_sdk import init_app, response

from app.core.config import get_app_settings, get_oss_settings
from app.core.lifespan import lifespan
from app.domains.slice.router import router as slice_router
from app.integrations.storage.oss import OssStorageClient
from app.middleware.gateway_auth import GatewayAuthMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

_settings = get_app_settings()

app = FastAPI(
    title=_settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# State — shared resources (Storage client via ACL)
# ------------------------------------------------------------------
app.state.storage = OssStorageClient(get_oss_settings())

# ------------------------------------------------------------------
# Middleware（注册顺序：后注册先执行）
# 1. GatewayAuth（最先执行，拦截非网关请求）
# 2. CORS
# 3. NexusTraceMiddleware（由 init_app 注册）
# ------------------------------------------------------------------

app.add_middleware(GatewayAuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# SDK: 注册 NexusTraceMiddleware + 异常处理器（422 / 500）
# ------------------------------------------------------------------
init_app(app)

# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------

app.include_router(slice_router, prefix="/api/v1")

# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------

@app.get("/health", tags=["ops"])
async def health():
    return response.success(data={"status": "ok", "service": _settings.PROJECT_NAME})
