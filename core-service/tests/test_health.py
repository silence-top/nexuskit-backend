"""
Health 端点基础测试
"""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """验证 /health 端点正常响应"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_register_validation_error(client):
    """验证注册接口参数校验 (422)"""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "ab",  # 太短 (min_length=3)
            "email": "not-email",  # 无效邮箱
            "password": "123",  # 太短 (min_length=6)
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["code"] == 42200
