# domains/identity/models.py — Identity domain entities (Role, Permission, Department, App, association tables)
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.base import Base

# ---------------------------------------------------------------------------
# Association tables (owned by identity domain)
# ---------------------------------------------------------------------------

user_roles = Table(
    "auth_user_roles_link",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("auth_roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "auth_role_permissions_link",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("auth_roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("auth_permissions.id", ondelete="CASCADE"), primary_key=True),
)


# ---------------------------------------------------------------------------
# App 管理模式枚举（展示管理后台哪些面板，不限制接口调用）
# ---------------------------------------------------------------------------

class AppPermMode:
    """应用权限管理模式。

    不限制子系统能调哪些接口，仅决定：
      1. 管理后台显示哪些管理面板
      2. bootstrap 接口的查询范围优化

    FULL      - 平台管理：角色 + 菜单节点 + 角色-菜单绑定
    ROLE_ONLY - 平台仅管角色分配，无菜单管理面板
    """
    FULL      = "full"       # 管理：角色 + 菜单
    ROLE_ONLY = "role_only"  # 管理：仅角色


# ---------------------------------------------------------------------------
# App — subsystem registration
# ---------------------------------------------------------------------------

class App(Base):
    __tablename__ = "auth_apps"

    app_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False, comment="app key")
    app_name: Mapped[str] = mapped_column(String(64), nullable=False)
    app_secret: Mapped[str] = mapped_column(String(64), nullable=False)
    perm_mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=AppPermMode.FULL,
        server_default=AppPermMode.FULL,
        comment="权限模式: full=完整RBAC | role_only=仅角色 | passthru=SSO直通"
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="系统描述")

    def __repr__(self):
        return f"<App(code={self.app_code}, name={self.app_name}, mode={self.perm_mode})>"


# ---------------------------------------------------------------------------
# Department — organizational hierarchy
# ---------------------------------------------------------------------------

class Department(Base):
    __tablename__ = "auth_departments"

    dept_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="dept name")
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("auth_departments.id"), nullable=True, comment="parent dept")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="sort order")
    leader: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="dept leader")
    phone: Mapped[str | None] = mapped_column(String(11), nullable=True, comment="phone")
    email: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="email")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="status")

    # Self-referential hierarchy
    parent: Mapped["Department"] = relationship("Department", remote_side="Department.id", back_populates="children")
    children: Mapped[list["Department"]] = relationship(
        "Department", back_populates="parent", cascade="all, delete-orphan", order_by="Department.sort",
    )

    # NOTE: users relationship removed for domain isolation.
    # Auth domain's User has dept_id as logical FK only.

    def __repr__(self):
        return f"<Department(name={self.dept_name}, leader={self.leader})>"


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------

class Role(Base):
    __tablename__ = "auth_roles"

    app_code: Mapped[str] = mapped_column(
        String(32), ForeignKey("auth_apps.app_code"), index=True, comment="app code"
    )
    role_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="role name")
    role_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="role code")

    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary=role_permissions, back_populates="roles",
    )

    def __repr__(self) -> str:
        return f"<Role(code={self.role_code}, name={self.role_name})>"


# ---------------------------------------------------------------------------
# Permission — menus & buttons (RBAC core)
# ---------------------------------------------------------------------------

class Permission(Base):
    __tablename__ = "auth_permissions"

    # 1. Ownership & hierarchy
    app_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="app key")
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("auth_permissions.id"), nullable=True, comment="parent id")

    # 2. Core identity
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False, comment="perm code")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="perm name")
    type: Mapped[str] = mapped_column(String(10), nullable=False, default="C", comment="M=dir, C=menu, F=btn, L=link")

    # 3. Web routing
    path: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="frontend route")
    component: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="frontend component")

    # 4. External link
    is_ext: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", comment="is external")
    ext_url: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="ext url")

    # 5. UI & sorting
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="icon")
    sort: Mapped[int] = mapped_column(Integer, default=0, server_default="0", comment="sort order")
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="visible")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="active")

    # 6. Extension
    props: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON props")

    # 7. Self-referential hierarchy
    parent: Mapped["Permission"] = relationship("Permission", remote_side="Permission.id", back_populates="children")
    children: Mapped[list["Permission"]] = relationship(
        "Permission", back_populates="parent", cascade="all, delete-orphan",
    )

    # 8. M2M with Role
    roles: Mapped[list["Role"]] = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self) -> str:
        return f"<Permission(code={self.code}, name={self.name}, app={self.app_code})>"
