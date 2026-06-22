# sdk/response.py
from typing import Any, Generic, TypeVar
from pydantic import BaseModel
from .codes import BizCode

T = TypeVar("T")


class UnionResponse(BaseModel, Generic[T]):
    """
    统一响应模型
    - code: 业务码
    - message: 可读错误/成功信息
    - data: 可选业务数据
    - trace_id: 可选链路 id
    """
    code: int
    message: str
    data: T | None = None
    trace_id: str | None = None

def success(data: Any = None, message: str = "success", trace_id: str | None = None) -> dict:
    """
    返回成功响应的 dict（已通过 Pydantic 校验）
    保持与原实现兼容：返回 plain dict 以便直接传给 FastAPI。
    """
    return UnionResponse[Any](
        code=BizCode.SUCCESS,
        message=message,
        data=data,
        trace_id=trace_id
    ).model_dump()

def fail(code: int, message: str, trace_id: str | None = None) -> dict:
    """
    返回失败响应的 dict（已通过 Pydantic 校验）
    """
    return UnionResponse[None](
        code=code,
        message=message,
        data=None,
        trace_id=trace_id
    ).model_dump()
