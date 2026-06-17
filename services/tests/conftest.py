"""
测试配置与 fixtures
运行测试: cd services && python -m pytest tests/ -v
"""

import pytest
from httpx import ASGITransport, AsyncClient

from core.db import get_db, get_redis
from main import app


# --- Mock DB Session (无需真实数据库) ---
class MockSession:
    async def execute(self, *args, **kwargs):
        class Result:
            def scalar_one_or_none(self):
                return None

            def scalars(self):
                class Scalars:
                    def first(self):
                        return None

                    def all(self):
                        return []

                return Scalars()

        return Result()

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def refresh(self, obj):
        pass

    async def close(self):
        pass

    async def get(self, model, pk):
        return None

    def add(self, obj):
        pass


async def mock_get_db():
    yield MockSession()


async def mock_get_redis():
    class MockRedis:
        async def get(self, key):
            # Simulate valid refresh token session (format: valid:<at_jti>)
            if key.startswith("auth:rt:"):
                return b"valid:mock-at-jti"
            # AT blacklist keys should return None (not blacklisted) in tests
            if key.startswith("auth:at:blacklist:"):
                return None
            return None

        async def setex(self, *args):
            pass

        async def keys(self, pattern):
            # Simulate at least one valid session key for auth dependency
            if pattern.startswith("auth:rt:"):
                return ["auth:rt:1:mock-jti"]
            return []

        async def delete(self, *keys):
            pass

        async def pipeline(self, transaction=False):
            class MockPipeline:
                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

                def setex(self, *args):
                    return self

                def sadd(self, *args):
                    return self

                def expire(self, *args):
                    return self

                def delete(self, *args):
                    return self

                async def execute(self):
                    return []

            return MockPipeline()

    yield MockRedis()


@pytest.fixture(autouse=True)
def _override_deps():
    """全局覆盖 DB 和 Redis 依赖，避免测试连接真实服务"""
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_redis] = mock_get_redis
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    """异步测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
