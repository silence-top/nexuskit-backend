from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

# 导入内部模块逻辑
from .exceptions import (
    NexusKitException, 
    AuthException, 
    TokenExpiredException,
    PermissionException, 
    AppAccessException,
    ValidationException,
    NotFoundException,
    TooManyRequestsException,
    ServiceUnavailableException,
    nexuskit_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)
from .middleware import NexusTraceMiddleware, trace_ctx
from . import response

def init_app(app: FastAPI):
    """
    一键初始化 NexusKit 骨架：
    1. 注册追踪中间件 (Trace ID)
    2. 注册所有异常处理器 (400, 422, 500)
    """
    # 注册中间件
    app.add_middleware(NexusTraceMiddleware)
    
    # 注册自定义业务异常 (400, 401, 403, 404 等)
    app.add_exception_handler(NexusKitException, nexuskit_exception_handler)
    
    # 注册参数校验异常 (422)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 注册系统兜底异常 (500)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    
    return app

# 定义对外暴露的 API
__all__ = [
    "init_app",
    "NexusKitException",
    "AuthException",
    "TokenExpiredException",
    "PermissionException",
    "AppAccessException",
    "ValidationException",
    "NotFoundException",
    "TooManyRequestsException",
    "ServiceUnavailableException",
    "trace_ctx",
    "response"
]