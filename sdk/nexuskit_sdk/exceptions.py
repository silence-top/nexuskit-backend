from typing import Any
from dataclasses import dataclass
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .codes import BizCode
from .response import fail
from .middleware import trace_ctx

# --- 1. 异常类定义 ---

@dataclass
class NexusKitException(Exception):
    """NexusKit 全局异常基类"""
    code: int = BizCode.INTERNAL_ERROR
    message: str = "Internal Server Error"
    status_code: int = 500

    def to_payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message}

class AuthException(NexusKitException):
    """认证相关异常 (401 系列)"""
    def __init__(self, message: str = "Authentication failed", code: int = BizCode.UNAUTHORIZED, status_code: int = 401):
        super().__init__(code=code, message=message, status_code=status_code)

class TokenExpiredException(AuthException):
    """Token 已过期 (40101)"""
    def __init__(self, message: str = "Token expired", code: int = BizCode.TOKEN_EXPIRED, status_code: int = 401):
        super().__init__(message=message, code=code, status_code=status_code)

class PermissionException(NexusKitException):
    """权限相关异常 (403 系列)"""
    def __init__(self, message: str = "Permission denied", code: int = BizCode.FORBIDDEN, status_code: int = 403):
        super().__init__(code=code, message=message, status_code=status_code)

class AppAccessException(PermissionException):
    """分系统隔离：该用户无权进入当前系统 (40301)"""
    def __init__(self, message: str = "App access denied", code: int = BizCode.APP_FORBIDDEN, status_code: int = 403):
        super().__init__(message=message, code=code, status_code=status_code)

class ValidationException(NexusKitException):
    """业务逻辑中的参数校验异常 (400 系列)"""
    def __init__(self, message: str = "Invalid parameters", code: int = BizCode.BAD_REQUEST, status_code: int = 400):
        super().__init__(code=code, message=message, status_code=status_code)

class NotFoundException(NexusKitException):
    """资源未找到异常 (404 系列)"""
    def __init__(self, message: str = "Resource not found", code: int = BizCode.NOT_FOUND, status_code: int = 404):
        super().__init__(code=code, message=message, status_code=status_code)

class TooManyRequestsException(NexusKitException):
    """触发限流 (429 系列)"""
    def __init__(self, message: str = "Too many requests", code: int = BizCode.TOO_MANY, status_code: int = 429):
        super().__init__(code=code, message=message, status_code=status_code)

class ServiceUnavailableException(NexusKitException):
    """上游服务不可用 (503 系列)"""
    def __init__(self, message: str = "Service unavailable", code: int = BizCode.UNAVAILABLE, status_code: int = 503):
        super().__init__(code=code, message=message, status_code=status_code)

# --- 2. 异常处理器 ---

def _build_fail_response(code: int, message: str, status_code: int) -> JSONResponse:
    """统一构造 fail 响应"""
    return JSONResponse(
        status_code=status_code,
        content=fail(code=code, message=message, trace_id=trace_ctx.get())
    )

async def nexuskit_exception_handler(request: Request, exc: NexusKitException) -> JSONResponse:
    """处理自定义业务异常 (NexusKitException 及其子类)"""
    return _build_fail_response(code=exc.code, message=exc.message, status_code=exc.status_code)

def _format_validation_errors(exc: RequestValidationError) -> str:
    """把 pydantic/fastapi 的 errors() 转成单行可读字符串"""
    parts: list[str] = []
    for err in exc.errors():
        location = " -> ".join(map(str, err.get("loc", [])))
        msg = err.get("msg", "")
        parts.append(f"[{location}]: {msg}")
    return "请求参数格式错误: " + " | ".join(parts) if parts else "请求参数格式错误"

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理 FastAPI/Pydantic 自动抛出的 422 参数校验异常"""
    full_message = _format_validation_errors(exc)
    return _build_fail_response(code=BizCode.UNPROCESSABLE, message=full_message, status_code=422)

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """最后一道防线：拦截所有未捕获的系统异常 (500)"""
    # 建议在这里记录完整堆栈日志（logger.exception）
    return _build_fail_response(code=BizCode.INTERNAL_ERROR, message="服务器内部错误，请稍后再试", status_code=500)


# --- 3. 一键注册函数（类型提示并修正调用示例） ---

def setup_exception_handlers(app: FastAPI) -> None:
    """在 main.py 中调用 setup_exception_handlers(app) 即可完成注册"""
    app.add_exception_handler(NexusKitException, nexuskit_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
