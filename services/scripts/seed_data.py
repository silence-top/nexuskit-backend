"""
基础数据初始化脚本
- 可独立运行: python scripts/seed_data.py
- 也可被 main.py lifespan 自动调用
"""

import asyncio
import logging
import uuid

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import AsyncSessionLocal
from core.security import get_password_hash

# Import domain models
from domains.auth.models import User
from domains.identity.models import App, Department, Permission, Role, user_roles

logger = logging.getLogger("nexuskit.seed")


async def _seed_permissions(db: AsyncSession) -> bool:
    """Initialize base permission data. Returns True if any new records were created."""
    created = False

    # 1. Initialize app
    result = await db.execute(select(App).where(App.app_code == "platform"))
    platform_app = result.scalar_one_or_none()

    if not platform_app:
        platform_app = App(
            app_code="platform",
            app_name="NexusKit 核心管理平台",
            app_secret=uuid.uuid4().hex,
        )
        db.add(platform_app)
        await db.flush()
        logger.info("  + 应用 'platform' 已创建")
        created = True

    # 2. Initialize department
    result = await db.execute(select(Department).where(Department.dept_name == "总公司"))
    root_dept = result.scalar_one_or_none()

    if not root_dept:
        root_dept = Department(dept_name="总公司", parent_id=None, sort=1, leader="Admin", is_active=True)
        db.add(root_dept)
        await db.flush()

        tech_dept = Department(dept_name="研发中心", parent_id=root_dept.id, sort=1, is_active=True)
        db.add(tech_dept)
        await db.flush()
        logger.info("  + 组织架构: 总公司 -> 研发中心")
        created = True

    # 3. Initialize permission tree
    result = await db.execute(select(Permission).where(Permission.code == "sys:mng"))
    sys_mng = result.scalar_one_or_none()

    if not sys_mng:
        sys_mng = Permission(app_code="platform", code="sys:mng", name="系统管理", type="M", icon="setting", sort=100)
        db.add(sys_mng)
        await db.flush()

        user_mng = Permission(
            app_code="platform",
            parent_id=sys_mng.id,
            code="sys:user:view",
            name="用户管理",
            type="C",
            path="/system/user",
            component="system/user/index",
            icon="user",
            sort=1,
        )
        db.add(user_mng)
        await db.flush()

        user_add = Permission(
            app_code="platform", parent_id=user_mng.id, code="sys:user:add", name="新增用户", type="F", sort=1
        )
        db.add(user_add)
        logger.info("  + 权限树: 系统管理 -> 用户管理 -> 新增用户")
        created = True

    # 4. Initialize role
    result = await db.execute(select(Role).where(Role.role_code == "super_admin"))
    admin_role = result.scalar_one_or_none()

    if not admin_role:
        admin_role = Role(app_code="platform", role_name="超级管理员", role_code="super_admin")
        all_perms = (await db.execute(select(Permission))).scalars().all()
        admin_role.permissions = list(all_perms)
        db.add(admin_role)
        await db.flush()
        logger.info("  + 角色 'super_admin' 已创建并绑定所有权限")
        created = True

    # 5. Initialize admin user
    result = await db.execute(select(User).where(User.username == "admin"))
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        admin_user = User(
            username="admin", hashed_password=get_password_hash("admin123"), email="admin@nexuskit.com", is_active=True
        )
        db.add(admin_user)
        await db.flush()

        # Insert into user_roles association table directly (no cross-domain relationship)
        await db.execute(insert(user_roles).values(user_id=admin_user.id, role_id=admin_role.id))
        logger.info("  + 用户 'admin' (密码: admin123) 已创建")
        created = True

    await db.commit()
    return created


async def seed_if_empty():
    """
    Idempotent seed: safe to call repeatedly.
    Called by main.py lifespan on startup.
    """
    async with AsyncSessionLocal() as db:
        try:
            has_new = await _seed_permissions(db)
            if has_new:
                logger.info("基础数据初始化完成")
            else:
                logger.info("基础数据已存在，跳过初始化")
        except Exception as e:
            await db.rollback()
            logger.error(f"基础数据初始化失败: {e}")
            raise


async def main():
    """Standalone entry point."""
    logging.basicConfig(level=logging.INFO)
    logger.info("开始执行基础数据初始化...")
    await seed_if_empty()
    logger.info("初始化脚本执行完毕")


if __name__ == "__main__":
    asyncio.run(main())
