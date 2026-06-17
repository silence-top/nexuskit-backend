# domains/identity/schemas.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MenuBase(BaseModel):
    title: str = Field(..., description="菜单标题")
    icon: str | None = Field(None, description="菜单图标")
    path: str | None = Field(None, description="前端路由路径")
    component: str | None = Field(None, description="前端组件路径")
    is_frame: bool = Field(False, description="是否外链")
    is_cache: bool = Field(True, description="是否缓存")
    menu_type: str = Field(..., description="菜单类型 (M:目录, C:菜单, F:按钮)")
    visible: bool = Field(True, description="菜单是否可见")
    status: bool = Field(True, description="菜单状态 (正常/停用)")
    perms: str | None = Field(None, description="权限标识")
    parent_id: int | None = Field(None, description="父菜单ID")
    order_num: int = Field(0, description="显示顺序")
    remark: str | None = Field(None, description="备注")
    app_code: str = Field("platform", description="所属应用编码")


class MenuCreate(MenuBase):
    pass


class MenuUpdate(MenuBase):
    pass


class MenuInDB(MenuBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
