# domains/identity/schemas.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Menu ────────────────────────────────────────────

class MenuCreate(BaseModel):
    """创建菜单/按鈕/目录节点。字段名与 Permission 模型一一对应。

    app_code 从 URL 路径参数自动注入，前端可不传此字段。
    """
    app_code: str | None         = Field(None, description="所属应用编码，由 URL 路径自动覆盖")
    parent_id: int | None        = Field(None, description="父节点 ID，None 表示根节点")
    code: str                    = Field(..., description="权限标识码，全局唯一 (sys:user:add)。菜单目录可用路径替代")
    name: str                    = Field(..., description="菜单/按鈕名称")
    type: str                    = Field(..., description="节点类型: M=目录 C=菜单 F=按鈕 L=外链")
    path: str | None             = Field(None, description="前端路由路径")
    component: str | None        = Field(None, description="前端组件路径")
    is_ext: bool                 = Field(False, description="是否外链")
    ext_url: str | None          = Field(None, description="外链地址")
    icon: str | None             = Field(None, description="菜单图标")
    sort: int                    = Field(0, description="排序权重，越小越靠前")
    is_visible: bool             = Field(True, description="是否在菜单中显示")
    is_active: bool              = Field(True, description="是否启用")


class MenuUpdate(BaseModel):
    """更新菜单节点，所有字段均可选（仅传需要修改的字段）。"""
    parent_id: int | None        = Field(None, description="父节点 ID")
    code: str | None             = Field(None, description="权限标识码")
    name: str | None             = Field(None, description="菜单/按鈕名称")
    type: str | None             = Field(None, description="节点类型: M=目录 C=菜单 F=按鈕 L=外链")
    path: str | None             = Field(None, description="前端路由路径")
    component: str | None        = Field(None, description="前端组件路径")
    is_ext: bool | None          = Field(None, description="是否外链")
    ext_url: str | None          = Field(None, description="外链地址")
    icon: str | None             = Field(None, description="菜单图标")
    sort: int | None             = Field(None, description="排序权重")
    is_visible: bool | None      = Field(None, description="是否在菜单中显示")
    is_active: bool | None       = Field(None, description="是否启用")


class MenuOut(BaseModel):
    """菜单节点输出（管理员列表接口用）。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_code: str
    parent_id: int | None
    code: str
    name: str
    type: str
    path: str | None
    component: str | None
    is_ext: bool
    ext_url: str | None
    icon: str | None
    sort: int
    is_visible: bool
    is_active: bool


# ── App ────────────────────────────────────────────

class AppCreate(BaseModel):
    app_code: str        = Field(..., description="应用唯一标识码，下划线小写 (nexuskit / erp)", pattern=r"^[a-z0-9_]+$")
    app_name: str        = Field(..., description="应用显示名称")
    perm_mode: str       = Field("full", description="权限管理模式: full=完整RBAC | role_only=仅角色")
    description: str | None = Field(None, description="系统描述")
    # app_secret 由后端自动生成，不在此传入


class AppUpdate(BaseModel):
    app_name: str | None    = Field(None, description="应用显示名称")
    perm_mode: str | None   = Field(None, description="权限管理模式")
    description: str | None = Field(None, description="系统描述")
    # app_secret 不允许直接修改，应使用专用的「重置密鑰」接口


class AppOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_code: str
    app_name: str
    perm_mode: str
    description: str | None
    # app_secret 不在列表接口返回，只在创建/重置密鑰时单次返回


class AppSecretOut(BaseModel):
    """创建应用或重置密鑰时返回（仅展示一次，后端不再明文展示）。"""
    app_code: str
    app_secret: str
    message: str = "请将密鑰安全保存，不会再次展示"


# ── Role ───────────────────────────────────────────

class RoleCreate(BaseModel):
    app_code: str   = Field(..., description="所属应用")
    role_name: str  = Field(..., description="角色显示名称")
    role_code: str  = Field(..., description="角色唯一编码，全局唯一 (nexuskit:admin)", pattern=r"^[a-z0-9_:]+$")


class RoleUpdate(BaseModel):
    role_name: str | None = Field(None, description="角色显示名称")
    role_code: str | None = Field(None, description="角色唯一编码")


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_code: str
    role_name: str
    role_code: str


class RolePermissionsAssign(BaseModel):
    """批量设置角色的权限节点（全量替换）。"""
    permission_ids: list[int] = Field(..., description="权限节点 ID 列表，会全量替换现有绑定")


# ── User-Role ─────────────────────────────────────

class UserRoleAssign(BaseModel):
    role_id: int = Field(..., description="要分配的角色 ID")


# ── Department ───────────────────────────────────────

class DepartmentCreate(BaseModel):
    dept_name: str           = Field(..., description="部门名称")
    parent_id: int | None    = Field(None, description="父部门 ID，None 表示根部门")
    sort: int                = Field(0, description="排序权重")
    leader: str | None       = Field(None, description="部门负责人")
    phone: str | None        = Field(None, description="联系电话")
    email: str | None        = Field(None, description="联系邮笱")
    is_active: bool          = Field(True, description="是否启用")


class DepartmentUpdate(BaseModel):
    dept_name: str | None    = Field(None, description="部门名称")
    parent_id: int | None    = Field(None, description="父部门 ID")
    sort: int | None         = Field(None, description="排序权重")
    leader: str | None       = Field(None, description="部门负责人")
    phone: str | None        = Field(None, description="联系电话")
    email: str | None        = Field(None, description="联系邮笱")
    is_active: bool | None   = Field(None, description="是否启用")


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dept_name: str
    parent_id: int | None
    sort: int
    leader: str | None
    phone: str | None
    email: str | None
    is_active: bool


# ── UserApp ─────────────────────────────────────────────

class UserAppGrant(BaseModel):
    """Grant a user access to an app."""
    app_code: str   = Field(..., description="应用编码")
    is_active: bool = Field(True, description="是否启用")
    expired_at: datetime | None = Field(None, description="过期时间，NULL=永久")


class UserAppUpdate(BaseModel):
    """Update an existing user-app binding."""
    is_active: bool | None     = Field(None, description="是否启用")
    expired_at: datetime | None = Field(None, description="过期时间")


class UserAppOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    app_code: str
    is_active: bool
    expired_at: datetime | None
    created_at: datetime


# ── User （迁入自 Auth 域）───────────────────────────────

class UserAdminCreate(BaseModel):
    """[管理员] 新建用户，可指定部门和初始状态。"""
    username: str        = Field(..., min_length=3, max_length=20)
    email: EmailStr
    phone: str | None    = Field(None, max_length=20)
    password: str        = Field(..., min_length=6)
    dept_id: int | None  = None
    is_active: bool      = True


class UserAdminUpdate(BaseModel):
    """[管理员] 可更新的用户属性，启用/禁用也包含在内。"""
    email: EmailStr | None  = None
    phone: str | None       = None
    dept_id: int | None     = None
    is_active: bool | None  = None


class PasswordReset(BaseModel):
    """[管理员] 强制重置用户密码。"""
    new_password: str = Field(..., min_length=6)


class UserOut(BaseModel):
    """[管理员] 用户详情输出。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    phone: str | None
    is_active: bool
    is_mfa_enabled: bool
    dept_id: int | None
