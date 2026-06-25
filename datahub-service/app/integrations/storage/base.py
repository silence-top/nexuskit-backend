# app/integrations/storage/base.py — 存储层抽象基类（ACL 防腐层）
"""
防腐层设计：
  - 业务域（slice service）仅依赖 StorageClient 抽象接口
  - 具体实现（OssStorageClient / MinIOClient）在运行时注入
  - 未来切换存储后端只需替换实现类，业务代码零改动
"""
from abc import ABC, abstractmethod


class StorageClient(ABC):
    """对象存储抽象接口，所有存储后端必须实现此契约。"""

    @abstractmethod
    async def upload(self, bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """上传对象，返回 oss_key。"""
        ...

    @abstractmethod
    async def delete(self, bucket: str, key: str) -> None:
        """删除对象。"""
        ...

    @abstractmethod
    def get_presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        """生成预签名下载 URL（同步方法，不涉及网络 I/O）。"""
        ...

    @abstractmethod
    async def exists(self, bucket: str, key: str) -> bool:
        """检查对象是否存在。"""
        ...

    @staticmethod
    def build_key(app_code: str, original_filename: str, prefix: str = "slices") -> str:
        """生成 OSS 对象路径：{prefix}/{app_code}/{YYYY}/{uuid}{ext}"""
        import uuid
        from datetime import datetime
        from pathlib import PurePosixPath

        ext = PurePosixPath(original_filename).suffix.lower()
        year = datetime.now().strftime("%Y")
        return f"{prefix}/{app_code}/{year}/{uuid.uuid4().hex}{ext}"
