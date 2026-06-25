# domains/identity/service.py — Identity business logic
from datetime import datetime
import secrets
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_password_hash, revoke_all_user_tokens
from domains.auth.repository import UserRepository
from domains.auth.schemas import RoleBrief
from domains.identity.exceptions import (
    AppAccessForbiddenError,
    AppAlreadyExistsError, AppNotFoundError,
    DeptHasChildrenError, DeptNotFoundError,
    MenuHasChildrenError, MenuNotFoundError,
    RoleAlreadyExistsError, RoleHasUsersError, RoleNotFoundError,
)
from domains.identity.models import App, AppPermMode, Department, Permission, Role, UserApp, role_permissions, user_roles
from domains.identity.repository import PermissionRepository
from domains.identity.schemas import AppCreate, AppUpdate, DepartmentCreate, DepartmentUpdate, MenuCreate, MenuUpdate, PasswordReset, RoleCreate, RolePermissionsAssign, RoleUpdate, UserAdminCreate, UserAdminUpdate, UserAppGrant, UserAppUpdate


class IdentityService:
    def __init__(self, db: AsyncSession, redis: Redis | None = None, user_repo: UserRepository | None = None):
        self.db = db
        self.redis = redis
        self._perm_repo = PermissionRepository(db)
        self._user_repo = user_repo

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

    SUPER_ADMIN_ROLE_CODE = "super_admin"

    # ── 阶梯 C：完备动态路由菜单树（重量级）───────────────────

    _MENU_TREE_CACHE_TTL = 300  # 菜单树缓存 5 分钟

    async def get_user_menu_tree(self, user_id: int, app_code: str) -> dict[str, Any]:
        """阶梯 C：返回用户在指定 App 下的完备动态路由菜单树。

        适用：需要动态渲染左侧菜单的完整后台系统（如 Pure Admin）。
        交付：
          menu_tree - 嵌套 JSON 菜单树（M=目录, C=菜单, L=外链）
          buttons   - 按钮级权限编码列表（F=按钮）

        优化策略：
          1. 单次 SQL 拉取全部权限（O(1) DB roundtrip）
          2. 内存 O(n) 组建树（dict 索引 + 单次遍历）
          3. Redis 缓存结果（TTL 5min），写操作时主动失效

        super_admin 角色直通：跳过权限过滤，返回该 App 全量菜单与按钮。
        """
        # ── Redis 缓存命中检测 ──
        import json as _json
        cache_key = f"menu_tree:{user_id}:{app_code}"
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                return _json.loads(cached)

        role_codes = await self.get_user_role_codes(user_id, app_code)
        is_super_admin = self.SUPER_ADMIN_ROLE_CODE in role_codes

        if is_super_admin:
            stmt = (
                select(Permission)
                .where(and_(Permission.app_code == app_code, Permission.is_active.is_(True)))
                .order_by(Permission.sort.asc())
            )
        else:
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

        tree_data = self._build_menu_tree(all_perms)

        # ── 写入 Redis 缓存 ──
        if self.redis:
            await self.redis.setex(cache_key, self._MENU_TREE_CACHE_TTL, _json.dumps(tree_data, ensure_ascii=False))

        return tree_data

    @staticmethod
    def _build_menu_tree(all_perms: list) -> dict[str, Any]:
        """O(n) 单次遍历构建嵌套菜单树 + 按钮权限列表。

        算法：
          1. 第一遍：构建 menu_dict（id → node），分离按钮权限
          2. 第二遍：根据 parent_id 挂接子节点或归入 roots
        """
        menu_dict: dict[int, dict] = {}
        perm_codes: list[str] = []

        for p in all_perms:
            if p.type == "F":
                if p.code:
                    perm_codes.append(p.code)
            elif p.type in ("M", "C", "L"):
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

        # 第二遍：挂接父子关系
        roots: list[dict] = []
        for node_id, node in menu_dict.items():
            parent_id = node["parent_id"]
            if parent_id and parent_id in menu_dict:
                menu_dict[parent_id]["children"].append(node)
            else:
                roots.append(node)

        return {"menu_tree": roots, "buttons": list(set(perm_codes))}

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
            # 同时失效菜单树缓存
            keys += [f"menu_tree:{uid}:{app_code}" for uid in user_ids]
            await self.redis.delete(*keys)

    async def get_menu_list_flat(self, app_code: str) -> list[dict[str, Any]]:
        """Flat menu list for admin management UI."""
        permissions = await self._perm_repo.get_all_by_app(app_code)
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

    async def get_menu_tree_for_admin(self, app_code: str) -> dict[str, Any]:
        """[管理员] 返回指定 App 的全量菜单树（含未激活节点），用于管理后台树形展示。

        与 get_user_menu_tree 的区别：
          - 不过滤 is_active，展示全部节点
          - 不按用户权限过滤
          - 不写缓存
        """
        permissions = await self._perm_repo.get_all_by_app(app_code)
        return self._build_menu_tree(permissions)

    async def validate_menu_relation(self, menu_id: int, parent_id: int | None) -> bool:
        """防止循环引用（递归 CTE 深层检测）。

        校验逻辑：
          1. parent_id 为 None → 根节点，合法
          2. menu_id == parent_id → 自引用，非法
          3. parent_id 存在于 menu_id 的后代链中 → 形成环，非法
        """
        if not parent_id:
            return True
        if menu_id == parent_id:
            return False
        # 递归 CTE：检查 parent_id 是否在当前节点的后代中
        descendant_ids = await self._perm_repo.get_descendant_ids(menu_id)
        return parent_id not in descendant_ids

    # --- Menu CRUD ---

    async def create_menu(self, data: MenuCreate) -> None:
        if not data.app_code:
            raise MenuNotFoundError("app_code 必填")
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
        # 递归 CTE 检查是否存在后代节点
        if await self._perm_repo.has_descendants(menu_id):
            raise MenuHasChildrenError("请先删除子菜单或按鈕")
        menu = await self._perm_repo.get_by_id(menu_id)
        app_code = menu.app_code if menu else None
        await self._perm_repo.delete(menu_id)
        await self.db.commit()
        if app_code:
            await self.clear_app_cache_for_users(app_code)
    
    # ─────────────────────────────────────────────────────────
    # App 管理
    # ─────────────────────────────────────────────────────────
    
    async def list_apps(self) -> list[App]:
        result = await self.db.execute(select(App).order_by(App.id.asc()))
        return list(result.scalars().all())
    
    async def create_app(self, data: AppCreate) -> App:
        existing = await self.get_app(data.app_code)
        if existing:
            raise AppAlreadyExistsError(f"应用 '{data.app_code}' 已存在")
        # app_secret 后端自动生成，返回给调用方一次
        raw_secret = secrets.token_urlsafe(32)
        app = App(**data.model_dump(), app_secret=raw_secret)
        self.db.add(app)
        await self.db.commit()
        await self.db.refresh(app)
        # 临时将明文 secret 挂在对象上供 router 层取用（不入库）
        app._plain_secret = raw_secret
        return app

    async def reset_app_secret(self, app_code: str) -> tuple[App, str]:
        """重置应用密鑰，返回 (app, 新密鑰明文)。调用方展示一次后屏弃。"""
        app = await self.get_app(app_code)
        if not app:
            raise AppNotFoundError(f"应用 '{app_code}' 不存在")
        raw_secret = secrets.token_urlsafe(32)
        app.app_secret = raw_secret
        await self.db.commit()
        return app, raw_secret
    
    async def update_app(self, app_code: str, data: AppUpdate) -> App:
        app = await self.get_app(app_code)
        if not app:
            raise AppNotFoundError(f"应用 '{app_code}' 不存在")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(app, k, v)
        await self.db.commit()
        await self.db.refresh(app)
        return app
    
    async def delete_app(self, app_code: str) -> None:
        app = await self.get_app(app_code)
        if not app:
            raise AppNotFoundError(f"应用 '{app_code}' 不存在")
        await self.db.delete(app)
        await self.db.commit()
    
    # ─────────────────────────────────────────────────────────
    # 角色管理
    # ─────────────────────────────────────────────────────────
    
    async def list_roles(self, app_code: str) -> list[Role]:
        result = await self.db.execute(
            select(Role).where(Role.app_code == app_code).order_by(Role.id.asc())
        )
        return list(result.scalars().all())
    
    async def create_role(self, data: RoleCreate) -> Role:
        existing = await self.db.execute(select(Role).where(Role.role_code == data.role_code))
        if existing.scalar_one_or_none():
            raise RoleAlreadyExistsError(f"角色编码 '{data.role_code}' 已存在")
        role = Role(**data.model_dump())
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def update_role(self, role_id: int, data: RoleUpdate) -> Role:
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise RoleNotFoundError("角色不存在")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(role, k, v)
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def delete_role(self, role_id: int) -> None:
        # 检查是否有用户使用该角色
        user_count = await self.db.execute(
            select(user_roles.c.user_id).where(user_roles.c.role_id == role_id).limit(1)
        )
        if user_count.scalar_one_or_none() is not None:
            raise RoleHasUsersError("角色下还有用户，请先移除用户后再删除")
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise RoleNotFoundError("角色不存在")
        await self.db.delete(role)
        await self.db.commit()
    
    # ─────────────────────────────────────────────────────────
    # 角色 ↔ 权限节点绑定
    # ─────────────────────────────────────────────────────────
    
    async def get_role_permissions(self, role_id: int) -> list[Permission]:
        """Get all permission nodes bound to a role."""
        result = await self.db.execute(
            select(Permission)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .where(role_permissions.c.role_id == role_id)
            .order_by(Permission.sort.asc())
        )
        return list(result.scalars().all())
    
    async def assign_role_permissions(self, role_id: int, data: RolePermissionsAssign) -> None:
        """Batch-replace all permissions for a role (full replace)."""
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise RoleNotFoundError("角色不存在")
        # 全量替换：删旧插新
        await self.db.execute(delete(role_permissions).where(role_permissions.c.role_id == role_id))
        if data.permission_ids:
            await self.db.execute(
                role_permissions.insert(),
                [{"role_id": role_id, "permission_id": pid} for pid in data.permission_ids],
            )
        await self.db.commit()
        # 刷新该角色对应用户的缓存
        user_ids_result = await self.db.execute(
            select(user_roles.c.user_id).where(user_roles.c.role_id == role_id)
        )
        user_ids = user_ids_result.scalars().all()
        if user_ids and self.redis:
            keys = [f"auth:perms:{uid}" for uid in user_ids]
            await self.redis.delete(*keys)
    
    # ─────────────────────────────────────────────────────────
    # 用户 ↔ 角色分配
    # ─────────────────────────────────────────────────────────
    
    async def list_user_roles(self, user_id: int, app_code: str | None = None) -> list[Role]:
        """List all roles of a user, optionally filtered by app_code."""
        stmt = select(Role).join(user_roles, Role.id == user_roles.c.role_id).where(
            user_roles.c.user_id == user_id
        )
        if app_code:
            stmt = stmt.where(Role.app_code == app_code)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def assign_role_to_user(self, user_id: int, role_id: int) -> None:
        """Assign a role to a user (idempotent)."""
        role_result = await self.db.execute(select(Role).where(Role.id == role_id))
        if not role_result.scalar_one_or_none():
            raise RoleNotFoundError("角色不存在")
        # 幂等就论：已有则跳过
        existing = await self.db.execute(
            select(user_roles).where(
                and_(user_roles.c.user_id == user_id, user_roles.c.role_id == role_id)
            )
        )
        if existing.first() is None:
            await self.db.execute(user_roles.insert().values(user_id=user_id, role_id=role_id))
            await self.db.commit()
            await self.cache_user_permissions(user_id)
    
    async def revoke_role_from_user(self, user_id: int, role_id: int) -> None:
        """Revoke a role from a user."""
        await self.db.execute(
            delete(user_roles).where(
                and_(user_roles.c.user_id == user_id, user_roles.c.role_id == role_id)
            )
        )
        await self.db.commit()
        await self.cache_user_permissions(user_id)

    # ─────────────────────────────────────────────────────────
    # 部门管理
    # ─────────────────────────────────────────────────────────

    async def list_departments(self) -> list[Department]:
        """Return all departments ordered by sort."""
        result = await self.db.execute(select(Department).order_by(Department.sort.asc(), Department.id.asc()))
        return list(result.scalars().all())

    async def get_department(self, dept_id: int) -> Department | None:
        return await self.db.get(Department, dept_id)

    async def create_department(self, data: DepartmentCreate) -> Department:
        dept = Department(**data.model_dump())
        self.db.add(dept)
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def update_department(self, dept_id: int, data: DepartmentUpdate) -> Department:
        dept = await self.get_department(dept_id)
        if not dept:
            raise DeptNotFoundError("部门不存在")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(dept, k, v)
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def delete_department(self, dept_id: int) -> None:
        dept = await self.get_department(dept_id)
        if not dept:
            raise DeptNotFoundError("部门不存在")
        if dept.children:
            raise DeptHasChildrenError("请先删除子部门")
        await self.db.delete(dept)
        await self.db.commit()

    # ─────────────────────────────────────────────────────────
    # 用户 ↔ 应用访问授权（强校验）
    # ─────────────────────────────────────────────────────────

    async def check_user_app_access(self, user_id: int, app_code: str) -> None:
        """强校验：用户是否具备访问该 App 的权限。

        校验顺序：
          1. 无记录 → 403 APP_FORBIDDEN
          2. is_active = False → 403 APP_FORBIDDEN
          3. expired_at 不为空且已过期 → 403 APP_FORBIDDEN
        """
        from datetime import timezone
        result = await self.db.execute(
            select(UserApp).where(
                and_(UserApp.user_id == user_id, UserApp.app_code == app_code)
            )
        )
        binding = result.scalar_one_or_none()

        if not binding:
            raise AppAccessForbiddenError(f"用户未被授权访问应用 '{app_code}'")
        if not binding.is_active:
            raise AppAccessForbiddenError(f"用户对应用 '{app_code}' 的访问权限已禁用")
        if binding.expired_at and binding.expired_at < datetime.now(tz=timezone.utc):
            raise AppAccessForbiddenError(f"用户对应用 '{app_code}' 的访问权限已过期")

    async def list_user_app_grants(self, user_id: int) -> list[UserApp]:
        """List all app bindings for a user."""
        result = await self.db.execute(
            select(UserApp).where(UserApp.user_id == user_id).order_by(UserApp.app_code.asc())
        )
        return list(result.scalars().all())

    async def grant_user_app_access(self, user_id: int, data: UserAppGrant) -> UserApp:
        """Grant / update user access to an app (upsert)."""
        # 确认 app 存在
        if not await self.get_app(data.app_code):
            raise AppNotFoundError(f"应用 '{data.app_code}' 不存在")
        # Upsert
        result = await self.db.execute(
            select(UserApp).where(
                and_(UserApp.user_id == user_id, UserApp.app_code == data.app_code)
            )
        )
        binding = result.scalar_one_or_none()
        if binding:
            binding.is_active = data.is_active
            binding.expired_at = data.expired_at
        else:
            binding = UserApp(
                user_id=user_id,
                app_code=data.app_code,
                is_active=data.is_active,
                expired_at=data.expired_at,
            )
            self.db.add(binding)
        await self.db.commit()
        await self.db.refresh(binding)
        return binding

    async def update_user_app_access(self, user_id: int, app_code: str, data: UserAppUpdate) -> UserApp:
        """Update is_active / expired_at of an existing binding."""
        result = await self.db.execute(
            select(UserApp).where(
                and_(UserApp.user_id == user_id, UserApp.app_code == app_code)
            )
        )
        binding = result.scalar_one_or_none()
        if not binding:
            raise AppNotFoundError("用户尚未授权该应用")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(binding, k, v)
        await self.db.commit()
        await self.db.refresh(binding)
        return binding

    async def revoke_user_app_access(self, user_id: int, app_code: str) -> None:
        """Revoke user's access to an app."""
        await self.db.execute(
            delete(UserApp).where(
                and_(UserApp.user_id == user_id, UserApp.app_code == app_code)
            )
        )
        await self.db.commit()

    # ─────────────────────────────────────────────────────────
    # 用户管理（迁自 Auth 域）
    # ─────────────────────────────────────────────────────────

    def _require_user_repo(self):
        if not self._user_repo:
            raise RuntimeError("UserRepository not injected into IdentityService")
        return self._user_repo

    async def list_users(
        self,
        keyword: str | None = None,
        is_active: bool | None = None,
        dept_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        repo = self._require_user_repo()
        from domains.auth.schemas import UserRead
        users, total = await repo.list_users(keyword, is_active, dept_id, page, page_size)
        return {
            "items": [UserRead.model_validate(u) for u in users],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def admin_create_user(self, data: UserAdminCreate):
        repo = self._require_user_repo()
        from domains.auth.exceptions import UserAlreadyExistsError
        from domains.auth.schemas import UserRead
        if await repo.get_by_email(data.email):
            raise UserAlreadyExistsError("邮笱已存在")
        if await repo.get_by_username(data.username):
            raise UserAlreadyExistsError("用户名已存在")
        user = await repo.create(
            username=data.username,
            email=data.email,
            hashed_password=get_password_hash(data.password),
            phone=data.phone,
            dept_id=data.dept_id,
            is_active=data.is_active,
        )
        await repo.session.commit()
        await repo.session.refresh(user)
        return UserRead.model_validate(user)

    async def get_user_by_id(self, user_id: int):
        repo = self._require_user_repo()
        from domains.auth.exceptions import UserNotFoundError
        from domains.auth.schemas import UserRead
        user = await repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("用户不存在")
        return UserRead.model_validate(user)

    async def admin_update_user(self, user_id: int, data: UserAdminUpdate):
        repo = self._require_user_repo()
        from domains.auth.exceptions import UserNotFoundError
        from domains.auth.schemas import UserRead
        user = await repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("用户不存在")
        fields = data.model_dump(exclude_unset=True)
        if not fields:
            return UserRead.model_validate(user)
        await repo.update(user, **fields)
        # 禁用时强制下线
        if fields.get("is_active") is False and self.redis:
            await revoke_all_user_tokens(user_id, self.redis)
        await repo.session.commit()
        await repo.session.refresh(user)
        return UserRead.model_validate(user)

    async def admin_delete_user(self, user_id: int) -> None:
        repo = self._require_user_repo()
        from domains.auth.exceptions import UserNotFoundError
        user = await repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("用户不存在")
        if self.redis:
            await revoke_all_user_tokens(user_id, self.redis)
        await repo.delete(user)
        await repo.session.commit()

    async def admin_reset_password(self, user_id: int, data: PasswordReset) -> None:
        repo = self._require_user_repo()
        from domains.auth.exceptions import UserNotFoundError
        user = await repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("用户不存在")
        await repo.update(user,
            hashed_password=get_password_hash(data.new_password),
            version=user.version + 1,
        )
        await repo.session.commit()
        if self.redis:
            await revoke_all_user_tokens(user_id, self.redis)

    async def revoke_user_sessions(self, user_id: int) -> None:
        """[Admin] DELETE /users/{id}/sessions — 强制下线。"""
        if self.redis:
            await revoke_all_user_tokens(user_id, self.redis)