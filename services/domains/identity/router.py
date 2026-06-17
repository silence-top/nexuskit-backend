# domains/identity/router.py — Identity HTTP endpoints
from fastapi import APIRouter, Path, Query, status

from common.responses import success
from domains.auth.dependencies import CurrentUserDep
from domains.identity.dependencies import IdentityServiceDep
from domains.identity.schemas import MenuCreate, MenuUpdate

router = APIRouter()


@router.get("/menus", summary="获取当前用户菜单树")
async def get_my_menus(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: str = Query("platform"),
):
    menu_tree = await service.get_user_identity_meta(user_id=current_user.id, app_code=app_code)
    return success(data=menu_tree)


@router.post("/menus", status_code=status.HTTP_201_CREATED, summary="新增菜单/按钮")
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
