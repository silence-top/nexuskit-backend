# domains/identity/exceptions.py — Identity domain exceptions
from nexuskit_sdk.codes import BizCode
from common.exceptions.base import DomainError


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
