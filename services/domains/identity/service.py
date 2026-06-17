# domains/identity/service.py — Identity business logic
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from domains.auth.schemas import RoleBrief
from domains.identity.exceptions import MenuHasChildrenError, MenuNotFoundError
from domains.identity.models import Permission, Role, role_permissions, user_roles
from domains.identity.repository import PermissionRepository
from domains.identity.schemas import MenuCreate, MenuUpdate


class IdentityService:
    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.db = db
        self.redis = redis
        self._perm_repo = PermissionRepository(db)

    # --- Cross-domain: provide roles for Auth domain ---

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

    # --- User identity meta ---

    async def get_user_identity_meta(self, user_id: int, app_code: str) -> dict[str, Any]:
        """Core method: fetch menu tree + global button permission codes in one pass."""
        stmt = (
            select(Permission)
            .distinct()
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(
                and_(user_roles.c.user_id == user_id, Permission.app_code == app_code, Permission.is_active.is_(True))
            )
            .order_by(Permission.sort.asc())
        )

        result = await self.db.execute(stmt)
        all_perms = result.scalars().all()

        menu_dict = {}
        permissions_codes = []

        for p in all_perms:
            if p.code:
                permissions_codes.append(p.code)
            if p.type in ["M", "C"]:
                menu_dict[p.id] = {
                    "id": p.id,
                    "parent_id": p.parent_id,
                    "name": p.name,
                    "path": p.path,
                    "component": p.component,
                    "meta": {"title": p.name, "icon": p.icon, "order": p.sort, "type": p.type, "keepAlive": True},
                    "children": [],
                }

        menu_tree = []
        for p in all_perms:
            if p.id in menu_dict:
                node = menu_dict[p.id]
                if p.parent_id and p.parent_id in menu_dict:
                    menu_dict[p.parent_id]["children"].append(node)
                else:
                    menu_tree.append(node)

        return {
            "menu_tree": menu_tree,
            "permissions": list(set(permissions_codes)),
        }

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
        perm = await self._perm_repo.create(data.model_dump())
        await self.db.commit()
        await self.clear_app_cache_for_users(perm.app_code)

    async def update_menu(self, menu_id: int, data: MenuUpdate) -> None:
        menu = await self._perm_repo.get_by_id(menu_id)
        if not menu:
            raise MenuNotFoundError("菜单不存在")
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
