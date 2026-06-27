# domains/identity/exceptions.py — Identity domain exceptions
from nexuskit_sdk.codes import BizCode
from common.exceptions.base import DomainError


# ── Menu ────────────────────────────────────────────

class MenuDomainError(DomainError):
    status_code = 400
    biz_code = BizCode.BAD_REQUEST


class MenuNotFoundError(MenuDomainError):
    status_code = 404
    biz_code = BizCode.NOT_FOUND


class MenuHasChildrenError(MenuDomainError):
    """Cannot delete menu that still has children — relation constraint."""
    status_code = 400
    biz_code = BizCode.RELATION_EXISTS


# ── App ────────────────────────────────────────────

class AppDomainError(DomainError):
    status_code = 400
    biz_code = BizCode.BAD_REQUEST


class AppNotFoundError(AppDomainError):
    status_code = 404
    biz_code = BizCode.NOT_FOUND


class AppAlreadyExistsError(AppDomainError):
    status_code = 409
    biz_code = BizCode.CONFLICT


class AppAccessForbiddenError(AppDomainError):
    """User has no active access grant to this app."""
    status_code = 403
    biz_code = BizCode.APP_FORBIDDEN


# ── Role ───────────────────────────────────────────

class RoleDomainError(DomainError):
    status_code = 400
    biz_code = BizCode.BAD_REQUEST


class RoleNotFoundError(RoleDomainError):
    status_code = 404
    biz_code = BizCode.NOT_FOUND


class RoleAlreadyExistsError(RoleDomainError):
    status_code = 409
    biz_code = BizCode.ROLE_EXISTS


class RoleHasUsersError(RoleDomainError):
    """Cannot delete role that still has users assigned."""
    status_code = 400
    biz_code = BizCode.RELATION_EXISTS


# ── Sync ──────────────────────────────────────────

class PermissionSyncError(DomainError):
    """权限同步失败。"""
    status_code = 422
    biz_code = BizCode.UNPROCESSABLE


class RoleSyncError(DomainError):
    """角色同步失败。"""
    status_code = 422
    biz_code = BizCode.UNPROCESSABLE


class RoleBindingForbiddenError(DomainError):
    """不允许手动绑定子系统上报角色的权限。"""
    status_code = 403
    biz_code = BizCode.FORBIDDEN


# ── Department ──────────────────────────────────────────

class DeptDomainError(DomainError):
    status_code = 400
    biz_code = BizCode.BAD_REQUEST


class DeptNotFoundError(DeptDomainError):
    status_code = 404
    biz_code = BizCode.NOT_FOUND


class DeptHasChildrenError(DeptDomainError):
    """Cannot delete department that still has sub-departments."""
    status_code = 400
    biz_code = BizCode.RELATION_EXISTS
