from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)


class DbSettings(BaseSettings):
    model_config = _ENV
    DATABASE_URL: str
    REDIS_URL: str
    DEBUG: bool = False


class AuthSettings(BaseSettings):
    model_config = _ENV
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    REFRESH_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    INTERNAL_SECRET: str


class AppSettings(BaseSettings):
    model_config = _ENV
    PROJECT_NAME: str = "NexusKit Auth"
    ENVIRONMENT: str = "development"  # local | development | staging | production


@lru_cache
def get_db_settings() -> DbSettings:
    return DbSettings()


@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings()


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()
