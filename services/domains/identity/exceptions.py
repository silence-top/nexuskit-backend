# domains/identity/exceptions.py — Identity domain exceptions
from common.exceptions.base import DomainError


class MenuDomainError(DomainError):
    status_code = 400


class MenuNotFoundError(MenuDomainError):
    status_code = 404


class MenuHasChildrenError(MenuDomainError):
    status_code = 400
