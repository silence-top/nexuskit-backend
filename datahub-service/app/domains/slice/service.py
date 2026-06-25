# app/domains/slice/service.py — SliceFile business logic
import os
from collections.abc import Sequence

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.slice.exceptions import (
    SliceNotFoundError,
    StorageDeleteError,
    StorageUploadError,
    UnsupportedFileFormatError,
)
from app.domains.slice.models import SliceFile
from app.domains.slice.repository import SliceRepository
from app.domains.slice.schemas import SliceFileOut, SliceListQuery, SliceUploadMeta
from app.integrations.storage.base import StorageClient

# 允许上传的文件扩展名白名单
_ALLOWED_EXTENSIONS = {".svs", ".ndpi", ".tiff", ".tif", ".mrxs", ".vms", ".vmu", ".scn", ".czi"}


class SliceService:
    def __init__(self, db: AsyncSession, storage: StorageClient) -> None:
        self._repo = SliceRepository(db)
        self._db = db
        self._storage = storage

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    async def upload(
        self,
        *,
        app_code: str,
        user_id: int,
        file: UploadFile,
        meta: SliceUploadMeta,
    ) -> SliceFileOut:
        """接收上传文件 → OSS → 写入 DB，返回 SliceFileOut schema。"""
        original_name = file.filename or "unknown"
        ext = os.path.splitext(original_name)[1].lower()

        if ext not in _ALLOWED_EXTENSIONS:
            raise UnsupportedFileFormatError(ext, list(_ALLOWED_EXTENSIONS))

        file_format = ext.lstrip(".")
        data = await file.read()
        file_size = len(data)

        # 构建 OSS key
        oss_key = StorageClient.build_key(app_code, original_name)

        # 上传到 OSS（捕获具体异常，转为域异常）
        try:
            await self._storage.upload(
                bucket=app_code,
                key=oss_key,
                data=data,
                content_type=file.content_type or "application/octet-stream",
            )
        except Exception as exc:
            raise StorageUploadError(str(exc)) from exc

        # 写入数据库
        async with self._db.begin():
            obj = await self._repo.create(
                app_code=app_code,
                case_id=meta.case_id,
                patient_id=meta.patient_id,
                original_name=original_name,
                file_format=file_format.upper(),
                staining_type=meta.staining_type,
                file_size=file_size,
                oss_key=oss_key,
                status="ready",
                uploaded_by=user_id,
            )
        return SliceFileOut.model_validate(obj)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    async def list(self, query: SliceListQuery) -> tuple[list[SliceFileOut], int]:
        items, total = await self._repo.list(query)
        return [SliceFileOut.model_validate(i) for i in items], total

    async def get(self, slice_id: int) -> SliceFileOut:
        obj = await self._repo.get_by_id(slice_id)
        if obj is None:
            raise SliceNotFoundError(slice_id)
        return SliceFileOut.model_validate(obj)

    # ------------------------------------------------------------------
    # Presigned URL
    # ------------------------------------------------------------------

    def get_presigned_url(self, obj: SliceFileOut, expires: int = 3600) -> str:
        return self._storage.get_presigned_url(
            bucket=obj.app_code,
            key=obj.oss_key,
            expires=expires,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(self, slice_id: int) -> None:
        # 先获取记录
        obj = await self._repo.get_by_id(slice_id)
        if obj is None:
            raise SliceNotFoundError(slice_id)

        # 先删除 OSS 对象，避免数据库记录删了 OSS 还留着
        try:
            await self._storage.delete(bucket=obj.app_code, key=obj.oss_key)
            if obj.thumbnail_key:
                await self._storage.delete(bucket=obj.app_code, key=obj.thumbnail_key)
        except Exception as exc:
            raise StorageDeleteError(str(exc)) from exc

        async with self._db.begin():
            await self._repo.delete(obj)
