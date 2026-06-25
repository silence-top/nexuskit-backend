# app/integrations/storage/oss.py — 阿里云 OSS 存储实现
"""
阿里云 OSS 驱动，实现 StorageClient 抽象接口。
支持多 Bucket 路由：按 app_code 路由到对应 Bucket，不存在则回退 default。
"""
import asyncio
import io
import json

import oss2

from app.core.config import OssSettings
from app.integrations.storage.base import StorageClient


class OssStorageClient(StorageClient):
    """阿里云 OSS 具体实现。"""

    def __init__(self, settings: OssSettings) -> None:
        self._auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        self._endpoint = settings.OSS_ENDPOINT
        self._bucket_map: dict[str, str] = json.loads(settings.OSS_BUCKET_MAP)

    def _get_bucket(self, app_code: str) -> oss2.Bucket:
        """按 app_code 返回对应 Bucket 客户端，不存在则回退 default。"""
        bucket_name = self._bucket_map.get(app_code) or self._bucket_map.get("default")
        if not bucket_name:
            raise ValueError(f"OSS_BUCKET_MAP 中找不到 app_code='{app_code}' 且无 default 配置")
        return oss2.Bucket(self._auth, self._endpoint, bucket_name)

    async def upload(self, bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """上传文件到 OSS，返回 oss_key。在线程池中执行阻塞 IO。"""
        oss_bucket = self._get_bucket(bucket)

        def _put():
            headers = {"Content-Type": content_type}
            oss_bucket.put_object(key, io.BytesIO(data), headers=headers)

        await asyncio.get_event_loop().run_in_executor(None, _put)
        return key

    def get_presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        """生成预签名下载 URL，默认有效期 1 小时。"""
        oss_bucket = self._get_bucket(bucket)
        return oss_bucket.sign_url("GET", key, expires)

    async def delete(self, bucket: str, key: str) -> None:
        """删除 OSS 对象。"""
        oss_bucket = self._get_bucket(bucket)

        def _del():
            oss_bucket.delete_object(key)

        await asyncio.get_event_loop().run_in_executor(None, _del)

    async def exists(self, bucket: str, key: str) -> bool:
        """检查 OSS 对象是否存在。"""
        oss_bucket = self._get_bucket(bucket)
        try:
            await asyncio.get_event_loop().run_in_executor(None, lambda: oss_bucket.head_object(key))
            return True
        except oss2.exceptions.NoSuchKey:
            return False
