# domains/identity/schemas.py
from pydantic import BaseModel, ConfigDict, Field


class MenuCreate(BaseModel):
    """创建菜单/按鈕/目录节点。字段名与 Permission 模型一一对应。"""
    app_code: str                = Field(..., description="所属应用编码")
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
