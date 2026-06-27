# domains/identity/repository.py — Permission & Role data access
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Permission, Role, role_permissions


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, menu_id: int) -> Permission | None:
        return await self.session.get(Permission, menu_id)

    async def get_children(self, menu_id: int) -> list[Permission]:
        result = await self.session.execute(
            select(Permission).where(Permission.parent_id == menu_id)
        )
        return list(result.scalars().all())

    async def get_all_by_app(self, app_code: str, is_active: bool | None = None) -> list[Permission]:
        """一次拉取指定 App 全部权限节点（扁平），按 sort 排序。"""
        stmt = select(Permission).where(Permission.app_code == app_code)
        if is_active is not None:
            stmt = stmt.where(Permission.is_active.is_(is_active))
        stmt = stmt.order_by(Permission.sort.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── 递归 CTE：查询全部后代 ──────────────────────────

    async def get_descendant_ids(self, menu_id: int) -> list[int]:
        """PostgreSQL 递归 CTE：返回指定节点的全部后代 ID（含自身）。

        时间复杂度 O(h)，h = 子树高度，无需应用层递归。
        """
        cte = (
            select(Permission.id, Permission.parent_id)
            .where(Permission.id == menu_id)
            .cte("descendants", recursive=True)
        )
        cte = cte.union_all(
            select(Permission.id, Permission.parent_id)
            .where(Permission.parent_id == cte.c.id)
        )
        result = await self.session.execute(select(cte.c.id))
        return [row[0] for row in result.all()]

    async def get_ancestor_ids(self, menu_id: int) -> list[int]:
        """PostgreSQL 递归 CTE：返回指定节点到根的全部祖先 ID（含自身）。

        用于循环引用检测：若 new_parent_id 出现在当前节点的祖先链中，则形成环。
        """
        cte = (
            select(Permission.id, Permission.parent_id)
            .where(Permission.id == menu_id)
            .cte("ancestors", recursive=True)
        )
        cte = cte.union_all(
            select(Permission.id, Permission.parent_id)
            .join(cte, Permission.id == cte.c.parent_id)
        )
        result = await self.session.execute(select(cte.c.id))
        return [row[0] for row in result.all()]

    async def has_descendants(self, menu_id: int) -> bool:
        """快速判断是否存在后代（CTE + LIMIT 2，短路优化）。"""
        ids = await self.get_descendant_ids(menu_id)
        # 返回结果包含自身，> 1 表示有后代
        return len(ids) > 1

    # ── CRUD ────────────────────────────────────────────

    async def create(self, data: dict) -> Permission:
        perm = Permission(**data)
        self.session.add(perm)
        await self.session.flush()
        return perm

    async def update(self, menu_id: int, data: dict) -> Permission | None:
        perm = await self.get_by_id(menu_id)
        if perm is None:
            return None
        for key, value in data.items():
            setattr(perm, key, value)
        await self.session.flush()
        return perm

    async def delete(self, menu_id: int) -> bool:
        await self.session.execute(delete(Permission).where(Permission.id == menu_id))
        return True

    # ── Sync 批量操作 ─────────────────────────────

    async def batch_create(self, items: list[dict]) -> list[Permission]:
        """批量插入权限节点，返回已插入对象列表（含自增 id）。"""
        perms = [Permission(**data) for data in items]
        self.session.add_all(perms)
        await self.session.flush()
        return perms

    async def batch_update_fields(self, ids: list[int], fields: dict) -> int:
        """批量更新指定字段，返回受影响行数。"""
        if not ids:
            return 0
        stmt = (
            update(Permission)
            .where(Permission.id.in_(ids))
            .values(**fields)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount  # type: ignore[return-value]

    async def batch_soft_delete(self, ids: list[int]) -> int:
        """批量软下线（is_active=False），返回受影响行数。"""
        if not ids:
            return 0
        from datetime import datetime, timezone
        stmt = (
            update(Permission)
            .where(Permission.id.in_(ids))
            .values(is_active=False, synced_at=datetime.now(tz=timezone.utc))
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount  # type: ignore[return-value]

    async def get_descendant_ids_batch(self, root_ids: list[int]) -> list[int]:
        """PostgreSQL 递归 CTE：批量查询多个根节点的全部后代 ID（含自身）。"""
        if not root_ids:
            return []
        cte = (
            select(Permission.id, Permission.parent_id)
            .where(Permission.id.in_(root_ids))
            .cte("descendants_batch", recursive=True)
        )
        cte = cte.union_all(
            select(Permission.id, Permission.parent_id)
            .where(Permission.parent_id == cte.c.id)
        )
        result = await self.session.execute(select(cte.c.id))
        return [row[0] for row in result.all()]


# ─────────────────────────────────────────────────────
# RoleRepository — 角色数据访问
# ─────────────────────────────────────────────────────

class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_by_app(self, app_code: str) -> list[Role]:
        """拉取指定 App 下全部角色（含 synced_at 标记）。"""
        result = await self.session.execute(
            select(Role).where(Role.app_code == app_code).order_by(Role.id.asc())
        )
        return list(result.scalars().all())

    async def batch_create(self, items: list[dict]) -> list[Role]:
        """批量插入角色，返回已插入对象列表。"""
        roles = [Role(**data) for data in items]
        self.session.add_all(roles)
        await self.session.flush()
        return roles

    async def batch_soft_delete(self, ids: list[int]) -> int:
        """批量软下线角色（删除记录），返回受影响行数。"""
        if not ids:
            return 0
        result = await self.session.execute(
            delete(Role).where(Role.id.in_(ids))
        )
        await self.session.flush()
        return result.rowcount  # type: ignore[return-value]

    async def replace_role_permissions(self, role_id: int, permission_ids: list[int]) -> None:
        """全量替换角色的权限绑定。"""
        await self.session.execute(
            delete(role_permissions).where(role_permissions.c.role_id == role_id)
        )
        if permission_ids:
            await self.session.execute(
                role_permissions.insert(),
                [{"role_id": role_id, "permission_id": pid} for pid in permission_ids],
            )
        await self.session.flush()

    async def get_role_permission_ids(self, role_id: int) -> list[int]:
        """获取角色已绑定的权限 ID 列表。"""
        result = await self.session.execute(
            select(role_permissions.c.permission_id).where(role_permissions.c.role_id == role_id)
        )
        return [row[0] for row in result.all()]
