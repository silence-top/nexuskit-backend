# app/core/config.py — Datahub Service configuration
import json
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)


class DbSettings(BaseSettings):
    model_config = _ENV
    DATABASE_URL: str
    DEBUG: bool = False


class OssSettings(BaseSettings):
    """阿里云 OSS 配置，支持多 Bucket（按 app_code 路由）。

    OSS_BUCKET_MAP 格式（JSON 字符串）：
        '{"default":"bucket-default","nexuskit":"bucket-nexuskit","diagnosis":"bucket-diag"}'
    """
    model_config = _ENV
    OSS_ACCESS_KEY_ID: str
    OSS_ACCESS_KEY_SECRET: str
    OSS_ENDPOINT: str           # e.g. oss-cn-hangzhou.aliyuncs.com
    OSS_BUCKET_MAP: str         # JSON: {app_code: bucket_name, "default": bucket_name}

    def bucket_map(self) -> dict[str, str]:
        return json.loads(self.OSS_BUCKET_MAP)


class AppSettings(BaseSettings):
    model_config = _ENV
    PROJECT_NAME: str = "Datahub Service"
    ENVIRONMENT: str = "development"
    # NexusKit 内部调用凭证（服务间鉴权）
    NEXUSKIT_URL: str = "http://localhost:5000"
    NEXUSKIT_APP_CODE: str = "datahub"
    NEXUSKIT_APP_SECRET: str = ""


@lru_cache
def get_db_settings() -> DbSettings:
    return DbSettings()


@lru_cache
def get_oss_settings() -> OssSettings:
    return OssSettings()


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()
