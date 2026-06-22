# domains/identity/router.py — Identity HTTP endpoints
from fastapi import APIRouter, Path, status

from common.responses import success
from domains.auth.dependencies import CurrentUserDep
from domains.identity.dependencies import AppCodeDep, IdentityServiceDep
from domains.identity.schemas import MenuCreate, MenuUpdate

router = APIRouter()


# ─────────────────────────────────────────────────────────
# 权限获取 — 外部系统公共入口
# ─────────────────────────────────────────────────────────
@router.get(
    "/roles",
    summary="获取当前用户角色列表",
    description="返回用户在指定 App 下的角色编码列表。适合 role_only 模式、仅需角色分流的轻量级系统。",
)
async def get_my_roles(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: AppCodeDep,
):
    role_codes = await service.get_user_role_codes(user_id=current_user.id, app_code=app_code)
    return success(data=role_codes)


@router.get(
    "/permissions",
    summary="获取当前用户权限元数据",
    description="返回用户在指定 App 下的完整权限数据: roles + menu_tree + permissions。适合 full 模式、需要完整 RBAC 数据的系统。",
)
async def get_my_permissions(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: AppCodeDep,
):
    roles = await service.get_user_role_codes(user_id=current_user.id, app_code=app_code)
    tree = await service.get_user_menu_tree(user_id=current_user.id, app_code=app_code)
    return success(data={"roles": roles, **tree})


# ─────────────────────────────────────────────────────────
# 菜单管理 CRUD（管理员接口）
# ─────────────────────────────────────────────────────────
@router.get("/menus", summary="获取菜单列表（扁平）")
async def list_menus(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: AppCodeDep,
):
    """[管理员] 返回指定 App 的扁平化菜单列表，供管理后台树形展示。"""
    items = await service.get_menu_list_flat(app_code=app_code)
    return success(data=items)


@router.post("/menus", status_code=status.HTTP_201_CREATED, summary="新增菜单/按鈕")
async def create_menu(
    data: MenuCreate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
):
    await service.create_menu(data)
    return success(message="创建成功")


@router.put("/menus/{menu_id}", summary="更新菜单内容")
async def update_menu(
    data: MenuUpdate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    menu_id: int = Path(...),
):
    await service.update_menu(menu_id, data)
    return success(message="更新成功")


@router.delete("/menus/{menu_id}", summary="删除菜单")
async def delete_menu(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    menu_id: int = Path(...),
):
    await service.delete_menu(menu_id)
    return success(message="删除成功")
