import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import all domain models so Alembic/Base.metadata sees every table
import domains.auth.models  # noqa: F401
import domains.identity.models  # noqa: F401
from common.base import Base

from .config import get_app_settings, get_db_settings

logger = logging.getLogger("nexuskit")


def _make_engine():
    _db = get_db_settings()  # lru_cache — reads .env once
    return create_async_engine(_db.DATABASE_URL, echo=_db.DEBUG, pool_pre_ping=True)


def _make_redis_pool():
    _db = get_db_settings()
    return ConnectionPool.from_url(_db.REDIS_URL, decode_responses=True, max_connections=20)


engine = _make_engine()
pool = _make_redis_pool()
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# --- 建表函数 ---
async def init_db():
    """仅在非生产环境下用 create_all 建表；生产环境应由 Alembic 管理表结构。"""
    env = get_app_settings().ENVIRONMENT
    if env == "production":
        logger.warning("生产环境跳过 create_all，请使用 alembic upgrade head 管理表结构")
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def wait_for_db(max_retries: int = 30, delay: float = 1.0):
    """
    等待数据库就绪（带重试机制）
    - max_retries: 最大重试次数
    - delay: 每次重试间隔（秒）
    """
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ 数据库连接就绪")
            return
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"❌ 数据库连接失败，已重试 {max_retries} 次: {e}")
                raise
            logger.warning(f"⏳ 数据库未就绪 ({attempt}/{max_retries})，{delay}s 后重试...")
            await asyncio.sleep(delay)


async def get_redis():
    client = Redis(connection_pool=pool)
    try:
        yield client
    finally:
        # 对于连接池模式，这里的 close() 仅仅是回收到池
        # 如果你使用了 decode_responses=True，一定要确保 pool 也是这么配置的
        await client.aclose()  # 异步客户端建议使用 aclose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    依赖注入：数据库会话
    1. 当接口被调用时，它会创建一个数据库会话。
    2. 接口逻辑执行完后，它会自动关闭会话，释放资源。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# --- 可复用的依赖类型别名 (Annotated 风格) ---
DbDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]
