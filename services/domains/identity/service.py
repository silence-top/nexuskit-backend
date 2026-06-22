# domains/identity/service.py — Identity business logic
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from domains.auth.schemas import RoleBrief
from domains.identity.exceptions import MenuHasChildrenError, MenuNotFoundError
from domains.identity.models import App, AppPermMode, Permission, Role, role_permissions, user_roles
from domains.identity.repository import PermissionRepository
from domains.identity.schemas import MenuCreate, MenuUpdate


class IdentityService:
    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.db = db
        self.redis = redis
        self._perm_repo = PermissionRepository(db)

    # --- Cross-domain: provide roles for Auth domain ---

    async def get_app(self, app_code: str) -> App | None:
        """Get App entity by app_code."""
        result = await self.db.execute(
            select(App).where(App.app_code == app_code)
        )
        return result.scalar_one_or_none()

    async def get_user_roles_for_app(self, user_id: int, app_code: str) -> list[RoleBrief]:
        """Return roles for a user filtered by app_code. Called by AuthService."""
        stmt = (
            select(Role)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(and_(user_roles.c.user_id == user_id, Role.app_code == app_code))
        )
        result = await self.db.execute(stmt)
        roles = result.scalars().all()
        return [
            RoleBrief(id=r.id, role_name=r.role_name, role_code=r.role_code)
            for r in roles
        ]

    # ── 阶梯 A：纯角色编码列表（最轻量级）──────────────────────────

    async def get_user_role_codes(self, user_id: int, app_code: str) -> list[str]:
        """阿梯 A：返回用户在指定 App 下的角色编码列表。

        适用：简单 H5、轻量看板、仅需山粒度角色分流的系统。
        交付：["admin", "store_manager"]
        """
        roles = await self.get_user_roles_for_app(user_id, app_code)
        return [r.role_code for r in roles]

    # ── 阶梯 B：扁平化按钮/接口权限标识（中量级）─────────────────

    async def get_user_permission_codes(self, user_id: int, app_code: str) -> list[str]:
        """阶梯 B：返回用户在指定 App 下的按钮/接口级权限标识列表。

        适用：页面菜单写死但有按鈕控权需求、后端接口需要精确拦截的系统。
        交付：["sys:user:export", "sys:order:refund"]
        业务规则：仅返回 type="F"（按鈕/功能）类型的权限编码。
        """
        stmt = (
            select(Permission.code)
            .distinct()
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(
                and_(
                    user_roles.c.user_id == user_id,
                    Permission.app_code == app_code,
                    Permission.type == "F",  # 仅限按鈕/接口级权限
                    Permission.is_active.is_(True),
                    Permission.code.is_not(None),
                )
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ── 阶梯 C：完备动态路由菜单树（重量级）───────────────────

    async def get_user_menu_tree(self, user_id: int, app_code: str) -> dict[str, Any]:
        """阶梯 C：返回用户在指定 App 下的完备动态路由菜单树。

        适用：需要动态渲染左侧菜单的完整后台系统（如 Pure Admin）。
        交付：
          menu_tree   - 嵌套 JSON 菜单树（M=目录, C=菜单, L=外链）
          permissions - 按钮级权限编码列表（F=按鈕）
        """
        stmt = (
            select(Permission)
            .distinct()
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(
                and_(
                    user_roles.c.user_id == user_id,
                    Permission.app_code == app_code,
                    Permission.is_active.is_(True),
                )
            )
            .order_by(Permission.sort.asc())
        )
        result = await self.db.execute(stmt)
        all_perms = result.scalars().all()

        menu_dict: dict[int, dict] = {}
        perm_codes: list[str] = []

        for p in all_perms:
            if p.type == "F":
                # 按鈕/接口权限 → 加入权限编码列表
                if p.code:
                    perm_codes.append(p.code)
            elif p.type in ("M", "C", "L"):
                # 目录/菜单/外链 → 加入菜单树
                menu_dict[p.id] = {
                    "id": p.id,
                    "parent_id": p.parent_id,
                    "name": p.name,
                    "path": p.path,
                    "component": p.component,
                    "is_ext": p.is_ext,
                    "ext_url": p.ext_url,
                    "meta": {
                        "title": p.name,
                        "icon": p.icon,
                        "order": p.sort,
                        "type": p.type,
                        "keepAlive": True,
                    },
                    "children": [],
                }

        # 组装嵌套树
        roots: list[dict] = []
        for p in all_perms:
            if p.id not in menu_dict:
                continue
            node = menu_dict[p.id]
            if p.parent_id and p.parent_id in menu_dict:
                menu_dict[p.parent_id]["children"].append(node)
            else:
                roots.append(node)

        return {"menu_tree": roots, "buttons": list(set(perm_codes))}

    # ── 上层聊天模式：自动根据 App 的 perm_mode 分发到对应阶梯────────

    async def get_user_identity_meta(self, user_id: int, app_code: str) -> dict[str, Any]:
        """[已废弃] 便利方法，router 层已直接调用具体阶梯方法，此方法保留仅供内部测试用。"""
        roles = await self.get_user_role_codes(user_id, app_code)
        tree = await self.get_user_menu_tree(user_id, app_code)
        return {"roles": roles, **tree}

    async def cache_user_permissions(self, user_id: int) -> list[str]:
        """Sync permissions to Redis for gateway fast auth."""
        stmt = (
            select(Permission.code)
            .distinct()
            .join(role_permissions)
            .join(user_roles)
            .where(and_(user_roles.c.user_id == user_id, Permission.is_active.is_(True), Permission.code.is_not(None)))
        )
        result = await self.db.execute(stmt)
        perms = [row for row in result.scalars().all()]

        if self.redis:
            cache_key = f"auth:perms:{user_id}"
            async with self.redis.pipeline(transaction=True) as pipe:
                await pipe.delete(cache_key)
                if perms:
                    await pipe.sadd(cache_key, *perms)
                    await pipe.expire(cache_key, 86400)
                await pipe.execute()
        return perms

    async def init_user_default_roles(self, user_id: int, role_codes: list[str] | None = None):
        """Assign default roles to a newly registered user."""
        if role_codes is None:
            role_codes = ["default_user"]

        role_stmt = select(Role).where(Role.role_code.in_(role_codes))
        roles_res = await self.db.execute(role_stmt)
        roles = roles_res.scalars().all()

        if roles:
            # Insert directly into user_roles association table (no ORM relationship needed)
            for role in roles:
                await self.db.execute(
                    user_roles.insert().values(user_id=user_id, role_id=role.id)
                )
            await self.db.flush()
            await self.cache_user_permissions(user_id)

    async def clear_app_cache_for_users(self, app_code: str):
        """Clear Redis cache for all users who have permissions in this app."""
        if not self.redis:
            return

        stmt = (
            select(user_roles.c.user_id)
            .distinct()
            .join(Role, Role.id == user_roles.c.role_id)
            .join(role_permissions, Role.id == role_permissions.c.role_id)
            .join(Permission, Permission.id == role_permissions.c.permission_id)
            .where(Permission.app_code == app_code)
        )
        result = await self.db.execute(stmt)
        user_ids = result.scalars().all()

        if user_ids:
            keys = [f"auth:perms:{uid}" for uid in user_ids]
            await self.redis.delete(*keys)

    async def get_menu_list_flat(self, app_code: str) -> list[dict[str, Any]]:
        """Flat menu list for admin management UI."""
        stmt = select(Permission).where(Permission.app_code == app_code).order_by(Permission.sort.asc())
        result = await self.db.execute(stmt)
        permissions = result.scalars().all()

        return [
            {
                "id": p.id,
                "parent_id": p.parent_id,
                "name": p.name,
                "code": p.code,
                "type": p.type,
                "path": p.path,
                "component": p.component,
                "sort": p.sort,
                "is_active": p.is_active,
            }
            for p in permissions
        ]

    async def validate_menu_relation(self, menu_id: int, parent_id: int | None) -> bool:
        """Prevent circular menu references."""
        if not parent_id:
            return True
        if menu_id == parent_id:
            return False

        parent_stmt = select(Permission).where(Permission.id == parent_id)
        parent_res = await self.db.execute(parent_stmt)
        return parent_res.scalar_one_or_none() is not None

    # --- Menu CRUD ---

    async def create_menu(self, data: MenuCreate) -> None:
        # 防循环引用校验
        dummy_id = -1  # 新建时还没有 id，用 -1 占位不会与任何已有 id 冲突
        if not await self.validate_menu_relation(dummy_id, data.parent_id):
            raise MenuNotFoundError("父菜单不存在")
        perm = await self._perm_repo.create(data.model_dump())
        await self.db.commit()
        await self.clear_app_cache_for_users(perm.app_code)

    async def update_menu(self, menu_id: int, data: MenuUpdate) -> None:
        menu = await self._perm_repo.get_by_id(menu_id)
        if not menu:
            raise MenuNotFoundError("菜单不存在")
        # 防循环引用校验
        new_parent = data.parent_id if data.parent_id is not None else menu.parent_id
        if not await self.validate_menu_relation(menu_id, new_parent):
            raise MenuNotFoundError("父菜单不存在或形成循环引用")
        app_code = menu.app_code
        await self._perm_repo.update(menu_id, data.model_dump(exclude_unset=True))
        await self.db.commit()
        await self.clear_app_cache_for_users(app_code)

    async def delete_menu(self, menu_id: int) -> None:
        children = await self._perm_repo.get_children(menu_id)
        if children:
            raise MenuHasChildrenError("请先删除子菜单或按钮")
        menu = await self._perm_repo.get_by_id(menu_id)
        app_code = menu.app_code if menu else None
        await self._perm_repo.delete(menu_id)
        await self.db.commit()
        if app_code:
            await self.clear_app_cache_for_users(app_code)
