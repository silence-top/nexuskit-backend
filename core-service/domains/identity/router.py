# domains/identity/router.py — Identity HTTP endpoints
from fastapi import APIRouter, HTTPException, Path, Query, status

from common.responses import success
from domains.auth.dependencies import CurrentUserDep
from domains.identity.dependencies import AppCodeDep, AppSecretDep, IdentityServiceDep
from domains.identity.schemas import (
    AppCreate, AppUpdate, AppSecretOut,
    DepartmentCreate, DepartmentUpdate,
    MenuCreate, MenuUpdate,
    PasswordReset, PermissionSyncRequest,
    RoleCreate, RolePermissionsAssign, RoleSyncRequest, RoleUpdate,
    UserAdminCreate, UserAdminUpdate,
    UserAppGrant, UserAppUpdate,
    UserRoleAssign,
)

router = APIRouter()


# ─────────────────────────────────────────────────────────
# 权限获取 — 外部系统公共入口
# ─────────────────────────────────────────────────────────
@router.get("/roles", summary="获取当前用户角色列表")
async def get_my_roles(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: AppCodeDep,
):
    """role_only 模式系统的入口：返回角色编码列表。"""
    await service.check_user_app_access(current_user.id, app_code)
    role_codes = await service.get_user_role_codes(user_id=current_user.id, app_code=app_code)
    return success(data=role_codes)


@router.get("/permissions", summary="获取当前用户权限元数据")
async def get_my_permissions(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: AppCodeDep,
):
    """full 模式系统的入口：返回 roles + menu_tree + buttons。"""
    await service.check_user_app_access(current_user.id, app_code)
    roles = await service.get_user_role_codes(user_id=current_user.id, app_code=app_code)
    tree = await service.get_user_menu_tree(user_id=current_user.id, app_code=app_code)
    return success(data={"roles": roles, **tree})


# ─────────────────────────────────────────────────────────
# 用户管理（管理员）
# ─────────────────────────────────────────────────────────
@router.get("/users", summary="用户列表")
async def list_users(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    keyword: str | None = Query(None, description="搜索用户名/邮箱"),
    is_active: bool | None = Query(None, description="状态过滤"),
    dept_id: int | None = Query(None, description="部门过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    result = await service.list_users(keyword, is_active, dept_id, page, page_size)
    result["items"] = [u.model_dump() for u in result["items"]]
    return success(data=result)


@router.post("/users", status_code=status.HTTP_201_CREATED, summary="新建用户")
async def admin_create_user(
    data: UserAdminCreate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
):
    user = await service.admin_create_user(data)
    return success(data=user.model_dump(), message="用户创建成功")


@router.get("/users/{user_id}", summary="用户详情")
async def get_user(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
):
    user = await service.get_user_by_id(user_id)
    return success(data=user.model_dump())


@router.put("/users/{user_id}", summary="更新用户信息")
async def update_user(
    data: UserAdminUpdate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
):
    user = await service.admin_update_user(user_id, data)
    return success(data=user.model_dump(), message="更新成功")


@router.delete("/users/{user_id}", summary="删除用户", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
):
    await service.admin_delete_user(user_id)


@router.put("/users/{user_id}/password", summary="重置用户密码")
async def reset_user_password(
    data: PasswordReset,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
):
    await service.admin_reset_password(user_id, data)
    return success(message="密码已重置")


@router.delete("/users/{user_id}/sessions", summary="强制下线用户", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_sessions(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
):
    """DELETE /users/{id}/sessions — 销毁该用户全部 Session，强制下线。"""
    await service.revoke_user_sessions(user_id)


# ─────────────────────────────────────────────────────────
# App 管理
# ─────────────────────────────────────────────────────────
@router.get("/apps", summary="获取所有应用列表")
async def list_apps(service: IdentityServiceDep, current_user: CurrentUserDep):
    apps = await service.list_apps()
    return success(data=[{"id": a.id, "app_code": a.app_code, "app_name": a.app_name,
                          "perm_mode": a.perm_mode, "description": a.description} for a in apps])


@router.post("/apps", status_code=status.HTTP_201_CREATED, summary="注册新应用")
async def create_app(data: AppCreate, service: IdentityServiceDep, current_user: CurrentUserDep):
    app = await service.create_app(data)
    return success(
        data=AppSecretOut(app_code=app.app_code, app_secret=app._plain_secret).model_dump(),
        message="应用创建成功，请将 app_secret 安全保存",
    )


@router.put("/apps/{app_code}", summary="更新应用信息")
async def update_app(
    data: AppUpdate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: str = Path(...),
):
    app = await service.update_app(app_code, data)
    return success(data={"app_code": app.app_code, "perm_mode": app.perm_mode}, message="更新成功")


@router.delete("/apps/{app_code}", summary="删除应用", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: str = Path(...),
):
    await service.delete_app(app_code)


@router.post("/apps/{app_code}/secret", summary="重置应用密码")
async def reset_app_secret(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: str = Path(...),
):
    """[管理员] 重置 app_secret。新密鑰仅返回一次，展示后后端不再明文存储。"""
    app, new_secret = await service.reset_app_secret(app_code)
    return success(
        data=AppSecretOut(app_code=app.app_code, app_secret=new_secret).model_dump(),
        message="密码已重置，请将新密码安全保存",
    )


# ─────────────────────────────────────────────────────────
# 角色管理
# ─────────────────────────────────────────────────────────
@router.get("/apps/{app_code}/roles", summary="获取应用的角色列表")
async def list_roles(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: str = Path(...),
):
    roles = await service.list_roles(app_code)
    return success(data=[{"id": r.id, "role_name": r.role_name, "role_code": r.role_code} for r in roles])


@router.post("/apps/{app_code}/roles", status_code=status.HTTP_201_CREATED, summary="新建角色")
async def create_role(
    data: RoleCreate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: str = Path(...),
):
    data.app_code = app_code  # 优先用 URL 中的 app_code
    role = await service.create_role(data)
    return success(data={"id": role.id, "role_code": role.role_code}, message="角色创建成功")


@router.put("/roles/{role_id}", summary="更新角色")
async def update_role(
    data: RoleUpdate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    role_id: int = Path(...),
):
    role = await service.update_role(role_id, data)
    return success(data={"id": role.id, "role_code": role.role_code}, message="更新成功")


@router.delete("/roles/{role_id}", summary="删除角色", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    role_id: int = Path(...),
):
    await service.delete_role(role_id)


@router.get("/roles/{role_id}/permissions", summary="获取角色已绑定的权限节点")
async def get_role_permissions(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    role_id: int = Path(...),
):
    perms = await service.get_role_permissions(role_id)
    return success(data=[{"id": p.id, "code": p.code, "name": p.name, "type": p.type} for p in perms])


@router.put("/roles/{role_id}/permissions", summary="批量设置角色权限（全量替换）")
async def assign_role_permissions(
    data: RolePermissionsAssign,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    role_id: int = Path(...),
):
    await service.assign_role_permissions(role_id, data)
    return success(message="权限绑定已更新")


# ─────────────────────────────────────────────────────────
# 用户-角色分配
# ─────────────────────────────────────────────────────────
@router.get("/users/{user_id}/roles", summary="获取用户的角色列表")
async def list_user_roles(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
    app_code: str | None = Query(None, description="小系统过滤，不传则返回所有系统的角色"),
):
    roles = await service.list_user_roles(user_id, app_code)
    return success(data=[{"id": r.id, "app_code": r.app_code, "role_name": r.role_name, "role_code": r.role_code} for r in roles])


@router.post("/users/{user_id}/roles", status_code=status.HTTP_201_CREATED, summary="给用户分配角色")
async def assign_user_role(
    data: UserRoleAssign,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
):
    await service.assign_role_to_user(user_id, data.role_id)
    return success(message="角色分配成功")


@router.delete("/users/{user_id}/roles/{role_id}", summary="撤销用户的角色", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_role(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
    role_id: int = Path(...),
):
    await service.revoke_role_from_user(user_id, role_id)


# ─────────────────────────────────────────────────────────
# 菜单管理 CRUD
# ─────────────────────────────────────────────────────────
@router.get("/apps/{app_code}/menus", summary="获取菜单列表（扁平）")
async def list_menus(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: str = Path(...),
):
    """[管理员] 返回指定 App 的扁平化菜单列表，供管理后台树形展示。"""
    items = await service.get_menu_list_flat(app_code=app_code)
    return success(data=items)


@router.get("/apps/{app_code}/menus/tree", summary="获取菜单树（嵌套）")
async def get_menu_tree(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: str = Path(...),
):
    """[管理员] 返回指定 App 的全量嵌套菜单树，含未激活节点。"""
    tree = await service.get_menu_tree_for_admin(app_code=app_code)
    return success(data=tree)


@router.post("/apps/{app_code}/menus", status_code=status.HTTP_201_CREATED, summary="新增菜单/按鈕")
async def create_menu(
    data: MenuCreate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    app_code: str = Path(...),
):
    data = data.model_copy(update={"app_code": app_code})
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


@router.delete("/menus/{menu_id}", summary="删除菜单", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    menu_id: int = Path(...),
):
    await service.delete_menu(menu_id)


# ─────────────────────────────────────────────────────────
# 部门管理
# ─────────────────────────────────────────────────────────
@router.get("/departments", summary="获取部门列表")
async def list_departments(service: IdentityServiceDep, current_user: CurrentUserDep):
    """[管理员] 返回所有部门列表，前端根据 parent_id 组装树形。"""
    depts = await service.list_departments()
    return success(data=[
        {"id": d.id, "dept_name": d.dept_name, "parent_id": d.parent_id,
         "sort": d.sort, "leader": d.leader, "phone": d.phone,
         "email": d.email, "is_active": d.is_active}
        for d in depts
    ])


@router.post("/departments", status_code=status.HTTP_201_CREATED, summary="新建部门")
async def create_department(
    data: DepartmentCreate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
):
    dept = await service.create_department(data)
    return success(data={"id": dept.id, "dept_name": dept.dept_name}, message="部门创建成功")


@router.put("/departments/{dept_id}", summary="更新部门")
async def update_department(
    data: DepartmentUpdate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    dept_id: int = Path(...),
):
    dept = await service.update_department(dept_id, data)
    return success(data={"id": dept.id, "dept_name": dept.dept_name}, message="更新成功")


@router.delete("/departments/{dept_id}", summary="删除部门", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    dept_id: int = Path(...),
):
    await service.delete_department(dept_id)


# ─────────────────────────────────────────────────────────
# 用户-应用访问授权管理
# ─────────────────────────────────────────────────────────
@router.get("/users/{user_id}/apps", summary="获取用户已授权的应用列表")
async def list_user_app_grants(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
):
    grants = await service.list_user_app_grants(user_id)
    return success(data=[
        {
            "user_id": g.user_id, "app_code": g.app_code,
            "is_active": g.is_active, "expired_at": g.expired_at,
            "created_at": g.created_at,
        }
        for g in grants
    ])


@router.post("/users/{user_id}/apps", status_code=status.HTTP_201_CREATED, summary="授权用户访问应用")
async def grant_user_app(
    data: UserAppGrant,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
):
    """幂等操作：已存在则更新，不存在则新建。"""
    binding = await service.grant_user_app_access(user_id, data)
    return success(
        data={"user_id": binding.user_id, "app_code": binding.app_code, "is_active": binding.is_active},
        message="授权成功",
    )


@router.put("/users/{user_id}/apps/{app_code}", summary="更新用户应用授权")
async def update_user_app(
    data: UserAppUpdate,
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
    app_code: str = Path(...),
):
    binding = await service.update_user_app_access(user_id, app_code, data)
    return success(
        data={"user_id": binding.user_id, "app_code": binding.app_code, "is_active": binding.is_active},
        message="更新成功",
    )


@router.delete("/users/{user_id}/apps/{app_code}", summary="撤销用户应用授权", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_app(
    service: IdentityServiceDep,
    current_user: CurrentUserDep,
    user_id: int = Path(...),
    app_code: str = Path(...),
):
    await service.revoke_user_app_access(user_id, app_code)


# ─────────────────────────────────────────────────────────
# 服务间内部接口（AppSecretDep 鉴权，不走用户 Token）
# ─────────────────────────────────────────────────────────
@router.get("/internal/users/{user_id}", summary="[内部] 查询用户信息")
async def internal_get_user(
    app: AppSecretDep,
    service: IdentityServiceDep,
    user_id: int = Path(...),
):
    """供子系统调用：通过 app_code + 签名验证代替用户 Token。"""
    user = await service.get_user_by_id(user_id)
    return success(data=user.model_dump())


@router.get("/internal/users/{user_id}/roles", summary="[内部] 查询用户在指定应用的角色")
async def internal_get_user_roles(
    app: AppSecretDep,
    service: IdentityServiceDep,
    user_id: int = Path(...),
    filter_app_code: str | None = Query(None, alias="app_code", description="过滤指定应用的角色，不传则返回所有"),
):
    """供子系统鉴权层使用：获取用户在自身系统的角色列表。"""
    roles = await service.list_user_roles(user_id, filter_app_code)
    return success(data=[
        {"id": r.id, "app_code": r.app_code, "role_name": r.role_name, "role_code": r.role_code}
        for r in roles
    ])


@router.post(
    "/internal/apps/{app_code}/permissions/sync",
    summary="[内部] 子系统权限全量同步",
)
async def sync_permissions(
    app: AppSecretDep,
    service: IdentityServiceDep,
    data: PermissionSyncRequest,
    app_code: str = Path(...),
):
    """子系统调用：上报全量权限清单，中控平台完成三阶段对齐（新增/更新/软下线）。

    鉴权：AppSecretDep（HMAC-SHA256 签名），不走用户 Token。
    """
    # 校验 app_code 与签名中的应用一致
    if app.app_code != app_code:
        from domains.identity.exceptions import PermissionSyncError
        raise PermissionSyncError(f"路径 app_code '{app_code}' 与签名应用 '{app.app_code}' 不一致")

    result = await service.sync_permissions(app_code=app_code, items=data.items)
    return success(data=result.model_dump(), message="权限同步完成")


@router.post(
    "/internal/apps/{app_code}/roles/sync",
    summary="[内部] 子系统角色全量同步",
)
async def sync_roles(
    app: AppSecretDep,
    service: IdentityServiceDep,
    data: RoleSyncRequest,
    app_code: str = Path(...),
):
    """子系统调用：上报全量角色清单（含权限绑定），中控平台完成三阶段对齐。

    鉴权：AppSecretDep（HMAC-SHA256 签名），不走用户 Token。
    """
    if app.app_code != app_code:
        from domains.identity.exceptions import RoleSyncError
        raise RoleSyncError(f"路径 app_code '{app_code}' 与签名应用 '{app.app_code}' 不一致")

    result = await service.sync_roles(app_code=app_code, items=data.items)
    return success(data=result.model_dump(), message="角色同步完成")


# ─────────────────────────────────────────────────────────
# 内部查询接口（供子系统按需获取应用/部门详情）
# ─────────────────────────────────────────────────────────
@router.get("/internal/apps/{app_code}", summary="[内部] 查询应用信息")
async def internal_get_app(
    app: AppSecretDep,
    service: IdentityServiceDep,
    app_code: str = Path(...),
):
    """供子系统调用：通过 app_code 查询应用详情。

    鉴权：AppSecretDep（HMAC-SHA256 签名），不走用户 Token。
    """
    result = await service.get_app(app_code)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="应用不存在")
    return success(data={
        "id": result.id,
        "app_code": result.app_code,
        "app_name": result.app_name,
        "perm_mode": result.perm_mode,
        "description": result.description,
    })


@router.get("/internal/departments/{dept_id}", summary="[内部] 查询部门信息")
async def internal_get_department(
    app: AppSecretDep,
    service: IdentityServiceDep,
    dept_id: int = Path(...),
):
    """供子系统调用：通过 dept_id 查询部门详情。

    鉴权：AppSecretDep（HMAC-SHA256 签名），不走用户 Token。
    """
    dept = await service.get_department(dept_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")
    return success(data={
        "id": dept.id,
        "dept_name": dept.dept_name,
        "parent_id": dept.parent_id,
        "sort": dept.sort,
        "leader": dept.leader,
        "phone": dept.phone,
        "email": dept.email,
        "is_active": dept.is_active,
    })
