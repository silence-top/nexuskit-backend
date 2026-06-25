# app/domains/slice/router.py — /slices routes
from fastapi import APIRouter, Form, Query, Request, UploadFile, status

from app.domains.slice.dependencies import ServiceDep
from app.domains.slice.schemas import (
    SliceFileOut,
    SliceListQuery,
    SlicePresignedUrlOut,
    SliceUploadMeta,
)
from nexuskit_sdk import response

router = APIRouter(prefix="/slices", tags=["slices"])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_slice(
    request: Request,
    svc: ServiceDep,
    file: UploadFile,
    case_id: str | None = Form(None),
    patient_id: str | None = Form(None),
    staining_type: str = Form(...),
    description: str | None = Form(None),
):
    """上传病理切片文件（multipart/form-data）。

    鉴权：读取网关注入的 `X-User-Id` 和 `X-App-Code`（由 GatewayAuthMiddleware 验证并注入 request.state）。
    """
    meta = SliceUploadMeta(
        case_id=case_id,
        patient_id=patient_id,
        staining_type=staining_type,
        description=description,
    )
    obj = await svc.upload(
        app_code=request.state.app_code,
        user_id=request.state.user_id,
        file=file,
        meta=meta,
    )
    return response.success(data=obj.model_dump())


@router.get("")
async def list_slices(
    svc: ServiceDep,
    app_code: str | None = Query(None),
    case_id: str | None = Query(None),
    patient_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """分页查询切片列表，支持 app_code / case_id / patient_id / status 过滤。"""
    query = SliceListQuery(
        app_code=app_code,
        case_id=case_id,
        patient_id=patient_id,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    items, total = await svc.list(query)
    return response.success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [i.model_dump() for i in items],
    })


@router.get("/{slice_id}")
async def get_slice(slice_id: int, svc: ServiceDep):
    """获取切片元数据详情。"""
    obj = await svc.get(slice_id)
    return response.success(data=obj.model_dump())


@router.get("/{slice_id}/url")
async def get_presigned_url(
    slice_id: int,
    svc: ServiceDep,
    expires: int = Query(3600, ge=60, le=86400, description="URL 有效秒数（60s ~ 24h）"),
):
    """获取 OSS 预签名下载 URL。"""
    obj = await svc.get(slice_id)
    url = svc.get_presigned_url(obj, expires=expires)
    result = SlicePresignedUrlOut(slice_id=slice_id, url=url, expires_in=expires)
    return response.success(data=result.model_dump())


@router.delete("/{slice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slice(slice_id: int, svc: ServiceDep):
    """删除切片记录及 OSS 对象。"""
    await svc.delete(slice_id)
